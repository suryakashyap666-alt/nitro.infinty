from __future__ import annotations
from typing import Any, Dict, List

SUPPORTED_LANGUAGES = {
    'en': {'name': 'English', 'native': 'English', 'flag': 'GB', 'speech': 'en-US', 'enabled': True},
    'hi': {'name': 'Hindi', 'native': 'हिन्दी', 'flag': 'IN', 'speech': 'hi-IN', 'enabled': True},
    'ja': {'name': 'Japanese', 'native': '日本語', 'flag': 'JP', 'speech': 'ja-JP', 'enabled': True},
    'ar': {'name': 'Arabic', 'native': 'العربية', 'flag': 'SA', 'speech': 'ar-SA', 'enabled': True},
    'es': {'name': 'Spanish', 'native': 'Español', 'flag': 'ES', 'speech': 'es-ES', 'enabled': True},
    'fr': {'name': 'French', 'native': 'Français', 'flag': 'FR', 'speech': 'fr-FR', 'enabled': True},
    'zh': {'name': 'Chinese', 'native': '中文', 'flag': 'CN', 'speech': 'zh-CN', 'enabled': True},
    'ru': {'name': 'Russian', 'native': 'Русский', 'flag': 'RU', 'speech': 'ru-RU', 'enabled': True},
    'bn': {'name': 'Bengali', 'native': 'বাংলা', 'flag': 'BD', 'speech': 'bn-BD', 'enabled': True},
    'de': {'name': 'German', 'native': 'Deutsch', 'flag': 'DE', 'speech': 'de-DE', 'enabled': True},
    'pt': {'name': 'Portuguese', 'native': 'Português', 'flag': 'BR', 'speech': 'pt-BR', 'enabled': True},
}


def detect_language(text: str) -> str:
    if not text or len(text.strip()) == 0:
        return 'en'
    t = text.strip()
    if any('\u0900' <= c <= '\u097f' for c in t): return 'hi'
    if any('\u4e00' <= c <= '\u9fff' for c in t): return 'zh'
    if any('\u3040' <= c <= '\u30ff' for c in t): return 'ja'
    if any('\u0600' <= c <= '\u06ff' for c in t): return 'ar'
    if any('\u0400' <= c <= '\u04ff' for c in t): return 'ru'
    return 'en'