from __future__ import annotations

import logging
import os

try:  # noqa: SIM105 - compatibility shim for older openai versions
    from openai import OpenAI, OpenAIError
except ImportError:  # pragma: no cover - fallback for legacy clients
    from openai import OpenAI  # type: ignore
    from openai.error import OpenAIError  # type: ignore


logger = logging.getLogger("orchestrator.adapters.openai")


class MissingOpenAIKeyError(RuntimeError):
    """Raised when an OpenAI client is requested without a valid API key."""


def get_openai_client(api_key: str | None = None) -> OpenAI:
    """Create an OpenAI client after validating the API key."""
    resolved_key = (api_key or os.getenv("OPENAI_API_KEY", "")).strip()
    if not resolved_key or resolved_key.lower() == "replace-me":
        logger.debug("OpenAI client requested but API key is missing or placeholder")
        raise MissingOpenAIKeyError("OpenAI API key is not configured")

    return OpenAI(api_key=resolved_key)


__all__ = ["MissingOpenAIKeyError", "OpenAIError", "get_openai_client"]
