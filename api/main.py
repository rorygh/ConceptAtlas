import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

STATIC      = Path(__file__).parent / "static"
COURSES_PATH = Path(__file__).parent.parent / "data" / "courses.json"

_courses_cache = None


def _all_courses():
    global _courses_cache
    if _courses_cache is None:
        _courses_cache = json.loads(COURSES_PATH.read_text())
    return _courses_cache


def _flatten_prereqs(node) -> list:
    if node is None:
        return []
    if isinstance(node, str):
        if not node or node.startswith("''") or node.upper().startswith("GIR:"):
            return []
        return [node]
    return [id_ for item in node.get("items", []) for id_ in _flatten_prereqs(item)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    from retrieval.search import _load
    _load()
    yield


app = FastAPI(lifespan=lifespan)


class SearchRequest(BaseModel):
    query: str
    n: int = 10


@app.post("/api/search")
def search(req: SearchRequest):
    from retrieval.search import search as _search
    results = _search(req.query, n=req.n)
    return {
        "courses": [
            {"id": c["id"], "title": c["title"], "description": c["description"],
             "units": c["units"], "level": c.get("level")}
            for c in results
        ]
    }


@app.get("/api/courses")
def courses():
    return [
        {
            "id":    c["id"],
            "title": c["title"],
            "units": c["units"],
            "level": c.get("level"),
            "dept":  c["id"].split(".")[0],
        }
        for c in _all_courses()
    ]


@app.get("/api/graph")
def graph():
    all_ids = {c["id"] for c in _all_courses()}
    edges = []
    for c in _all_courses():
        for prereq in _flatten_prereqs(c.get("prerequisites")):
            if prereq in all_ids:
                edges.append({"source": prereq, "target": c["id"]})
    return {"edges": edges}


@app.get("/api/course/{course_id:path}")
def course(course_id: str):
    for c in _all_courses():
        if c["id"] == course_id:
            return {
                "id":               c["id"],
                "title":            c["title"],
                "description":      c["description"],
                "units":            c["units"],
                "level":            c.get("level"),
                "prereqs_flat":     _flatten_prereqs(c.get("prerequisites")),
                "related_subjects": c.get("related_subjects", []),
                "instructors":      c.get("instructors", []),
                "url":              c.get("url"),
            }
    raise HTTPException(status_code=404, detail="Course not found")


@app.get("/api/similar/{course_id:path}")
def similar_courses(course_id: str):
    from retrieval.search import _load
    _, collection, courses_by_id = _load()
    if course_id not in courses_by_id:
        raise HTTPException(status_code=404, detail="Not found")
    stored = collection.get(ids=[course_id], include=["embeddings"])
    if stored["embeddings"] is None or len(stored["embeddings"]) == 0:
        raise HTTPException(status_code=404, detail="No embedding found")
    results = collection.query(query_embeddings=[stored["embeddings"][0]], n_results=21)
    return {
        "similar": [
            {"id": rid, "score": round(1 - i / 20, 3)}
            for i, rid in enumerate(results["ids"][0])
            if rid != course_id
        ][:20]
    }


@app.get("/favicon.svg")
def favicon():
    return FileResponse(STATIC / "favicon.svg", media_type="image/svg+xml")

@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")
