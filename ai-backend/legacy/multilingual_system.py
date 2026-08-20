from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from .multilingual import normalize_lang_code, SUPPORTED_LANGUAGES


@dataclass
class BotLanguagePolicy:
    use_global_language_system: bool = True
    selected_languages: Optional[List[str]] = None

    @staticmethod
    def from_state(state: Dict[str, Any] | None) -> BotLanguagePolicy:
        s = state or {}
        use_global = bool(s.get("useGlobalLanguageSystem", True))
        langs = s.get("selectedLanguages") or None
        return BotLanguagePolicy(use_global_language_system=use_global, selected_languages=langs)