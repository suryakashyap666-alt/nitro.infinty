from __future__ import annotations

SUPPORTED_LANGUAGES = ["en", "hi", "es", "fr", "de", "ja", "zh", "ru", "ar", "pt"]


def detect_language_from_text(text: str) -> str:
    t = (text or "").strip()
    if not t:
        return "en"
    if any("\u0900" <= c <= "\u097f" for c in t): return "hi"
    if any("\u4e00" <= c <= "\u9fff" for c in t): return "zh"
    if any("\u3040" <= c <= "\u30ff" for c in t): return "ja"
    if any("\u0600" <= c <= "\u06ff" for c in t): return "ar"
    if any("\u0400" <= c <= "\u04ff" for c in t): return "ru"
    return "en"


def normalize_lang_code(code: str) -> str:
    if not code:
        return "en"
    return code.strip().lower().split("-")[0]