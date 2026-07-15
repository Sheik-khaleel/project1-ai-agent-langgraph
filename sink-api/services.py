from __future__ import annotations

import logging

from schemas import RecordsPayload, RecordsResponse
from database import all_records, count_records, extend_records

logger = logging.getLogger("sink_api.services")


class RecordsService:
    """Business logic for managing records in the sink API."""

    @staticmethod
    def list_records() -> RecordsResponse:
        records = all_records()
        logger.info("Listing records", extra={"count": len(records)})
        return RecordsResponse(count=len(records), records=records)

    @staticmethod
    def ingest_records(payload: RecordsPayload) -> RecordsResponse:
        logger.info("Ingest request received", extra={"count": len(payload.records)})
        if not payload.records:
            logger.warning("Rejecting ingest due to missing records")
            raise ValueError("No records supplied")

        extend_records(payload.records)
        logger.info(
            "Records ingested",
            extra={"stored": len(payload.records), "total": count_records()},
        )
        return RecordsResponse(count=len(payload.records), records=payload.records)
