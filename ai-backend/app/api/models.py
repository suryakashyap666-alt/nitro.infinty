"""
ai-backend/app/api/models.py

GET /api/v1/models — Returns native Nitro AI model capabilities.
"""
from __future__ import annotations

from typing import Any, Dict, List
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["models"])

NITRO_MODELS: List[Dict[str, Any]] = [
    {
        "modelId": "nitro-v1",
        "displayName": "Nitro Infinity AI Core (Unified)",
        "isDefault": True,
        "capabilities": ["chat", "math", "coding", "image_generation", "education", "reasoning"],
    },
    {
        "modelId": "nitro-brain-v1",
        "displayName": "Nitro Local Brain (Offline / Fast)",
        "isDefault": False,
        "capabilities": ["chat", "math", "coding", "learning_graph", "heuristics"],
    },
]


@router.get("/models")
def list_models() -> Dict[str, Any]:
    return {"providerId": "nitro", "models": NITRO_MODELS}