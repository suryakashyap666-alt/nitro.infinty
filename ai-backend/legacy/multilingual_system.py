from __future__ import annotations

"""Nitro Infinity AI global multilingual system helpers.

This repo uses lightweight language detection based on unicode script.
We implement: bot-aware language policy + effective reply language selection.

NOTE: This file intentionally stays lightweight and dependency-free.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .language import SUPPORTED_LANGUAGES
from .multilingual import normalize_lang_code, get_default_language



@dataclass
class BotLanguagePolicy:
    use_global_language_system: bool = True
    selected_languages: Optional[List[str]] = None

    @staticmethod
    def from_state(state: Dict[str, Any] | None) -> "BotLanguagePolicy":
        s = state or {}
        use_global = bool(s.get("useGlobalLanguageSystem", True))
        langs = s.get("selectedLanguages") or s.get("selected_languages") or None
        if isinstance(langs, str):
            langs = [langs]
        if isinstance(langs, list):
            langs = [normalize_lang_code(x) for x in langs if x]
        else:
            langs = None
        return BotLanguagePolicy(use_global_language_system=use_global, selected_languages=langs)


def normalize_language_list(langs: Optional[List[str]]) -> List[str]:
    if not langs:
        return []
    out: List[str] = []
    for x in langs:
        if not x:
            continue
        out.append(normalize_lang_code(str(x)))
    # de-dupe while preserving order
    seen = set()
    deduped: List[str] = []
    for x in out:
        if x in seen:
            continue
        seen.add(x)
        deduped.append(x)
    return deduped


def enabled_supported_languages() -> List[str]:
    return [k for k, v in SUPPORTED_LANGUAGES.items() if v.get("enabled", True)]


def get_effective_supported_languages(policy: BotLanguagePolicy) -> List[str]:
    if policy.use_global_language_system:
        return enabled_supported_languages()
    return normalize_language_list(policy.selected_languages)


def pick_reply_language(
    *,
    policy: BotLanguagePolicy,
    detected_lang: str,
    preferred_lang: Optional[str] = None,
) -> str:
    """Return server-authoritative reply language code."""

    detected_lang = normalize_lang_code(detected_lang)
    if policy.use_global_language_system:
        # Auto-switch = detected language wins.
        return detected_lang

    # Manual mode: prefer explicitly set language, else detected if inside selected,
    # else fallback to first supported language.
    preferred = normalize_lang_code(preferred_lang) if preferred_lang else None
    supported = get_effective_supported_languages(policy)
    if preferred and (not supported or preferred in supported):
        return preferred
    if supported and detected_lang in supported:
        return detected_lang
    if supported:
        return supported[0]
    return get_default_language()


def format_reply_language_marker(lang_code: str) -> str:
    """Lightweight marker for UI/TTS without doing full translation."""
    lang_code = normalize_lang_code(lang_code)
    name = SUPPORTED_LANGUAGES.get(lang_code, {}).get("name", lang_code)
    return f"[{name}]"


