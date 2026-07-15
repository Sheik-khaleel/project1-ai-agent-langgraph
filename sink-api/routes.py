from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request

from schemas import RecordsPayload, RecordsResponse
from services import RecordsService

router = APIRouter()
logger = logging.getLogger("sink_api.routes")


@router.get("/health")
def health(request: Request) -> dict[str, str]:
    """Simple health endpoint for the sink service."""
    client_host = request.client.host if request.client else None
    logger.info("Health check requested", extra={"client": client_host})
    return {"status": "ok"}


@router.get("/records", response_model=RecordsResponse)
def list_records(request: Request) -> RecordsResponse:
    """Return all stored records."""
    client_host = request.client.host if request.client else None
    logger.info("List records requested", extra={"client": client_host})
    return RecordsService.list_records()


@router.post("/records", response_model=RecordsResponse, status_code=201)
def ingest_records(request: Request, payload: RecordsPayload) -> RecordsResponse:
    """Store records sent by the orchestrator."""
    client_host = request.client.host if request.client else None
    logger.info("Ingest records requested", extra={"client": client_host})
    try:
        return RecordsService.ingest_records(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
