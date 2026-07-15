from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from typing import Final

from orchestrator import prompts
from orchestrator.adapters import MissingOpenAIKeyError, OpenAIError, get_openai_client
from orchestrator.models import OrchestratorState

_SUPPORTED_KEYWORDS: Final[tuple[str, ...]] = ("ingest", "import", "sync")
_REQUIRED_TOPIC: Final[str] = "todo"
_DEFAULT_LIMIT: Final[int] = 5
_MAX_LIMIT: Final[int] = 10


logger = logging.getLogger("orchestrator.intent")


@dataclass(slots=True)
class IntentResult:
    supported: bool
    limit: int | None = None


def prepare_state(message: str) -> OrchestratorState:
    """Interpret the user message and build the initial orchestrator state."""
    normalized = message.strip()
    if not normalized:
        raise ValueError("Message is empty")

    normalized_lower = normalized.lower()
    logger.info("Preparing orchestrator state", extra={"normalized": normalized_lower})

    try:
        classification = _classify_with_llm(message)
    except OpenAIError as exc:
        logger.warning(
            "LLM classification failed, falling back to heuristics: %s",
            getattr(exc, "message", str(exc)),
        )
        classification = None
    except Exception as exc:  # noqa: BLE001 - fall back to heuristics if LLM call fails
        logger.warning(
            "LLM classification failed, falling back to heuristics: %s",
            str(exc),
        )
        classification = None

    if classification is None:
        classification = _heuristic_classification(normalized_lower)
        logger.info(
            "Applied heuristic classification",
            extra={
                "supported": classification.supported,
                "limit": classification.limit,
            },
        )
    else:
        logger.info(
            "LLM classification result",
            extra={
                "supported": classification.supported,
                "limit": classification.limit,
            },
        )

    if not classification.supported:
        logger.warning("Unsupported request detected")
        raise ValueError("Message does not contain a supported ingest request")

    limit = _normalize_limit(classification.limit, normalized_lower)
    logger.info("Final limit determined", extra={"limit": limit})

    return OrchestratorState(
        message=message,
        fetch_url=os.getenv("FETCH_URL"),
        sink_url=os.getenv("SINK_URL"),
        limit=limit,
        status="pending",
    )


def _classify_with_llm(message: str) -> IntentResult | None:
    api_key = os.getenv("OPENAI_API_KEY")
    try:
        client = get_openai_client(api_key)
    except MissingOpenAIKeyError:
        logger.debug("Skipping LLM classification due to missing or placeholder API key")
        return None

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    prompt = prompts.INTENT_CLASSIFIER_PROMPT.format(message=message)

    logger.info("Calling LLM classifier", extra={"model": model})
    logger.debug("LLM prompt", extra={"prompt": prompt})
    try:
        response = client.responses.create(
            model=model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt,
                        }
                    ],
                }
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
    except TypeError as exc:
        if "response_format" not in str(exc):
            raise
        logger.debug(
            "Retrying LLM classification without response_format due to client compatibility",
            extra={"error": str(exc)},
        )
        response = client.responses.create(
            model=model,
            input=prompt,
            temperature=0,
        )
        response = client.responses.create(
            model=model,
            input=prompt,
            temperature=0,
        )
    content = _extract_text(response)
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        logger.debug(
            "LLM response was not valid JSON",
            extra={"error": str(exc), "content": content},
        )
        return None
    supported = bool(data.get("supported", False))
    limit = data.get("limit")
    if isinstance(limit, str) and limit.isdigit():
        limit = int(limit)
    if not isinstance(limit, int):
        limit = None

    return IntentResult(supported=supported, limit=limit)


def _extract_text(response: object) -> str:
    try:
        # New Responses API shape
        output = getattr(response, "output", None)
        if output:
            content = output[0].content[0].text  # type: ignore[index]
            return str(content)
        # Fallback to choices-based structure
        choices = getattr(response, "choices", None)
        if choices:
            return str(choices[0].message["content"])  # type: ignore[index]
    except Exception as exc:  # pragma: no cover - defensive branch
        raise ValueError("Unable to parse LLM response") from exc

    raise ValueError("Empty response from LLM")


def _heuristic_classification(message: str) -> IntentResult:
    supported = _is_ingest_request(message)
    limit = _extract_limit(message) if supported else None
    logger.debug(
        "Heuristic classification applied",
        extra={"supported": supported, "limit": limit},
    )
    return IntentResult(supported=supported, limit=limit)


def _normalize_limit(candidate: int | None, message: str) -> int:
    if isinstance(candidate, int) and 1 <= candidate <= _MAX_LIMIT:
        return candidate
    logger.debug("Normalizing limit from message", extra={"candidate": candidate})
    return _extract_limit(message)


def _is_ingest_request(message: str) -> bool:
    has_keyword = any(keyword in message for keyword in _SUPPORTED_KEYWORDS)
    has_topic = _REQUIRED_TOPIC in message or f"{_REQUIRED_TOPIC}s" in message
    return has_keyword and has_topic


def _extract_limit(message: str) -> int:
    match = re.search(r"\b(\d{1,2})\b", message)
    if not match:
        return _DEFAULT_LIMIT

    value = int(match.group(1))
    if not 1 <= value <= _MAX_LIMIT:
        return _DEFAULT_LIMIT

    return value
