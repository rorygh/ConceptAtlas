from typing import Literal

from pydantic import BaseModel, Field


class Filters(BaseModel):
    level: str | None = Field(
        None,
        description="'U' for undergraduate only, 'G' for graduate only, null for no restriction",
    )
    depts: list[str] = Field(
        default_factory=list,
        description="MIT dept numbers to restrict to, e.g. ['6', '18']. Empty = any dept.",
    )
    max_units: int | None = Field(
        None,
        description="Hard upper limit on course units. null = no limit.",
    )
    exclude_keywords: list[str] = Field(
        default_factory=list,
        description="Words/phrases that must NOT appear in the course title or description.",
    )
    instructors: list[str] = Field(
        default_factory=list,
        description="Instructor name substrings to match, e.g. ['Williams']. Empty = any instructor.",
    )
    min_rating: float | None = Field(
        None,
        description="Minimum course rating (scale ~0-7). null = no minimum.",
    )
    has_prereqs: bool | None = Field(
        None,
        description="True = only courses WITH prerequisites, False = only courses with NO prerequisites, null = no restriction.",
    )
    requires_courses: list[str] = Field(
        default_factory=list,
        description="Course IDs that must appear in the course's own prerequisite list, e.g. ['18.06', '6.042J'].",
    )


class LearningIntent(BaseModel):
    action: Literal["search", "filter"] = Field(
        description=(
            "'search' = semantic vector search then filter (use when user wants to discover courses by topic). "
            "'filter' = apply filters to all courses with no semantic search "
            "(use when user specifies concrete constraints with no open-ended topic, "
            "e.g. 'show me courses by Williams', 'list grad EECS courses under 9 units')."
        ),
    )
    topics: list[str] = Field(
        default_factory=list,
        description="Academic concepts to embed and search for. Required when action='search', empty when action='filter'.",
    )
    filters: Filters = Field(
        default_factory=Filters,
        description="Hard constraints extracted from the query.",
    )
    explanation: str = Field(
        description="One sentence describing what the user wants, for display.",
    )
