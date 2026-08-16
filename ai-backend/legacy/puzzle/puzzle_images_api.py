from __future__ import annotations

import base64
import hashlib
import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, File, Form, UploadFile

router = APIRouter(prefix="/puzzles", tags=["puzzles"])


def _b64_sha256(b64: str) -> str:
    h = hashlib.sha256()
    h.update(b64.encode("utf-8"))
    return h.hexdigest()


@router.post("/image/solve")
async def solve_puzzle_image(
    user_id: str = Form(...),
    message: str = Form(""),
    hint_mode: Optional[str] = Form(None),
    image: UploadFile = File(...),
) -> Dict[str, Any]:
    """MVP image ingestion endpoint.

    - Accepts multipart image upload.
    - Encodes to base64 and passes into PuzzleEngine.

    OCR/image parsing is not implemented in this repo; puzzle solving is still text-first.
    """

    from .puzzle_engine import PuzzleEngine

    data = await image.read()
    if not data:
        return {"recognized": False, "puzzle_type": "unknown", "reply": "No image bytes received."}

    max_bytes = 5 * 1024 * 1024
    if len(data) > max_bytes:
        return {"recognized": False, "puzzle_type": "unknown", "reply": "Image too large. Please upload <= 5MB."}

    image_b64 = base64.b64encode(data).decode("utf-8")

    # Use same storage location Nitro uses
    storage_path = os.path.join(os.path.dirname(__file__), "..", "data", "nitro_state.json")
    storage_path = os.path.abspath(storage_path)

    engine = PuzzleEngine(storage_path=storage_path)

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
        "reasoning_path": result.reasoning_path,
        "hint_logic": result.hint_logic,
        "image_fingerprint": _b64_sha256(image_b64[:20000]),
    }

