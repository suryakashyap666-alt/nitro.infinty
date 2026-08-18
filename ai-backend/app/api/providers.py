"""
ai-backend/app/api/providers.py

GET /api/v1/providers — Catalog of Nitro AI native engines and specialized bot roles.
"""
from __future__ import annotations

from typing import Any, Dict, List
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["providers"])

NITRO_SYSTEM_ROLES: List[Dict[str, Any]] = [
    {"roleId": "core_reasoning", "name": "Nitro Core Reasoning & Logic", "engine": "Nitro Core"},
    {"roleId": "math_solver", "name": "Nitro Step-by-Step Math & Calculus Solver", "engine": "Nitro MathEngine"},
    {"roleId": "code_architect", "name": "Nitro Coding & Software Assistant", "engine": "Nitro CodingEngine"},
    {"roleId": "image_studio", "name": "Nitro Color & Vector Image Studio", "engine": "Nitro ImageSystem"},
    {"roleId": "educator", "name": "Nitro Adaptive Curriculum & Exam Engine", "engine": "Nitro EducationEngine"},
    {"roleId": "profession_ai", "name": "Nitro Profession & Career Workflow Assistant", "engine": "Nitro ProfessionEngine"},
    {"roleId": "voice_engine", "name": "Nitro Voice & Speech Synthesis", "engine": "Nitro VoiceSystem"},
]


@router.get("/providers")
def get_providers() -> Dict[str, Any]:
    return {
        "provider": {
            "providerId": "nitro",
            "displayName": "Nitro Infinity AI",
            "description": "Self-contained, provider-agnostic native AI engine with memory, bots, and multimodal capabilities.",
            "isDefault": True,
            "roles": NITRO_SYSTEM_ROLES,
        }
    }