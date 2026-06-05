import json
from functools import lru_cache
from pathlib import Path

import chromadb
import numpy as np
from sentence_transformers import SentenceTransformer

CHROMA_PATH = Path(__file__).parent.parent / "data" / "chroma"
COURSES_PATH = Path(__file__).parent.parent / "data" / "courses.json"
SIM_PATH     = Path(__file__).parent.parent / "data" / "similarity.npy"


@lru_cache(maxsize=1)
def _load():
    model = SentenceTransformer("all-MiniLM-L6-v2")
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    collection = client.get_collection("courses")
    courses_by_id = {c["id"]: c for c in json.loads(COURSES_PATH.read_text())}
    return model, collection, courses_by_id


@lru_cache(maxsize=1)
def _load_embeddings() -> tuple[list[str], np.ndarray, dict[str, int]]:
    """Load and cache the full embedding matrix.

    Returns (ids, matrix, id_to_index). Unit vectors from all-MiniLM, so
    matrix @ query_vec gives cosine similarity for every course in one shot.
    """
    _, collection, _ = _load()
    data = collection.get(include=["embeddings"])
    ids: list[str] = data["ids"]
    E = np.array(data["embeddings"], dtype=np.float32)
    id_to_idx = {rid: i for i, rid in enumerate(ids)}
    return ids, E, id_to_idx


@lru_cache(maxsize=1)
def _load_similarity_matrix() -> np.ndarray:
    """Load the all-pairs cosine similarity matrix (float16, ~100 MB).

    Normally written by ingest/embed_courses.py to data/similarity.npy.
    Falls back to computing on demand if the file doesn't exist.
    """
    if SIM_PATH.exists():
        return np.load(SIM_PATH)
    _, E, _ = _load_embeddings()
    return (E @ E.T).astype(np.float16)


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
