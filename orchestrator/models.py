from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class OrchestratorState(BaseModel):
    """Shared state that flows through the LangGraph orchestration."""

    message: str
    fetch_url: str | None = None
    sink_url: str | None = None
    limit: int = Field(default=5, ge=1, le=20)
    fetched_data: list[dict[str, Any]] = Field(default_factory=list)
    transformed_records: list[dict[str, Any]] = Field(default_factory=list)
    sink_result: dict[str, Any] | None = None
    status: str = "initialized"
    errors: list[str] = Field(default_factory=list)


class QueryRequest(BaseModel):
    """Incoming payload for the orchestrator query endpoint."""

    message: str


class QueryResponse(BaseModel):
    """Response schema returned by the orchestrator."""

    status: str
    records: list[dict[str, Any]]
    sink_result: dict[str, Any] | None = None
    errors: list[str] = Field(default_factory=list)
    limit: int | None = None
