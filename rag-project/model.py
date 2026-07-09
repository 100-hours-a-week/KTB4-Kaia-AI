from datetime import date

from pydantic import BaseModel


class TilEntry(BaseModel):
    """TIL 저장 스키마."""
    schema_version: int = 1
    date: date
    topic: str
    learned: str
    stuck: str | None = None
    related_concepts: list[str] = []


class WilEntry(BaseModel):
    """WIL(Week I Learned) 저장 스키마."""
    schema_version: int = 1
    start: date
    end: date
    source_files: list[str] = []


class RetrospectiveEntry(BaseModel):
    """회고 저장 스키마."""
    schema_version: int = 1
    date: date
    topic: str
    difficulties: str
    reflections: str
    decisions: str | None = None
    problem_solving: str | None = None
    future_plans: str | None = None
