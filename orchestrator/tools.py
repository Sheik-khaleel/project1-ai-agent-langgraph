from __future__ import annotations

import logging
from typing import Any

import httpx


logger = logging.getLogger("orchestrator.tools")


def fetch_from_source(url: str, *, timeout: float = 10.0) -> list[dict[str, Any]]:
    """Retrieve data from the upstream source API."""
    logger.info("Fetching from source", extra={"url": url, "timeout": timeout})
    response = httpx.get(url, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list):
        msg = "Expected JSON array from source API"
        raise ValueError(msg)
    records = [item for item in payload if isinstance(item, dict)]
    logger.info("Fetched payload from source", extra={"records": len(records)})
    return records


def post_to_sink(url: str, payload: dict[str, Any], *, timeout: float = 10.0) -> dict[str, Any]:
    """Send transformed data to the sink API and return its response."""
    logger.info(
        "Posting to sink",
        extra={
            "url": url,
            "timeout": timeout,
            "records": len(payload.get("records", [])),
        },
    )
    response = httpx.post(url, json=payload, timeout=timeout)
    response.raise_for_status()
    body = response.json()
    if not isinstance(body, dict):
        msg = "Expected JSON object from sink API"
        raise ValueError(msg)
    logger.info("Received response from sink", extra={"keys": list(body.keys())})
    return body
