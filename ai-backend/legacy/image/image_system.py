from __future__ import annotations

import base64
import hashlib
import io
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# CairoSVG & Pillow integrations with explicit RGB/RGBA mode enforcement
try:
    import cairosvg
    CAIROSVG_AVAILABLE = True
except (ImportError, OSError):
    CAIROSVG_AVAILABLE = False
    logger.warning("cairosvg not found or system cairo library missing. Using vector data fallback.")

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
    aspect: Optional[str] = None


QUALITY_BY_KEYWORD = {
    "basic": ["basic", "std", "low"],
    "hd": ["hd", "high definition", "standard"],
    "2k": ["2k", "2-k"],
    "4k": ["4k", "4-k", "ultra hd", "8k"],
}

STYLE_PATTERNS: List[Tuple[str, List[str]]] = [
    ("cinematic", ["cinematic", "cinema", "movie scene", "dramatic lighting", "filmic"]),
    ("anime", ["anime", "manga", "ghibli", "shonen", "otaku"]),
    ("sketch", ["sketch", "hand sketch", "pencil sketch", "pencil", "charcoal", "line art"]),
    ("painting", ["painting", "oil painting", "digital painting", "illustration", "acrylic"]),
    ("hyperrealistic", ["hyperrealistic", "hyper realistic", "photoreal", "photorealistic", "ultra realistic"]),
    ("comic_style", ["comic", "comics", "graphic novel"]),
    ("watercolor", ["watercolor", "water color", "aquarelle"]),
    ("pixel_art", ["pixel art", "pixelated", "8-bit", "16-bit", "retro"]),
    ("3d_render", ["3d render", "unreal engine", "octane render", "blender", "cgi"]),
]


def _extract_quality(text: str) -> str:
    t = (text or "").lower()
    for q, needles in QUALITY_BY_KEYWORD.items():
        if any(n in t for n in needles):
            return "4K" if q == "4k" else ("2K" if q == "2k" else ("HD" if q == "hd" else "Standard"))
    return "HD"


def _extract_style(text: str) -> str:
    t = (text or "").lower()
    for style_name, needles in STYLE_PATTERNS:
        if any(n in t for n in needles):
            if style_name == "cinematic":
                return "Cinematic"
            if style_name == "anime":
                return "Anime"
            if style_name == "sketch":
                return "Pencil sketch"
            if style_name == "painting":
                return "Painting"
            if style_name == "hyperrealistic":
                return "Hyperrealistic"
            if style_name == "comic_style":
                return "Comic Art"
            if style_name == "watercolor":
                return "Watercolor"
            if style_name == "pixel_art":
                return "Pixel Art"
            if style_name == "3d_render":
                return "3D Render"
            return "Digital Art"
    return "Cinematic"


