from __future__ import annotations

import base64
import hashlib
import io
import logging
import os
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# CairoSVG & Pillow integrations
try:
    import cairosvg
    CAIROSVG_AVAILABLE = True
except (ImportError, OSError):
    CAIROSVG_AVAILABLE = False

try:
    from PIL import Image as PILImage
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False


@dataclass
class ImageIntent:
    action: str  # 'generate' or 'analyze'
    prompt: str


@dataclass
class ImageStylePlan:
    style: str
    quality: str
    aspect: str  # 'landscape', 'portrait', 'square'
    width: int
    height: int


def detect_image_intent(message: str) -> Optional[ImageIntent]:
    t = (message or "").strip()
    if not t:
        return None

    lower = t.lower()

    if any(m in lower for m in ["analyze this image", "is this ai", "detect image", "check image"]):
        return ImageIntent(action="analyze", prompt=t)

    gen_regexes = [
        r"\b(generate|create|make|draw|paint|render|produce|design)\b.*\b(image|picture|photo|illustration|art|drawing|sketch|wallpaper|portrait)\b",
        r"\b(image|picture|photo|illustration|art|drawing)\s+(of|for|showing|depicting)\b",
        r"^(draw|paint|sketch|illustrate)\s+",
        r"^(generate|create|make)\s+(an?\s+)?(image|picture|photo|art|wallpaper)",
    ]

    for pat in gen_regexes:
        if re.search(pat, lower):
            cleaned_prompt = re.sub(
                r"^(please\s+)?(can you\s+)?(generate|create|make|draw|paint|render|produce)\s+(an?\s+)?(image|picture|photo|illustration|art|drawing|sketch|wallpaper|portrait)?\s*(of|for|showing|depicting)?\s*",
                "",
                t,
                flags=re.IGNORECASE,
            ).strip()
            return ImageIntent(action="generate", prompt=cleaned_prompt or t)

    return None


def plan_style_and_quality(prompt: str) -> ImageStylePlan:
    """Intelligently detects the scene and auto-sets optimal dimensions to prevent cropping."""
    pl = (prompt or "").lower()

    # Landscape keywords (wide scenes, environments, epic monsters, space)
    landscape_triggers = [
        "wallpaper", "landscape", "wide", "cinematic", "space", "universe",
        "dragon", "galaxy", "planet", "city", "background", "panorama",
        "horizon", "skyline", "mountain", "ocean", "battle", "epic"
    ]

    # Portrait keywords (people, characters, full body standing shots)
    portrait_triggers = [
        "portrait", "vertical", "phone", "full body", "standing", "model",
        "person", "man", "woman", "warrior", "character", "costume", "outfit"
    ]

    if any(k in pl for k in portrait_triggers) and not any(k in pl for k in ["wallpaper", "space", "panorama"]):
        aspect = "portrait"
        width, height = 432, 768  # Clean 9:16 ratio
    elif any(k in pl for k in landscape_triggers):
        aspect = "landscape"
        width, height = 768, 432  # Cinematic 16:9 ratio
    else:
        aspect = "square"
        width, height = 576, 576  # Balanced 1:1 ratio

    return ImageStylePlan(
        style="Digital Art",
        quality="HD",
        aspect=aspect,
        width=width,
        height=height,
    )


def safety_block(prompt: str) -> Optional[str]:
    t = (prompt or "").lower()
    blocked = [
        ("self-harm", ["suicide", "self harm"]),
        ("sexual content", ["explicit", "porn", "nude", "nsfw"]),
        ("violence", ["how to make a bomb", "mass shooting"]),
    ]
    for reason, needles in blocked:
        if any(n in t for n in needles):
            return reason
    return None


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def svg_to_png_bytes(
    svg_code: str,
    output_width: Optional[int] = None,
    output_height: Optional[int] = None,
) -> Optional[bytes]:
    """Converts SVG string to raw PNG bytes, enforcing full 32-bit RGBA color channels."""
    if not svg_code or not svg_code.strip():
        return None

    svg_str = svg_code.strip()
    if not svg_str.startswith("<svg") and "<svg" in svg_str:
        m = re.search(r"<svg[\s\S]*?</svg>", svg_str)
        if m:
            svg_str = m.group(0)

    png_data = None

    if CAIROSVG_AVAILABLE:
        try:
            kwargs: Dict[str, Any] = {"bytestring": svg_str.encode("utf-8")}
            if output_width:
                kwargs["output_width"] = output_width
            if output_height:
                kwargs["output_height"] = output_height
            png_data = cairosvg.svg2png(**kwargs)
        except Exception as err:
            logger.warning("CairoSVG conversion error: %s", err)
            png_data = None

    if png_data and PILLOW_AVAILABLE:
        try:
            image_stream = io.BytesIO(png_data)
            with PILImage.open(image_stream) as pil_img:
                rgba_img = pil_img.convert("RGBA")
                out_stream = io.BytesIO()
                rgba_img.save(out_stream, format="PNG", optimize=True)
                return out_stream.getvalue()
        except Exception as err:
            return png_data

    return png_data or svg_code.encode("utf-8")


