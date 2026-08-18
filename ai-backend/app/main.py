"""
ai-backend/app/main.py

Standalone FastAPI entrypoint for the decoupled AI microservice.
"""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as chat_router

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "WEB_CLIENT_ORIGIN",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000",
    ).split(",")
    if origin.strip()
]

app = FastAPI(
    title="Nitro Infinity AI — Backend",
    version="1.0.0",
    description="Decoupled, provider-agnostic AI microservice for Nitro Infinity AI.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if "*" not in ALLOWED_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "nitro-infinity-ai-backend"}