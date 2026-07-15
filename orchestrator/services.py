from __future__ import annotations

import logging
from dataclasses import dataclass

from orchestrator.graph import graph
from orchestrator.intent import prepare_state
from orchestrator.models import QueryRequest, QueryResponse

logger = logging.getLogger("orchestrator.services")


@dataclass(slots=True)
class OrchestratorServiceError(Exception):
    """Raised when orchestration cannot complete successfully."""

    message: str
    errors: list[str]

    def __post_init__(self) -> None:
        super().__init__(self.message, self.errors)

    def __str__(self) -> str:  # pragma: no cover - dataclass default isn't ideal
        return self.message


class OrchestratorService:
    """Coordinates orchestration requests and response shaping."""

    @staticmethod
    def run_query(payload: QueryRequest) -> QueryResponse:
        logger.info("Received query request", extra={"query_text": payload.message})

        try:
            state = prepare_state(payload.message)
        except ValueError:
            logger.warning("Invalid query payload", exc_info=True)
            raise

        logger.info(
            "State prepared for query",
            extra={
                "limit": state.limit,
                "fetch_url": state.fetch_url,
                "sink_url": state.sink_url,
            },
        )

        logger.info("Starting orchestration run")
        result_state = graph.run(state)
        logger.info(
            "Orchestration finished",
            extra={
                "status": result_state.status,
                "records": len(result_state.transformed_records),
            },
        )

        if result_state.status == "error":
            logger.error(
                "Orchestration completed with errors",
                extra={"errors": result_state.errors},
            )
            raise OrchestratorServiceError(
                "Orchestration completed with errors",
                errors=result_state.errors,
            )

        return QueryResponse(
            status=result_state.status,
            records=result_state.transformed_records,
            sink_result=result_state.sink_result,
            errors=result_state.errors,
            limit=result_state.limit,
        )
