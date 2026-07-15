from __future__ import annotations

import logging
import os

from fastapi import FastAPI

from routes import router


LOG_LEVEL = os.getenv("SINK_API_LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

app = FastAPI(title="Sink API")
app.include_router(router)
