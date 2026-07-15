from __future__ import annotations

import logging
import os
from typing import Any, TypedDict, cast

from langgraph.graph import END, StateGraph

from orchestrator import prompts, tools
from orchestrator.models import OrchestratorState


logger = logging.getLogger("orchestrator.graph")


class GraphState(TypedDict, total=False):
    message: str
    fetch_url: str
    sink_url: str
    limit: int
    fetched_data: list[dict[str, Any]]
    transformed_records: list[dict[str, Any]]
    sink_result: dict[str, Any]
    status: str
    errors: list[str]
    fetch_prompt: str


def _ensure_errors(state: GraphState) -> None:
    if "errors" not in state or state["errors"] is None:
        state["errors"] = []


def _append_error(state: GraphState, message: str) -> GraphState:
    _ensure_errors(state)
    state["errors"].append(message)
    state["status"] = "error"
    logger.error("State transitioned to error", extra={"error_message": message})
    return state


def _fetch_agent(state: GraphState) -> GraphState:
    next_state: GraphState = {**state}
    next_state["status"] = "fetching"
    next_state["fetch_prompt"] = prompts.FETCH_AGENT_PROMPT
    logger.info("FetchAgent started")

    fetch_url = next_state.get("fetch_url") or os.getenv("FETCH_URL")
    if not fetch_url:
        logger.error("FetchAgent missing fetch URL")
        return _append_error(next_state, "FETCH_URL environment variable is not set")

    logger.info("FetchAgent requesting source", extra={"url": fetch_url})
    try:
        fetched_data = tools.fetch_from_source(fetch_url)
    except Exception as exc:  # noqa: BLE001 - propagate context back to caller
        logger.exception("FetchAgent request failed")
        return _append_error(next_state, f"FetchAgent failed: {exc}")

    next_state["fetched_data"] = fetched_data
    next_state["status"] = "fetched"
    logger.info("FetchAgent completed", extra={"items": len(fetched_data)})
    return next_state


def _post_agent(state: GraphState) -> GraphState:
    next_state: GraphState = {**state}
    if next_state.get("status") == "error":
        logger.warning("PostAgent skipped due to prior error")
        return next_state

    fetched_data = next_state.get("fetched_data", [])
    if not fetched_data:
        logger.error("PostAgent missing fetched data")
        return _append_error(next_state, "FetchAgent did not supply data")

    limit = next_state.get("limit") or 5
    logger.info("PostAgent transforming records", extra={"limit": limit})
    transformed_records = [
        {
            "source_id": item.get("id"),
            "title": item.get("title"),
            "status": "done" if item.get("completed") else "inbox",
        }
        for item in fetched_data[:limit]
        if isinstance(item, dict)
    ]

    if not transformed_records:
        logger.error("PostAgent produced no transformed records")
        return _append_error(next_state, "No valid records found in fetched data")

    next_state["transformed_records"] = transformed_records

    sink_url = next_state.get("sink_url") or os.getenv("SINK_URL")
    if not sink_url:
        logger.error("PostAgent missing sink URL")
        return _append_error(next_state, "SINK_URL environment variable is not set")

    payload = {
        "records": transformed_records,
        "prompt": prompts.POST_AGENT_PROMPT,
    }

    logger.info(
        "PostAgent posting to sink",
        extra={"url": sink_url, "records": len(transformed_records)},
    )
    try:
        sink_response = tools.post_to_sink(sink_url, payload)
    except Exception as exc:  # noqa: BLE001 - propagate context back to caller
        logger.exception("PostAgent request failed")
        return _append_error(next_state, f"PostAgent failed: {exc}")

    next_state["sink_result"] = sink_response
    next_state["status"] = "completed"
    logger.info("PostAgent completed", extra={"sink_keys": list(sink_response.keys())})
    return next_state


class OrchestratorGraph:
    """LangGraph wrapper orchestrating FetchAgent and PostAgent."""

    def __init__(self) -> None:
        graph = StateGraph(GraphState)
        graph.add_node("fetch_agent", _fetch_agent)
        graph.add_node("post_agent", _post_agent)
        graph.set_entry_point("fetch_agent")
        graph.add_edge("fetch_agent", "post_agent")
        graph.add_edge("post_agent", END)
        self._graph = graph.compile()

    def run(self, state: OrchestratorState | GraphState) -> OrchestratorState:
        if isinstance(state, OrchestratorState):
            payload: GraphState = cast(GraphState, state.model_dump())
        else:
            payload = cast(GraphState, state)

        logger.info("Graph invocation started", extra={"status": payload.get("status")})
        result = self._graph.invoke(payload)
        logger.info("Graph invocation completed", extra={"status": result.get("status")})
        return OrchestratorState(**result)


graph = OrchestratorGraph()
