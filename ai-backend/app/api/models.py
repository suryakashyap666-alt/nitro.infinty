"""
ai-backend/app/api/models.py

GET /api/v1/models?providerId=...

Exposes selectable model IDs per provider. This is static, hand-maintained
metadata for now (no upstream "list models" calls are made on the
browser's behalf, since some of those calls require a key we don't hold
for user-supplied providers). It's deliberately structured so a future
engine that CAN enumerate its own models (e.g. by calling the provider
with the user's key) can plug in without changing this route's shape.
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/v1", tags=["models"])


__MODEL_CATALOG: Dict[str, List[Dict[str, Any]]] = {
    "nitro": [
        {"modelId": "nitro-v1", "displayName": "Nitro v1 (default)", "isDefault": True},
    ],
    "nitro-brain": [
        {"modelId": "nitro-brain-v1", "displayName": "Nitro Brain v1 (default)", "isDefault": True},
    ],
    "openai": [
        {"modelId": "gpt-4o-mini", "displayName": "GPT-4o mini", "isDefault": True},
        {"modelId": "gpt-4o", "displayName": "GPT-4o", "isDefault": False},
    ],
    "groq": [
        {"modelId": "llama-3.3-70b-versatile", "displayName": "Llama 3.3 70B", "isDefault": True},
    ],
    "openrouter": [
        {"modelId": "google/gemma-2-9b-it:free", "displayName": "Gemma 2 9B (free)", "isDefault": True},
    ],
    "together": [
        {"modelId": "meta-llama/Llama-3.3-70B-Instruct-Turbo", "displayName": "Llama 3.3 70B Turbo", "isDefault": True},
    ],
    "gemini": [
        {"modelId": "gemini-2.0-flash", "displayName": "Gemini 2.0 Flash", "isDefault": True},
    ],
    "claude": [
        {"modelId": "claude-sonnet-4-6", "displayName": "Claude Sonnet 4.6", "isDefault": True},
    ],
    "qwen": [
        {"modelId": "qwen2.5-72b-instruct", "displayName": "Qwen 2.5 72B Instruct", "isDefault": True},
    ],
}


@router.get("/models")
def list_models(providerId: str = Query(..., min_length=1)) -> Dict[str, Any]:
    normalized = providerId.strip().lower()
    models = __MODEL_CATALOG.get(normalized)
    if models is None:
        raise HTTPException(status_code=404, detail=f"Unknown providerId '{providerId}'.")
    return {"providerId": normalized, "models": models}