"""
ai-backend/app/main.py

Standalone FastAPI entrypoint for the decoupled AI microservice.
Run with: uvicorn app.main:app --host 0.0.0.0 --port 8000
(from inside ai-backend/, with ai-backend/ on PYTHONPATH — see start.sh)
"""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as chat_router
from app.api.providers import router as providers_router
from app.api.models import router as models_router
from app.api.health import router as health_router

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("WEB_CLIENT_ORIGIN", "http://localhost:3000").split(",")
    if origin.strip()
]

app = FastAPI(
    title="Nitro Infinity AI — Backend",
    version="1.0.0",
    description="Decoupled, provider-agnostic AI microservice for Nitro Infinity AI.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(providers_router)
app.include_router(models_router)
app.include_router(health_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "nitro-infinity-ai-backend"}