from datetime import date

from pydantic import BaseModel


class JournalEntry(BaseModel):
    schema_version: int = 1
    date: date
    topic: str
    learned: str
    stuck: str | None = None
    related_concepts: list[str] = []