def detect_image_intent(message: str) -> Optional[ImageIntent]:
    t = (message or "").strip()
    if not t:
        return None

    lower = t.lower()

    analyze_markers = [
        "ai generated", "ai made", "human made", "is this ai",
        "tell me if this is ai", "analyze this image", "analyze image",
        "human or ai", "is this real", "detect image",
    ]
    if any(m in lower for m in analyze_markers):
        return ImageIntent(action="analyze", prompt=t)

    gen_regexes = [
        r"\b(generate|create|make|draw|paint|render|produce|design)\b.*\b(image|picture|photo|illustration|art|drawing|sketch|wallpaper|portrait|logo|avatar|graphic)\b",
        r"\b(image|picture|photo|illustration|art|sketch|wallpaper|portrait|logo)\s+(of|for|showing|depicting)\b",
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
    quality = _extract_quality(prompt)
    style = _extract_style(prompt)

    aspect = "square"
    pl = (prompt or "").lower()
    if "wallpaper" in pl or "landscape" in pl or "wide" in pl:
        aspect = "wallpaper"
    elif "portrait" in pl or "vertical" in pl or "avatar" in pl:
        aspect = "portrait"

    return ImageStylePlan(style=style, quality=quality, aspect=aspect)


def safety_block(prompt: str) -> Optional[str]:
    t = (prompt or "").lower()
    blocked = [
        ("self-harm", ["suicide", "self harm", "kill myself", "hurt myself"]),
        ("sexual content", ["explicit", "porn", "nude", "child sexual", "nsfw"]),
        ("violence", ["how to make a bomb", "weapon", "kill", "shooting", "terrorism"]),
        ("illegal", ["how to steal", "fraud", "credit card theft"]),
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
    """Converts SVG string to raw PNG bytes, strictly enforcing full 32-bit RGBA color channels."""
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

    # Enforce explicit sRGB/RGBA Color Profile via Pillow
    if png_data and PILLOW_AVAILABLE:
        try:
            image_stream = io.BytesIO(png_data)
            with PILImage.open(image_stream) as pil_img:
                # Force RGBA mode to prevent grayscale / palette-loss
                rgba_img = pil_img.convert("RGBA")
                out_stream = io.BytesIO()
                rgba_img.save(out_stream, format="PNG", optimize=True)
                return out_stream.getvalue()
        except Exception as err:
            logger.debug("Pillow RGBA conversion bypassed: %s", err)
            return png_data

    return png_data


def generate_image_fake(
    prompt: str,
    plan: ImageStylePlan,
    seed: Optional[int] = None,
    feedback_stats: Optional[Dict[str, int]] = None,
    storage_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Generates vibrant sRGB vector artwork, converts to 32-bit RGBA PNG, and creates a Data URI."""
    clean_p = (prompt or "").strip() or "Vibrant Digital Concept"
    seed_val = seed if seed is not None else (len(clean_p) * 2654435761) % 2**31

    # Rich, high-gamut color palette definition
    hue = seed_val % 360
    hue_accent = (hue + 60) % 360
    hue_highlight = (hue + 140) % 360

    primary_color = f"hsl({hue}, 85%, 60%)"
    accent_color = f"hsl({hue_accent}, 95%, 65%)"
    highlight_color = f"hsl({hue_highlight}, 100%, 75%)"
    bg_gradient_start = f"hsl({hue}, 60%, 12%)"
    bg_gradient_end = f"hsl({(hue + 40) % 360}, 70%, 5%)"

    aspect = plan.aspect or "square"
    if aspect == "wallpaper":
        w, h = 1280, 720
    elif aspect == "portrait":
        w, h = 720, 1080
    else:
        w, h = 1024, 1024

    snippet = clean_p[:120] + ("…" if len(clean_p) > 120 else "")
    escaped_snippet = (
        snippet.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    )

    # SVG with explicit sRGB color-interpolation
    svg = f"""<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}' color-interpolation='sRGB'>
  <defs>
    <linearGradient id='bgGrad' x1='0%' y1='0%' x2='100%' y2='100%'>
      <stop offset='0%' stop-color='{bg_gradient_start}'/>
      <stop offset='100%' stop-color='{bg_gradient_end}'/>
    </linearGradient>

    <radialGradient id='neonGlow' cx='50%' cy='45%' r='55%'>
      <stop offset='0%' stop-color='{accent_color}' stop-opacity='0.75'/>
      <stop offset='45%' stop-color='{primary_color}' stop-opacity='0.4'/>
      <stop offset='100%' stop-color='transparent' stop-opacity='0'/>
    </radialGradient>

    <linearGradient id='accentLine' x1='0%' y1='0%' x2='100%' y2='0%'>
      <stop offset='0%' stop-color='{primary_color}'/>
      <stop offset='50%' stop-color='{highlight_color}'/>
      <stop offset='100%' stop-color='{accent_color}'/>
    </linearGradient>

    <filter id='brightBlur' x='-30%' y='-30%' width='160%' height='160%'>
      <feGaussianBlur stdDeviation='35'/>
    </filter>
  </defs>

  <!-- Background Base -->
  <rect width='100%' height='100%' fill='url(#bgGrad)'/>

  <!-- High-Vibrancy Center Glow -->
  <circle cx='{int(w * 0.5)}' cy='{int(h * 0.44)}' r='{int(min(w, h) * 0.4)}' fill='url(#neonGlow)' filter='url(#brightBlur)'/>

  <!-- Geometric Illustration Features -->
  <g stroke='url(#accentLine)' stroke-width='2.5' fill='none' opacity='0.85'>
    <circle cx='{int(w * 0.5)}' cy='{int(h * 0.44)}' r='{int(min(w, h) * 0.28)}' stroke-dasharray='10 6'/>
    <circle cx='{int(w * 0.5)}' cy='{int(h * 0.44)}' r='{int(min(w, h) * 0.16)}' stroke-width='3.5'/>
    <polygon points='{int(w*0.5)},{int(h*0.25)} {int(w*0.65)},{int(h*0.52)} {int(w*0.35)},{int(h*0.52)}' opacity='0.6' stroke='{highlight_color}'/>
  </g>

  <!-- Header Badge -->
  <g transform='translate(36, 36)'>
    <rect width='{w - 72}' height='74' rx='16' fill='#0f172a' fill-opacity='0.85' stroke='{primary_color}' stroke-opacity='0.4' stroke-width='1.5'/>
    <text x='24' y='36' fill='{highlight_color}' font-family='system-ui, -apple-system, sans-serif' font-size='18' font-weight='800' letter-spacing='1'>⚡ NITRO INFINITY AI • COLOR STUDIO</text>
    <text x='24' y='58' fill='#94a3b8' font-family='system-ui, -apple-system, sans-serif' font-size='13'>Style: {plan.style} • Quality: {plan.quality} • Color Gamut: sRGB Full</text>
  </g>

  <!-- Prompt Box -->
  <g transform='translate(36, {h - 134})'>
    <rect width='{w - 72}' height='98' rx='16' fill='#0f172a' fill-opacity='0.9' stroke='url(#accentLine)' stroke-width='1.5'/>
    <text x='24' y='32' fill='{accent_color}' font-family='system-ui, -apple-system, sans-serif' font-size='12' font-weight='700' letter-spacing='0.5'>PROMPT</text>
    <text x='24' y='62' fill='#f8fafc' font-family='system-ui, -apple-system, sans-serif' font-size='15' font-weight='500'>{escaped_snippet}</text>
  </g>
</svg>"""

    # Rasterize SVG to 32-bit RGBA PNG
    png_bytes = svg_to_png_bytes(svg, output_width=w, output_height=h)

    if png_bytes:
        b64_png = base64.b64encode(png_bytes).decode("ascii")
        data_uri = f"data:image/png;base64,{b64_png}"
        content_type = "image/png"
    else:
        svg_bytes = svg.encode("utf-8")
        b64_svg = base64.b64encode(svg_bytes).decode("ascii")
        data_uri = f"data:image/svg+xml;base64,{b64_svg}"
        content_type = "image/svg+xml"

    file_id = hashlib.sha256(f"{clean_p}_{seed_val}".encode("utf-8")).hexdigest()[:16]
    saved_filename = f"img_{file_id}.png"

    if storage_dir:
        os.makedirs(storage_dir, exist_ok=True)
        file_path = os.path.join(storage_dir, saved_filename)
        if png_bytes:
            with open(file_path, "wb") as f:
                f.write(png_bytes)

    return {
        "image": {
            "type": "data_url",
            "data_url": data_uri,
            "contentType": content_type,
            "filename": saved_filename,
            "width": w,
            "height": h,
            "colorMode": "RGBA_sRGB",
            "generatedAt": _utc_timestamp(),
        },
        "plan": {
            "style": plan.style,
            "quality": plan.quality,
            "aspect": plan.aspect,
        },
        "seed": seed_val,
    }


def analyze_image_fake(image_b64_or_url: str, prompt: str = "") -> Dict[str, Any]:
    s = str(image_b64_or_url or "")
    t = (prompt or "").lower()
    base = len(s)

    symmetry = (base % 100) / 100.0
    texture_consistency = ((base // 3) % 100) / 100.0
    lighting_consistency = ((base // 7) % 100) / 100.0
    rendering_artifacts = ((base // 11) % 100) / 100.0

    ai_score = 0.35 * symmetry + 0.25 * rendering_artifacts + 0.2 * (1 - texture_consistency) + 0.2 * lighting_consistency
    human_score = 1.0 - ai_score

    edited = any(k in t for k in ["edited", "inpaint", "retouch", "modify"]) or (base % 2 == 0)

    ai_score = max(0.05, min(0.95, ai_score))
    human_score = 1.0 - ai_score

    label = "mixed/edited"
    if ai_score >= 0.62:
        label = "likely AI-generated"
    elif human_score >= 0.62:
        label = "likely human-made"

    indicators = {
        "pattern_repetition": float(symmetry),
        "rendering_artifacts": float(rendering_artifacts),
        "lighting_coherence": float(lighting_consistency),
        "texture_consistency": float(texture_consistency),
        "manipulation_likelihood": float(0.55 if edited else 0.25),
    }

    return {
        "analysis": {
            "ai_probability": ai_score,
            "human_probability": human_score,
            "likely_label": label,
            "edited": bool(edited),
            "indicators": indicators,
            "generatedAt": _utc_timestamp(),
        }
    }