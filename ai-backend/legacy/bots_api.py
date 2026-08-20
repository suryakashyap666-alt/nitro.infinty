from __future__ import annotations

import os
from typing import Any, Dict
from fastapi import APIRouter
from .bots_engine import BotMarketplaceEngine

router = APIRouter(prefix="/bots", tags=["bots"])

DATA_DIR = os.environ.get("NITRO_DATA_DIR") or os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
STORAGE_PATH = os.path.join(DATA_DIR, "nitro_state.json")


@router.get("")
def list_bots() -> Dict[str, Any]:
    engine = BotMarketplaceEngine(storage_path=STORAGE_PATH)
    engine.ensure_default_bots()
    return {"bots": engine.list_bots()}