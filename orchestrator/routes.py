from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request

from orchestrator.models import QueryRequest, QueryResponse
from orchestrator.services import OrchestratorService, OrchestratorServiceError

router = APIRouter()
logger = logging.getLogger("orchestrator.routes")


@router.get("/health")
def health(request: Request) -> dict[str, str]:
    """Basic readiness probe for container orchestration."""
    client_host = request.client.host if request.client else None
    logger.info("Health check requested", extra={"client": client_host})
    return {"status": "ok"}


@router.post("/query", response_model=QueryResponse)
def query_orchestrator(request: Request, payload: QueryRequest) -> QueryResponse:
    """Kick off the LangGraph orchestration for a given request."""
    client_host = request.client.host if request.client else None
    logger.info("Query endpoint invoked", extra={"client": client_host})

    try:
        return OrchestratorService.run_query(payload)
    except ValueError as exc:
        logger.warning("Invalid query payload", extra={"client": client_host})
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except OrchestratorServiceError as exc:
        logger.error(
            "Orchestrator service error",
            extra={"client": client_host, "errors": exc.errors},
        )
        raise HTTPException(status_code=502, detail=exc.errors) from exc
