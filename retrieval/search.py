import json
from functools import lru_cache
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_PATH = Path(__file__).parent.parent / "data" / "chroma"
COURSES_PATH = Path(__file__).parent.parent / "data" / "courses.json"


@lru_cache(maxsize=1)
def _load():
    model = SentenceTransformer("all-MiniLM-L6-v2")
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    collection = client.get_collection("courses")
    courses_by_id = {c["id"]: c for c in json.loads(COURSES_PATH.read_text())}
    return model, collection, courses_by_id


def search(query: str, n: int = 5) -> list[dict]:
    model, collection, courses_by_id = _load()

    vec = model.encode([query]).tolist()
    results = collection.query(query_embeddings=vec, n_results=n * 3)

    # Deduplicate cross-listed courses by normalising the title.
    seen_titles: set[str] = set()
    courses = []
    for course_id in results["ids"][0]:
        course = courses_by_id.get(course_id)
        if not course:
            continue
        key = course["title"].lower().strip()
        if key in seen_titles:
            continue
        seen_titles.add(key)
        courses.append(course)
        if len(courses) == n:
            break

    return courses
