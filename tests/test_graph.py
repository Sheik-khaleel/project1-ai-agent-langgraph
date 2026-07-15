from __future__ import annotations

from typing import Any

import pytest

from orchestrator import tools
from orchestrator.graph import graph
from orchestrator.models import OrchestratorState


def test_graph_run_success(monkeypatch: pytest.MonkeyPatch) -> None:
    sample_payload = [
        {"id": idx, "title": f"Todo {idx}", "completed": idx % 2 == 0}
        for idx in range(1, 6)
    ]

    def fake_fetch(url: str) -> list[dict[str, Any]]:  # noqa: ARG001 - signature compatibility
        return sample_payload

    def fake_post(url: str, payload: dict[str, Any]) -> dict[str, Any]:  # noqa: ARG001
        assert payload["records"]
        return {"stored": len(payload["records"])}

    monkeypatch.setattr(tools, "fetch_from_source", fake_fetch)
    monkeypatch.setattr(tools, "post_to_sink", fake_post)

    initial_state = OrchestratorState(
        message="ingest todos",
        fetch_url="https://example.com/todos",
        sink_url="http://sink/records",
        limit=3,
        status="pending",
    )

    result = graph.run(initial_state)

    assert result.status == "completed"
    assert len(result.transformed_records) == 3
    assert result.sink_result == {"stored": 3}
    assert result.transformed_records[0]["status"] in {"done", "inbox"}


def test_graph_propagates_fetch_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def failing_fetch(url: str) -> list[dict[str, Any]]:  # noqa: ARG001
        raise RuntimeError("boom")

    monkeypatch.setattr(tools, "fetch_from_source", failing_fetch)

    initial_state = OrchestratorState(
        message="ingest todos",
        fetch_url="https://example.com/todos",
        sink_url="http://sink/records",
        status="pending",
    )

    result = graph.run(initial_state)

    assert result.status == "error"
    assert any("FetchAgent" in message for message in result.errors)