def generate_image_fake(
    prompt: str,
    plan: Optional[ImageStylePlan] = None,
    seed: Optional[int] = None,
    feedback_stats: Optional[Dict[str, int]] = None,
    storage_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Auto-sizes dimensions and applies anti-cutoff prompt framing to guarantee complete subject visibility."""
    clean_prompt = (prompt or "").strip() or "cybernetic dragon in deep space"

    # Auto-plan dimensions if not passed
    resolved_plan = plan or plan_style_and_quality(clean_prompt)
    width, height = resolved_plan.width, resolved_plan.height

    # Anti-cutoff camera framing prompt modifier
    framing_enhancer = "centered composition, wide angle shot, fully in frame, cinematic framing, complete subject, highly detailed, perfect lighting, no cutoff"
    enhanced_prompt = f"{clean_prompt}, {framing_enhancer}"

    encoded_prompt = urllib.parse.quote(enhanced_prompt)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true&model=turbo"

    png_bytes = None
    try:
        req = urllib.request.Request(
            image_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            png_bytes = resp.read()
    except Exception as e:
        logger.warning("Turbo image timeout/fallback: %s", e)

    # Fallback SVG if offline
    if not png_bytes or len(png_bytes) < 100:
        svg = f"""<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}'>
          <defs>
            <linearGradient id='bg' x1='0%' y1='0%' x2='100%' y2='100%'>
              <stop offset='0%' stop-color='#0f172a'/>
              <stop offset='100%' stop-color='#0284c7'/>
            </linearGradient>
          </defs>
          <rect width='100%' height='100%' fill='url(#bg)'/>
          <circle cx='{width//2}' cy='{height//2}' r='{min(width, height)//3}' fill='#38bdf8' opacity='0.85'/>
          <text x='{width//2}' y='{height - 30}' fill='#ffffff' font-size='15' font-family='sans-serif' text-anchor='middle'>⚡ NITRO AI: {clean_prompt[:30]}</text>
        </svg>"""
        png_bytes = svg.encode("utf-8")
        data_uri = f"data:image/svg+xml;base64,{base64.b64encode(png_bytes).decode('ascii')}"
        content_type = "image/svg+xml"
    else:
        b64_png = base64.b64encode(png_bytes).decode("ascii")
        data_uri = f"data:image/png;base64,{b64_png}"
        content_type = "image/png"

    file_id = hashlib.sha256(clean_prompt.encode("utf-8")).hexdigest()[:12]
    filename = f"img_{file_id}.png"

    if storage_dir and png_bytes:
        os.makedirs(storage_dir, exist_ok=True)
        file_path = os.path.join(storage_dir, filename)
        try:
            with open(file_path, "wb") as f:
                f.write(png_bytes)
        except Exception:
            pass

    return {
        "image": {
            "type": "data_url",
            "data_url": data_uri,
            "direct_url": image_url,
            "contentType": content_type,
            "filename": filename,
            "width": width,
            "height": height,
            "aspect": resolved_plan.aspect,
            "generatedAt": _utc_timestamp(),
        },
        "plan": {
            "style": resolved_plan.style,
            "quality": resolved_plan.quality,
            "aspect": resolved_plan.aspect,
            "width": width,
            "height": height,
        },
        "prompt": clean_prompt,
    }


def analyze_image_fake(image_b64_or_url: str, prompt: str = "") -> Dict[str, Any]:
    return {
        "analysis": {
            "ai_probability": 0.88,
            "human_probability": 0.12,
            "likely_label": "likely AI-generated",
            "generatedAt": _utc_timestamp(),
        }
    }