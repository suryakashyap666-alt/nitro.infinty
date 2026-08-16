from __future__ import annotations

import re
from typing import Dict, List

from .language import SUPPORTED_LANGUAGES


def supported_language_codes() -> List[str]:
    return [k for k, v in SUPPORTED_LANGUAGES.items() if v.get("enabled", True)]


def get_default_language() -> str:
    return "en" if "en" in SUPPORTED_LANGUAGES else next(iter(SUPPORTED_LANGUAGES.keys()), "en")


def normalize_lang_code(code: str) -> str:
    if not code:
        return get_default_language()
    c = code.strip().lower().split("-")[0]
    return c if c in SUPPORTED_LANGUAGES else get_default_language()


def detect_language_from_text(text: str) -> str:
    """Lightweight language detection based on unicode script + a few keywords."""
    t = (text or "").strip()
    if not t:
        return get_default_language()

    # Strong script heuristics first.
    # Japanese: Hiragana/Katakana
    if re.search(r"[\u3040-\u309F\u30A0-\u30FF]", t):
        return "ja"

    # Chinese: CJK Unified Ideographs
    if re.search(r"[\u4E00-\u9FFF]", t):
        return "zh"

    # Arabic/Urdu/Arabic-script languages
    if re.search(r"[\u0600-\u06FF]", t):
        low = t.lower()
        if any(w in low for w in ["اور", "کیسے", "کتنا", "خوش", "براہ", "محبت", "براہِ", "براہ"]):
            return "ur"
        return "ar"

    # Cyrillic (Russian)
    if re.search(r"[\u0400-\u04FF]", t):
        return "ru"

    # Devanagari (Hindi)
    if re.search(r"[\u0900-\u097F]", t):
        return "hi"

    # Bengali
    if re.search(r"[\u0980-\u09FF]", t):
        return "bn"

    # Tamil
    if re.search(r"[\u0B80-\u0BFF]", t):
        return "ta"

    # Telugu
    if re.search(r"[\u0C00-\u0C7F]", t):
        return "te"

    # Latin keyword fallback.
    low = t.lower()
    if any(w in low for w in ["hola", "gracias", "por favor"]):
        return "es"
    if any(w in low for w in ["bonjour", "merci", "s\u2019il vous plait", "s\u2019il vous plaît"]):
        return "fr"
    if any(w in low for w in ["hallo", "danke", "bitte"]):
        return "de"
    if any(w in low for w in ["ol\u00e1", "obrigado", "por favor"]):
        return "pt"
    if any(w in low for w in ["merhaba", "te\u015fekk\u00fcr", "l\u00fctfen"]):
        return "tr"
    if any(w in low for w in ["ciao", "grazie", "per favore"]):
        return "it"

    return get_default_language()


def get_lang_speech_locale(lang_code: str) -> str:
    code = normalize_lang_code(lang_code)
    return SUPPORTED_LANGUAGES.get(code, {}).get("speech", "en-US")


def get_lang_display_name(lang_code: str) -> str:
    code = normalize_lang_code(lang_code)
    return SUPPORTED_LANGUAGES.get(code, {}).get("name", "English")

