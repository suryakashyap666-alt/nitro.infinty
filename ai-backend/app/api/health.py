"""
ai-backend/app/api/health.py

GET /api/v1/health

Versioned health check, separate from the unversioned /health already
mounted at app root in main.py (kept as-is for any existing infra that
polls it). This one lives under the /api/v1 prefix for consistency with
the rest of the API boundary.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health")
def health_v1() -> Dict[str, Any]:
    return {"status": "ok", "service": "nitro-infinity-ai-backend", "apiVersion": "v1"}