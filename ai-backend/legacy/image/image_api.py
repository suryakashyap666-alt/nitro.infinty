from __future__ import annotations

import base64
import io
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile

from .image_system import (
    analyze_image_fake,
    detect_image_intent,
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


def _safe_prompt(prompt: str) -> str:
    return (prompt or "").strip()


@router.post("/generate")
def generate(
    user_id: str = Form(...),
    message: str = Form(...),
    bot_id: Optional[str] = Form(None),
) -> Dict[str, Any]:
    """Generates an image, rasterizes SVG via CairoSVG + Pillow to PNG, and returns formatted data URI."""
    prompt = _safe_prompt(message)

    block_reason = safety_block(prompt)
    if block_reason:
        raise HTTPException(status_code=400, detail=f"Blocked: {block_reason}")

    plan = plan_style_and_quality(prompt)
    image = generate_image_fake(
        prompt=prompt,
        plan=plan,
        feedback_stats=None,
        storage_dir=STORAGE_DIR,
    )

    action = {
        "type": "generate",
        "status": "done",
        "prompt": prompt,
        "style": image.get("plan", {}).get("style"),
        "quality": image.get("plan", {}).get("quality"),
        "aspect": image.get("plan", {}).get("aspect"),
        "image": image.get("image"),
        "download_url": f"/image/download/{image.get('image', {}).get('filename')}",
    }

    return {"ok": True, "action": action}


@router.post("/convert/svg2png")
async def convert_svg_endpoint(
    svg_file: Optional[UploadFile] = File(None),
    svg_raw: Optional[str] = Form(None),
) -> Response:
    """Converts uploaded SVG or raw SVG string to raw PNG bytes using CairoSVG."""
    svg_text = ""
    if svg_file:
        content = await svg_file.read()
        svg_text = content.decode("utf-8", errors="ignore")
    elif svg_raw:
        svg_text = svg_raw

    if not svg_text:
        raise HTTPException(status_code=400, detail="No SVG content provided.")

    png_bytes = svg_to_png_bytes(svg_text)
    if not png_bytes:
        raise HTTPException(status_code=500, detail="Failed to rasterize SVG to PNG.")

    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={"Content-Disposition": 'inline; filename="rendered_image.png"'},
    )


@router.get("/download/{filename}")
def download_image(filename: str) -> Response:
    """Streams a saved rendered PNG file as raw image/png."""
    safe_name = os.path.basename(filename)
    file_path = os.path.join(STORAGE_DIR, safe_name)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image file not found.")

    with open(file_path, "rb") as f:
        data = f.read()

    media_type = "image/png" if safe_name.endswith(".png") else "image/svg+xml"
    return Response(
        content=data,
        media_type=media_type,
        headers={"Content-Disposition": f'inline; filename="{safe_name}"'},
    )


@router.post("/analyze")
async def analyze(
    user_id: str = Form(...),
    message: str = Form(""),
    bot_id: Optional[str] = Form(None),
    image: UploadFile = File(...),
) -> Dict[str, Any]:
    prompt = _safe_prompt(message)

    block_reason = safety_block(prompt)
    if block_reason:
        raise HTTPException(status_code=400, detail=f"Blocked: {block_reason}")

    data = await image.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty upload")

    b64 = base64.b64encode(data).decode("ascii")
    content_type = image.content_type or "application/octet-stream"
    data_url = f"data:{content_type};base64,{b64}"

    out = analyze_image_fake(image_b64_or_url=data_url, prompt=prompt)

    action = {
        "type": "analyze",
        "status": "done",
        "prompt": prompt,
        "analysis": out.get("analysis"),
        "image": {
            "type": "data_url",
            "data_url": data_url,
            "contentType": content_type,
        },
    }

    return {"ok": True, "action": action}