from __future__ import annotations

import base64
import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, Form, HTTPException, Response, UploadFile

from .image_system import (
    analyze_image_fake,
    generate_image_fake,
    plan_style_and_quality,
    safety_block,
    svg_to_png_bytes,
)

router = APIRouter(prefix="/image", tags=["image"])

STORAGE_DIR = os.environ.get("NITRO_IMAGE_DIR") or os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "images"
)
os.makedirs(STORAGE_DIR, exist_ok=True)


@router.post("/generate")
def generate(
    user_id: str = Form(...),
    message: str = Form(...),
    bot_id: Optional[str] = Form(None),
) -> Dict[str, Any]:
    prompt = (message or "").strip()
    block_reason = safety_block(prompt)
    if block_reason:
        raise HTTPException(status_code=400, detail=f"Blocked: {block_reason}")

    plan = plan_style_and_quality(prompt)
    image = generate_image_fake(prompt=prompt, plan=plan, storage_dir=STORAGE_DIR)

    action = {
        "type": "generate",
        "status": "done",
        "prompt": prompt,
        "style": image.get("plan", {}).get("style"),
        "quality": image.get("plan", {}).get("quality"),
        "aspect": image.get("plan", {}).get("aspect"),
        "image": image.get("image"),
    }

    return {"ok": True, "action": action}


@router.post("/analyze")
async def analyze(
    user_id: str = Form(...),
    message: str = Form(""),
    image: UploadFile = Form(...),
) -> Dict[str, Any]:
    data = await image.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty image data")

    b64 = base64.b64encode(data).decode("ascii")
    data_url = f"data:{image.content_type or 'image/png'};base64,{b64}"
    out = analyze_image_fake(image_b64_or_url=data_url, prompt=message)

    return {"ok": True, "analysis": out.get("analysis")}