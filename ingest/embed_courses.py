import json
from pathlib import Path

import chromadb
import numpy as np
from sentence_transformers import SentenceTransformer

COURSES_PATH = Path(__file__).parent.parent / "data" / "courses.json"
CHROMA_PATH  = Path(__file__).parent.parent / "data" / "chroma"
SIM_PATH     = Path(__file__).parent.parent / "data" / "similarity.npy"


def embed():
    courses = json.loads(COURSES_PATH.read_text())
    print(f"Loaded {len(courses)} courses")

    print("Loading embedding model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # Build the strings we want to embed — title + description gives the model
    # enough context to understand what each course is actually about.
    texts = [f"{c['title']}. {c['description']}" for c in courses]
    ids = [c["id"] for c in courses]
    metadatas = [{"title": c["title"], "units": c["units"]} for c in courses]

    print("Embedding courses (this takes ~60s on CPU)...")
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=64)

    print("Storing in ChromaDB...")
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))

    # Delete and recreate so re-running this script stays idempotent.
    try:
        client.delete_collection("courses")
    except Exception:
        pass
    collection = client.create_collection("courses")

    # ChromaDB has a max batch size (~5461), so we add in chunks.
    emb_list = embeddings.tolist()
    chunk = 5000
    for i in range(0, len(ids), chunk):
        collection.add(
            ids=ids[i:i+chunk],
            embeddings=emb_list[i:i+chunk],
            documents=texts[i:i+chunk],
            metadatas=metadatas[i:i+chunk],
        )

    print(f"Done. {collection.count()} courses indexed → {CHROMA_PATH}")

    # All-pairs cosine similarity matrix — computed once here so startup is instant.
    # Normalize explicitly; shape: (n_courses, n_courses), dtype float16 (~100 MB).
    print("Computing all-pairs similarity matrix...")
    E = embeddings.astype(np.float32)
    norms = np.linalg.norm(E, axis=1, keepdims=True)
    E_norm = E / np.where(norms > 0, norms, 1.0)
    np.save(SIM_PATH, (E_norm @ E_norm.T).astype(np.float16))
    print(f"Saved similarity matrix {E_norm.shape[0]}×{E_norm.shape[0]} → {SIM_PATH}")


if __name__ == "__main__":
    embed()
