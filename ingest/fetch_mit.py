import json
import requests
from pathlib import Path

CATALOG_URL = "https://fireroad.mit.edu/courses/all?full=true"
OUTPUT_PATH = Path(__file__).parent.parent / "data" / "courses_raw.json"

FIELDS = {
    "subject_id", "title", "description", "prerequisites", "total_units", "level",
    "related_subjects", "rating", "url", "instructors", "schedule",
}


def fetch():
    print("Fetching MIT catalog...")
    response = requests.get(CATALOG_URL, timeout=30)
    response.raise_for_status()

    courses = [
        {k: v for k, v in course.items() if k in FIELDS}
        for course in response.json()
        if course.get("description")
    ]

    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(courses, indent=2))
    print(f"Saved {len(courses)} courses to {OUTPUT_PATH}")


if __name__ == "__main__":
    fetch()
