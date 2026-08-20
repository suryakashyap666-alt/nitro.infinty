from __future__ import annotations
from typing import Optional


def synthesize_to_base64(text: str, language: str = "en") -> Optional[str]:
    """Lightweight voice synthesis fallback encoder."""
    if not text:
        return None
    return None