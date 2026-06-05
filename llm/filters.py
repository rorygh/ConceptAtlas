"""Apply hard filters from a LearningIntent to a list of course dicts."""
from .schema import Filters


def _flatten_prereqs(node) -> set[str]:
    """Recursively collect all course IDs from a prerequisites tree."""
    if node is None:
        return set()
    if isinstance(node, str):
        return {node} if node and not node.startswith("GIR:") else set()
    return {id_ for item in node.get("items", []) for id_ in _flatten_prereqs(item)}


def apply_filters(courses: list[dict], filters: Filters) -> list[dict]:
    """Return only courses that satisfy all hard constraints in `filters`."""
    result = courses

    if filters.level:
        result = [c for c in result if c.get("level") == filters.level]

    if filters.depts:
        dept_set = set(filters.depts)
        result = [c for c in result if c["id"].split(".")[0] in dept_set]

    if filters.max_units is not None:
        result = [c for c in result if (c.get("units") or 0) <= filters.max_units]

    if filters.exclude_keywords:
        lower_kws = [kw.lower() for kw in filters.exclude_keywords]

        def _no_excluded(c: dict) -> bool:
            text = (c.get("title", "") + " " + c.get("description", "")).lower()
            return not any(kw in text for kw in lower_kws)

        result = [c for c in result if _no_excluded(c)]

    if filters.instructors:
        lower_names = [n.lower() for n in filters.instructors]

        def _instructor_match(c: dict) -> bool:
            course_instructors = " ".join(c.get("instructors") or []).lower()
            return any(n in course_instructors for n in lower_names)

        result = [c for c in result if _instructor_match(c)]

    if filters.min_rating is not None:
        result = [c for c in result if (c.get("rating") or 0) >= filters.min_rating]

    if filters.has_prereqs is True:
        result = [c for c in result if _flatten_prereqs(c.get("prerequisites"))]
    elif filters.has_prereqs is False:
        result = [c for c in result if not _flatten_prereqs(c.get("prerequisites"))]

    if filters.requires_courses:
        required_set = set(filters.requires_courses)

        def _has_required_prereqs(c: dict) -> bool:
            prereqs = _flatten_prereqs(c.get("prerequisites"))
            return required_set.issubset(prereqs)

        result = [c for c in result if _has_required_prereqs(c)]

    return result
