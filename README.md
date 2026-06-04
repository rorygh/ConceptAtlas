# ConceptNavigator

AI-powered learning discovery engine. Given a topic you want to learn, it retrieves relevant university courses, expands prerequisite relationships, and generates a personalized learning roadmap.

Initial data source: MIT course catalog via the [FireRoad API](https://fireroad.mit.edu/reference/catalog).

## How it works

1. **Input** — free-form learning goal ("I want to learn robotics")
2. **Topic extraction** — LLM extracts relevant concepts from the query
3. **Semantic search** — query is embedded and matched against course embeddings
4. **Prerequisite expansion** — a directed graph walks dependencies for each matched course
5. **Roadmap generation** — LLM constructs an ordered learning path with explanations

## Example

```
Input:  I want to learn about self-driving cars.

Recommended Courses
  1. Introduction to Robotics
  2. Computer Vision
  3. Feedback Control Systems

Suggested Learning Path
  Linear Algebra
  → Programming Fundamentals
  → Control Systems
  → Computer Vision
  → Robotics
  → Advanced Autonomy
```

## Stack

| Layer      | Tool                                  |
|------------|---------------------------------------|
| Embeddings | `sentence-transformers`               |
| Vector DB  | ChromaDB                              |
| Graph      | NetworkX                              |
| LLM        | Claude (Anthropic)                    |
| API        | FastAPI                               |
| Data       | MIT via FireRoad API                  |

## Project structure

```
ConceptNavigator/
├── ingest/          # Fetch + parse MIT catalog, generate embeddings
│   ├── fetch_mit.py     # Pulls all courses from FireRoad API → data/courses_raw.json
│   └── parse_courses.py # Validates schema, parses prereq trees → data/courses.json
├── retrieval/       # Vector search + graph traversal
├── llm/             # Topic extraction, path generation, explanations
├── api/             # FastAPI app
└── data/
    ├── courses_raw.json  # Raw API response (7,083 courses; 65 dropped for missing description)
    └── courses.json      # Validated, schema-conformant courses with parsed prerequisite trees
```

## RunPod Deployment

The Dockerfile contains all Python dependencies. Code is cloned and data is bootstrapped on first pod start via `setup.sh`.

### Build and push

```bash
docker build --platform linux/amd64 -t rorygh/conceptnavigator:v1.0 .
docker push rorygh/conceptnavigator:v1.0
```

### Pod config

- **Container image**: `rorygh/conceptnavigator:v1.0`
- **Environment variables**:
  - `RUNPOD_GITHUB_TOKEN` — GitHub PAT (repo read scope)
  - `ANTHROPIC_API_KEY` — Anthropic API key

### First-time setup

```bash
/setup.sh
cd /workspace/ConceptNavigator
```

## Data pipeline

The ingest pipeline runs in two steps:

```bash
python -m ingest.fetch_mit      # fetch raw catalog from FireRoad API
python -m ingest.parse_courses  # validate schema + parse prerequisite trees
```

**`fetch_mit.py`** hits `GET /courses/all?full=true` on the FireRoad API and writes a flat JSON array. It filters out courses with no description (65 of 7,148). Fields retained: `subject_id`, `title`, `description`, `prerequisites`, `total_units`, `level`, `related_subjects`, `rating`, `url`, `instructors`, `schedule`.

**`parse_courses.py`** validates each record against a Pydantic `Course` model and parses the prerequisite string into a typed AND/OR tree. The prereq grammar is: commas = AND, slashes = OR, parentheses = grouping. For example:

```
"GIR:CAL1, ((6.100A, 6.100B)/(6.100L, 16.C20))"

→ AND[
    "GIR:CAL1",
    OR[
      AND["6.100A", "6.100B"],
      AND["6.100L", "16.C20"]
    ]
  ]
```

Special tokens (`GIR:XXX`, `''permission of instructor''`) are preserved as leaf strings in the tree.

| Step | Input | Output | Courses |
|------|-------|--------|---------|
| fetch | FireRoad API | `courses_raw.json` | 7,083 |
| parse | `courses_raw.json` | `courses.json` | 7,083 (0 errors) |

## Local development

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in API keys
python -m ingest.fetch_mit
python -m ingest.parse_courses
uvicorn api.main:app --reload
```
