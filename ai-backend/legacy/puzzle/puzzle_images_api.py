from __future__ import annotations

import base64
import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, Form, UploadFile

router = APIRouter(prefix="/puzzles", tags=["puzzles"])


@router.post("/image/solve")
async def solve_puzzle_image(
    user_id: str = Form(...),
    message: str = Form(""),
    hint_mode: Optional[str] = Form(None),
    image: UploadFile = Form(...),
) -> Dict[str, Any]:
    from .puzzle_engine import PuzzleEngine

    data = await image.read()
    if not data:
        return {"recognized": False, "puzzle_type": "unknown", "reply": "No image bytes received."}

    image_b64 = base64.b64encode(data).decode("utf-8")
    storage_path = os.path.join(os.path.dirname(__file__), "..", "data", "nitro_state.json")

    engine = PuzzleEngine(storage_path=os.path.abspath(storage_path))
    result = engine.solve(
        user_id=str(user_id),
        message=str(message or "#puzzle"),
        bot_education_enabled=True,
        image_b64=image_b64,
        hint_mode=hint_mode,
    )

    return {
        "recognized": result.recognized,
        "puzzle_type": result.puzzle_type,
        "reply": result.reply,
        "final_answer": result.final_answer,
        "steps": result.steps,
        "solving_trick": result.solving_trick,
    }