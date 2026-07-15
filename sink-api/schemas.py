from __future__ import annotations

from pydantic import BaseModel, Field


class Record(BaseModel):
    source_id: int | None = None
    title: str
    status: str


class RecordsPayload(BaseModel):
    records: list[Record] = Field(default_factory=list)
    prompt: str | None = None


class RecordsResponse(BaseModel):
    count: int
    records: list[Record]
