from __future__ import annotations

import importlib.util
import pathlib
from typing import Any

import pytest
from fastapi.testclient import TestClient

from orchestrator import tools
from orchestrator.app import app as orchestrator_app

_BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
_SINK_MAIN = _BASE_DIR / "sink-api" / "main.py"


@pytest.fixture(name="sink_module")
def sink_module_fixture() -> Any:
    spec = importlib.util.spec_from_file_location("sink_api_main", _SINK_MAIN)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load sink API module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(name="clients")
def clients_fixture(sink_module: Any, monkeypatch: pytest.MonkeyPatch) -> tuple[TestClient, TestClient]:
    sink_app = sink_module.app
    sink_database = sink_module.DATABASE
    sink_database.clear()

    sink_client = TestClient(sink_app)
    orchestrator_client = TestClient(orchestrator_app)

    sample_payload = [
        {"id": idx, "title": f"Todo {idx}", "completed": idx % 2 == 0}
        for idx in range(1, 6)
    ]

    def fake_fetch(url: str) -> list[dict[str, Any]]:  # noqa: ARG001
        return sample_payload

    def fake_post(url: str, payload: dict[str, Any]) -> dict[str, Any]:  # noqa: ARG001
        response = sink_client.post("/records", json=payload)
        response.raise_for_status()
        return response.json()

    monkeypatch.setattr(tools, "fetch_from_source", fake_fetch)
    monkeypatch.setattr(tools, "post_to_sink", fake_post)
    monkeypatch.setenv("FETCH_URL", "https://example.com/todos")
    monkeypatch.setenv("SINK_URL", "http://sink/records")

    return orchestrator_client, sink_client


def test_orchestrator_to_sink_end_to_end(clients: tuple[TestClient, TestClient]) -> None:
    orchestrator_client, sink_client = clients

    response = orchestrator_client.post("/query", json={"message": "please ingest todos 3"})
    assert response.status_code == 200
    payload = response.json()

    assert payload["status"] == "completed"
    assert len(payload["records"]) == 3
    assert payload["limit"] == 3
    assert payload["sink_result"]["count"] == 3

    sink_records = sink_client.get("/records").json()
    assert sink_records["count"] == 3
    assert sink_records["records"][0]["title"].startswith("Todo")


def test_orchestrator_handles_sink_failure(
    clients: tuple[TestClient, TestClient], monkeypatch: pytest.MonkeyPatch
) -> None:
    orchestrator_client, sink_client = clients

    def failing_post(url: str, payload: dict[str, Any]) -> dict[str, Any]:  # noqa: ARG001
        response = sink_client.post("/records", json={"records": []})
        response.raise_for_status()
        return response.json()

    monkeypatch.setattr(tools, "post_to_sink", failing_post)

    response = orchestrator_client.post("/query", json={"message": "ingest todos"})
    assert response.status_code == 502
    detail = response.json()["detail"]
    assert any("PostAgent" in entry for entry in detail)


def test_query_endpoint_allows_preflight() -> None:
    client = TestClient(orchestrator_app)
    response = client.options(
        "/query",
        headers={
            "origin": "http://example.com",
            "access-control-request-method": "POST",
        },
    )

    assert response.status_code == 200
    allow_origin = response.headers.get("access-control-allow-origin")
    assert allow_origin in {"*", "http://example.com"}
    allow_methods = response.headers.get("access-control-allow-methods", "")
    assert "POST" in allow_methods
