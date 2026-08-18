"""
ai-backend/app/api/models.py

GET /api/v1/models — Returns native Nitro AI model catalog.
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
        "capabilities": [
            "core_reasoning",
            "math_solving",
            "code_architecture",
            "image_generation",
            "curriculum_education",
            "exam_generation",
            "profession_workflows",
            "voice_synthesis",
        ],
    },
    {
        "modelId": "nitro-brain-v1",
        "displayName": "Nitro Local Brain (Fast / Offline)",
        "isDefault": False,
        "capabilities": ["chat", "math", "coding", "learning_graph", "heuristics"],
    },
]


@router.get("/models")
def list_models() -> Dict[str, Any]:
    return {"providerId": "nitro", "models": NITRO_MODELS}