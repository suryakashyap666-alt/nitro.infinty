"""
ai-backend/app/api/health.py

GET /api/v1/health — Versioned health check for Nitro AI.
"""
from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health")
def health_v1() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": "nitro-infinity-ai",
        "engine": "Nitro Brain Core",
        "apiVersion": "v1",
    }