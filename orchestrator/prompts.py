from __future__ import annotations

FETCH_AGENT_PROMPT = """You are FetchAgent, responsible for downloading data."""
POST_AGENT_PROMPT = """You are PostAgent, responsible for transforming and persisting data."""
INTENT_CLASSIFIER_PROMPT = (
    "You analyze user requests about task ingestion. Respond with JSON containing "
    "'supported' (true if the request should trigger todo ingestion) and 'limit' "
    "(an integer count of todos to ingest or null when unspecified). "
    "User message: {message}"
)
