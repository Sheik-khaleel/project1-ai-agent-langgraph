from __future__ import annotations

from typing import Final

import pytest

from orchestrator import intent
from orchestrator.intent import IntentResult, prepare_state

_DEFAULT_FETCH_URL: Final[str] = "https://jsonplaceholder.typicode.com/todos"
_DEFAULT_SINK_URL: Final[str] = "http://sink-api:8000/records"


def _disable_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(intent, "_classify_with_llm", lambda _message: None)


def test_prepare_state_recognizes_ingest(monkeypatch: pytest.MonkeyPatch) -> None:
    _disable_llm(monkeypatch)
    monkeypatch.setenv("FETCH_URL", _DEFAULT_FETCH_URL)
    monkeypatch.setenv("SINK_URL", _DEFAULT_SINK_URL)

    message = "please ingest todos"
    state = prepare_state(message)

    assert state.message == message
    assert state.fetch_url == _DEFAULT_FETCH_URL
    assert state.sink_url == _DEFAULT_SINK_URL
    assert state.status == "pending"
    assert state.limit == 5


def test_prepare_state_falls_back_when_llm_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    def broken_llm(message: str) -> IntentResult:  # noqa: ARG001
        raise RuntimeError("llm down")

    monkeypatch.setattr(intent, "_classify_with_llm", broken_llm)
    monkeypatch.delenv("FETCH_URL", raising=False)
    monkeypatch.delenv("SINK_URL", raising=False)

    state = prepare_state("ingest todos")
    assert state.limit == 5


def test_prepare_state_respects_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    _disable_llm(monkeypatch)
    monkeypatch.delenv("FETCH_URL", raising=False)
    monkeypatch.delenv("SINK_URL", raising=False)

    state = prepare_state("sync todos 3")
    assert state.limit == 3


def test_prepare_state_out_of_range_limit_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _disable_llm(monkeypatch)
    monkeypatch.delenv("FETCH_URL", raising=False)
    monkeypatch.delenv("SINK_URL", raising=False)

    state = prepare_state("ingest todos 42")
    assert state.limit == 5


def test_prepare_state_uses_llm_result(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_llm(message: str) -> IntentResult:  # noqa: ARG001
        return IntentResult(supported=True, limit=7)

    monkeypatch.setattr(intent, "_classify_with_llm", fake_llm)
    state = prepare_state("handle these for me")
    assert state.limit == 7


@pytest.mark.parametrize(
    "message",
    ["", "tell me a joke", "sync invoices", "ingest data"],
)
def test_prepare_state_rejects_unsupported_requests(
    message: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    _disable_llm(monkeypatch)
    monkeypatch.delenv("FETCH_URL", raising=False)
    monkeypatch.delenv("SINK_URL", raising=False)

    with pytest.raises(ValueError):
        prepare_state(message)


def test_prepare_state_rejects_when_llm_says_no(monkeypatch: pytest.MonkeyPatch) -> None:
    def negative_llm(message: str) -> IntentResult:  # noqa: ARG001
        return IntentResult(supported=False, limit=None)

    monkeypatch.setattr(intent, "_classify_with_llm", negative_llm)

    with pytest.raises(ValueError):
        prepare_state("please ingest todos")
