"""Nitro Infinity AI Global Multilingual System"""
from __future__ import annotations
import json, os, re
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from typing import Tuple

SUPPORTED_LANGUAGES = {

    'en': {'name': 'English', 'native': 'English', 'flag': 'GB', 'speech': 'en-US', 'enabled': True},
    'hi': {'name': 'Hindi', 'native': '\u0939\u093f\u0902\u0926\u0940', 'flag': 'IN', 'speech': 'hi-IN', 'enabled': True},
    'ja': {'name': 'Japanese', 'native': '\u65e5\u672c\u8a9e', 'flag': 'JP', 'speech': 'ja-JP', 'enabled': True},
    'ar': {'name': 'Arabic', 'native': '\u0627\u0644\u0639\u0631\u0628\u064a\u0629', 'flag': 'SA', 'speech': 'ar-SA', 'enabled': True},
    'es': {'name': 'Spanish', 'native': 'Espanol', 'flag': 'ES', 'speech': 'es-ES', 'enabled': True},
    'fr': {'name': 'French', 'native': 'Francais', 'flag': 'FR', 'speech': 'fr-FR', 'enabled': True},
    'zh': {'name': 'Chinese', 'native': '\u4e2d\u6587', 'flag': 'CN', 'speech': 'zh-CN', 'enabled': True},
    'ru': {'name': 'Russian', 'native': '\u0420\u0443\u0441\u0441\u043a\u0438\u0439', 'flag': 'RU', 'speech': 'ru-RU', 'enabled': True},
    'bn': {'name': 'Bengali', 'native': '\u09ac\u09be\u0982\u09b2\u09be', 'flag': 'BD', 'speech': 'bn-BD', 'enabled': True},
    'ta': {'name': 'Tamil', 'native': '\u0ba4\u0bae\u0bbf\u0bb4\u0bcd', 'flag': 'IN', 'speech': 'ta-IN', 'enabled': True},
    'ur': {'name': 'Urdu', 'native': '\u0627\u0631\u062f\u0648', 'flag': 'PK', 'speech': 'ur-PK', 'enabled': True},
    'de': {'name': 'German', 'native': 'Deutsch', 'flag': 'DE', 'speech': 'de-DE', 'enabled': True},
    'pt': {'name': 'Portuguese', 'native': 'Portugues', 'flag': 'BR', 'speech': 'pt-BR', 'enabled': True},
    'ko': {'name': 'Korean', 'native': '\ud55c\uad6d\uc5b4', 'flag': 'KR', 'speech': 'ko-KR', 'enabled': True},
    'vi': {'name': 'Vietnamese', 'native': 'Tieng Viet', 'flag': 'VN', 'speech': 'vi-VN', 'enabled': True},
    'th': {'name': 'Thai', 'native': '\u0e44\u0e17\u0e22', 'flag': 'TH', 'speech': 'th-TH', 'enabled': True},
    'id': {'name': 'Indonesian', 'native': 'Bahasa Indonesia', 'flag': 'ID', 'speech': 'id-ID', 'enabled': True},
    'tr': {'name': 'Turkish', 'native': 'Turkce', 'flag': 'TR', 'speech': 'tr-TR', 'enabled': True},
    'it': {'name': 'Italian', 'native': 'Italiano', 'flag': 'IT', 'speech': 'it-IT', 'enabled': True},
    'te': {'name': 'Telugu', 'native': '\u0c24\u0c46\u0c32\u0c41\u0c17\u0c41', 'flag': 'IN', 'speech': 'te-IN', 'enabled': True},
    'mr': {'name': 'Marathi', 'native': '\u092e\u0930\u093e\u0920\u0940', 'flag': 'IN', 'speech': 'mr-IN', 'enabled': True},
    'ms': {'name': 'Malay', 'native': 'Bahasa Melayu', 'flag': 'MY', 'speech': 'ms-MY', 'enabled': True},
    'fa': {'name': 'Persian', 'native': '\u0641\u0627\u0631\u0633\u06cc', 'flag': 'IR', 'speech': 'fa-IR', 'enabled': True},
}


