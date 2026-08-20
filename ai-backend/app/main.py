from __future__ import annotations

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from brain.core import CoreBrain
from legacy.bots_engine import BotMarketplaceEngine
from legacy.image.image_api import router as image_router
from legacy.puzzle.puzzle_images_api import router as puzzle_router

from app.api.routes import router as chat_v1_router, ChatRequestPayload, chat as chat_endpoint_handler
from app.api.health import router as health_v1_router
from app.api.models import router as models_v1_router
from app.api.providers import router as providers_v1_router

DATA_DIR = os.environ.get("NITRO_DATA_DIR") or str(BASE_DIR / "data")
os.makedirs(DATA_DIR, exist_ok=True)
STATE_FILE = os.path.join(DATA_DIR, "nitro_state.json")

BOT_MARKET = BotMarketplaceEngine(storage_path=STATE_FILE)
BOT_MARKET.ensure_default_bots()
BRAIN = CoreBrain(storage_path=STATE_FILE, bot_market=BOT_MARKET)

app = FastAPI(
    title="Nitro Infinity AI — Engine & API",
    version="1.0.0",
    description="Native, self-contained AI engine powering Nitro AI.",
    docs_url="/docs",
    redoc_url="/redoc",
)

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "WEB_CLIENT_ORIGIN",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if "*" not in ALLOWED_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.brain = BRAIN
app.state.bot_market = BOT_MARKET

app.include_router(chat_v1_router)
app.include_router(health_v1_router)
app.include_router(models_v1_router)
app.include_router(providers_v1_router)
app.include_router(image_router)
app.include_router(puzzle_router)


@app.get("/")
def root() -> dict:
    return {
        "service": "Nitro Infinity AI Engine",
        "status": "online",
        "version": "1.0.0",
        "endpoints": {
            "chat": "POST /api/v1/chat",
            "health": "GET /api/v1/health",
            "bots": "GET /api/v1/bots",
            "models": "GET /api/v1/models",
            "interactive_docs": "GET /docs",
        },
    }


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "nitro-infinity-ai",
        "version": "1.0.0",
        "engine": "Nitro Brain Core",
    }


@app.get("/bots")
@app.get("/api/v1/bots")
def list_bots(query: str = "") -> dict:
    bots_list = BOT_MARKET.list_bots()
    from legacy.bots_engine import filter_bots
    return {"ok": True, "bots": filter_bots(bots_list, query)}


@app.post("/chat")
@app.post("/api/chat")
async def chat_alias(
    payload: ChatRequestPayload,
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    authorization: str | None = Header(None),
):
    return await chat_endpoint_handler(payload, x_api_key, authorization)