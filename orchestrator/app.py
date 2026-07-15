from __future__ import annotations

import logging
from os import getenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from orchestrator.routes import router

LOG_LEVEL = getenv("ORCHESTRATOR_LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
app = FastAPI(title="Agentic Orchestrator")

allowed_origins = getenv("CORS_ALLOW_ORIGINS", "*")
allow_credentials_env = getenv("CORS_ALLOW_CREDENTIALS", "false").lower()
allow_credentials = allow_credentials_env in {"1", "true", "yes"}

if allowed_origins == "*":
    cors_origins = ["*"]
else:
    cors_origins = [origin.strip() for origin in allowed_origins.split(",") if origin.strip()]

if not cors_origins:
    cors_origins = ["*"]

if cors_origins == ["*"] and allow_credentials:
    allow_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