# Character ranges for language detection
CHAR_RANGES = {
    'hi': (0x0900, 0x097F),  # Devanagari
    'ta': (0x0B80, 0x0BFF),  # Tamil
    'te': (0x0C60, 0x0C7F),  # Telugu
    'bn': (0x0980, 0x09FF),  # Bengali
    'ur': (0x0600, 0x06FF),  # Arabic
    'ar': (0x0600, 0x06FF),
    'ja': (0x4E00, 0x9FFF),  # CJK
    'zh': (0x4E00, 0x9FFF),
    'ko': (0xAC00, 0xD7AF),  # Hangul
    'th': (0x0E00, 0x0E7F),  # Thai
    'mr': (0x0900, 0x097F),  # Marathi (Devanagari)
    'te': (0x0C60, 0x0C7F),
}

# Common keywords per language
KEYWORD_PATTERNS = {
    'en': ['hello', 'hi', 'hey', 'thanks', 'what', 'how', 'please', 'yes', 'no'],
    'hi': ['नमस्ते', 'हाय', 'धन्यवाद', 'क्या', 'कैसे', 'कृपया', 'हाँ', 'नहीं'],
    'es': ['hola', 'gracias', 'como', 'que', 'si', 'no', 'por favor'],
    'fr': ['bonjour', 'salut', 'merci', 'comment', 'quoi', 'oui', 'non', 's\'il vous plaît'],
    'de': ['hallo', 'danke', 'wie', 'was', 'ja', 'nein', 'bitte'],
    'ja': ['こんにちは', 'ありがとう', 'どうですか', 'はい', 'いいえ'],
    'zh': ['你好', '谢谢', '什么', '是', '不是'],
    'ar': ['مرحبا', 'شكرا', 'كيف', 'ماذا', 'نعم', 'لا'],
    'pt': ['olá', 'obrigado', 'como', 'o que', 'sim', 'não', 'por favor'],
    'ru': ['привет', 'спасибо', 'как', 'что', 'да', 'нет', 'пожалуйста'],
    'it': ['ciao', 'grazie', 'come', 'cosa', 'sì', 'no', 'per favore'],
}


def detect_language(text: str) -> str:
    """Detect language from text using character ranges and keywords.
    Returns language code (e.g., 'en', 'hi', 'ja').
    """
    if not text or len(text.strip()) == 0:
        return 'en'  # default to English

    text_lower = text.lower()
    text_chars = set(ord(c) for c in text if ord(c) > 127)  # non-ASCII chars

    # Check for specific script characters
    script_scores = {}
    for lang, (start, end) in CHAR_RANGES.items():
        count = sum(1 for c in text_chars if start <= c <= end)
        if count > 0:
            script_scores[lang] = count

    if script_scores:
        detected = max(script_scores, key=script_scores.get)
        if detected in SUPPORTED_LANGUAGES and SUPPORTED_LANGUAGES[detected].get('enabled'):
            return detected

    # Fallback: check keywords
    for lang, keywords in KEYWORD_PATTERNS.items():
        for kw in keywords:
            if kw in text_lower:
                if lang in SUPPORTED_LANGUAGES and SUPPORTED_LANGUAGES[lang].get('enabled'):
                    return lang

    # Default to English if no language detected
    return 'en'


def get_speech_lang(lang_code: str) -> str:
    """Get speech API language code for TTS/STT."""
    if lang_code in SUPPORTED_LANGUAGES:
        return SUPPORTED_LANGUAGES[lang_code].get('speech', 'en-US')
    return 'en-US'


def get_supported_languages_list() -> List[Dict[str, Any]]:
    """Return list of all supported languages for UI."""
    return [
        {
            'code': code,
            'name': info['name'],
            'native': info['native'],
            'flag': info['flag'],
            'enabled': info.get('enabled', True),
        }
        for code, info in SUPPORTED_LANGUAGES.items()
        if info.get('enabled', True)
    ]
