"""
ai-backend/app/main.py

Unified FastAPI Application for Nitro Infinity AI.
Hosts the Core Brain, Nitro Bots, Multimodal Image Studio, Voice Engine,
and API v1 Routes under secure Nitro API key authentication.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure package directory is on Python path
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

# Import Core Nitro Engines
from brain.core import CoreBrain
from legacy.bots_engine import BotMarketplaceEngine
from legacy.image.image_api import router as image_router
from legacy.puzzle.puzzle_images_api import router as puzzle_router

# Import API v1 Routes
from app.api.routes import router as chat_v1_router
from app.api.health import router as health_v1_router
from app.api.models import router as models_v1_router
from app.api.providers import router as providers_v1_router

DATA_DIR = os.environ.get("NITRO_DATA_DIR") or str(BASE_DIR / "data")
os.makedirs(DATA_DIR, exist_ok=True)
STATE_FILE = os.path.join(DATA_DIR, "nitro_state.json")

# Initialize persistent Nitro AI Marketplace and Core Brain
BOT_MARKET = BotMarketplaceEngine(storage_path=STATE_FILE)
BOT_MARKET.ensure_default_bots()
BRAIN = CoreBrain(storage_path=STATE_FILE, bot_market=BOT_MARKET)

app = FastAPI(
    title="Nitro Infinity AI — Engine & API",
    version="1.0.0",
    description="Native, zero-dependency, self-contained AI engine powering Nitro AI.",
)

# CORS Configuration
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

# Attach state to app for sub-routers
app.state.brain = BRAIN
app.state.bot_market = BOT_MARKET

# Mount API v1 Routers
app.include_router(chat_v1_router)
app.include_router(health_v1_router)
app.include_router(models_v1_router)
app.include_router(providers_v1_router)

# Mount Image Studio & Puzzle Routers
app.include_router(image_router)
app.include_router(puzzle_router)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "nitro-infinity-ai",
        "version": "1.0.0",
        "engine": "Nitro Brain Core",
    }


@app.get("/api/v1/bots")
def list_bots_v1(query: str = "") -> dict:
    """Returns all active marketplace bots from Nitro AI."""
    bots_list = BOT_MARKET.list_bots()
    from legacy.bots_engine import filter_bots
    return {"ok": True, "bots": filter_bots(bots_list, query)}