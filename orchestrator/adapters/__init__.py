"""Adapter layer providing integrations with external services."""

from .openai_adapter import MissingOpenAIKeyError, OpenAIError, get_openai_client

__all__ = [
    "MissingOpenAIKeyError",
    "OpenAIError",
    "get_openai_client",
]
