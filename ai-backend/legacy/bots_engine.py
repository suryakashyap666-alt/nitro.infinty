from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class BotMarketplaceBot:
    name: str
    description: str
    skills: List[str]
    ratings: float
    creator: str
    category: str
    icon: str

    # Education system (education intelligence) - OFF by default for custom bots
    # MAIN Nitro Infinity AI (no bot_id) will always have it enabled.
    educationEnabled: bool = False

    # Multilingual global bot language system (default ON)
    useGlobalLanguageSystem: bool = True
    selectedLanguages: List[str] | None = None  # used only if global system disabled
    preferredLanguage: str | None = None  # bot-level preferred language (optional)
    voicePreferences: Dict[str, Any] | None = None

    # Live web intelligence support
    webSearchEnabled: bool = False
    allowedWebCategories: List[str] | None = None
    trustedSources: List[str] | None = None

    # Context understanding / conversation intelligence (OFF by default for custom bots)
    contextUnderstandingEnabled: bool = False
    userHistoryUnderstandingEnabled: bool = False
    webAssistanceEnabled: bool = False

    # Image generation / detection capabilities
    imageGenerationEnabled: bool = False
    imageDetectionEnabled: bool = False

    # Profession intelligence support for workplace and career guidance
    professionEnabled: bool = False
    professionCategories: List[str] | None = None
    workflowAssistanceEnabled: bool = False

    def to_dict(self) -> Dict[str, Any]:
        # Compute marketplace metadata for UI.
        # Voice support is browser-based; we can mark it as available if app runs in browser.
        # Backend always provides `voiceSupport: True` (frontend uses canUseVoice() for actual capability).
        from .language import SUPPORTED_LANGUAGES

        if self.useGlobalLanguageSystem:
            supported = [k for k, v in SUPPORTED_LANGUAGES.items() if v.get("enabled", True)]
            auto_detect = True
        else:
            supported = list(self.selectedLanguages or [])
            auto_detect = False

        return {
            "name": self.name,
            "description": self.description,
            "skills": self.skills,
            "ratings": self.ratings,
            "creator": self.creator,
            "category": self.category,
            "icon": self.icon,

            # Language system settings
            "useGlobalLanguageSystem": bool(self.useGlobalLanguageSystem),
            "selectedLanguages": list(self.selectedLanguages or []),
            "preferredLanguage": self.preferredLanguage,
            "voicePreferences": self.voicePreferences or {},

            # Marketplace display fields
            "supportedLanguages": supported,
            "voiceSupport": True,
            "autoDetectLanguage": auto_detect,

            # Education system
            "educationEnabled": bool(self.educationEnabled),
            # Live web intelligence system
            "webSearchEnabled": bool(self.webSearchEnabled),
            "allowedWebCategories": list(self.allowedWebCategories or []),
            "trustedSources": list(self.trustedSources or []),
            # Image generation/detection policy flags
            "imageGenerationEnabled": bool(self.imageGenerationEnabled),
            "imageDetectionEnabled": bool(self.imageDetectionEnabled),
            # Profession intelligence system
            "professionEnabled": bool(self.professionEnabled),
            "professionCategories": list(self.professionCategories or []),
            "workflowAssistanceEnabled": bool(self.workflowAssistanceEnabled),
            # Context intelligence flags
            "contextUnderstandingEnabled": bool(self.contextUnderstandingEnabled),
            "userHistoryUnderstandingEnabled": bool(self.userHistoryUnderstandingEnabled),
            "webAssistanceEnabled": bool(self.webAssistanceEnabled),
        }





class BotMarketplaceEngine:
    """Persists marketplace bots inside existing nitro_state.json under a top-level `bots` key."""

    def __init__(self, storage_path: str) -> None:
        self.storage_path = storage_path
        self._ensure_storage()

    def _ensure_storage(self) -> None:
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        if not os.path.exists(self.storage_path):
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump({"users": {}, "bots": {}}, f, ensure_ascii=False, indent=2)

    def _load(self) -> Dict[str, Any]:
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"users": {}, "bots": {}}

    def _save(self, data: Dict[str, Any]) -> None:
        tmp = self.storage_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.storage_path)

    def _get_bots_container(self, data: Dict[str, Any]) -> Dict[str, Any]:
        bots = data.setdefault("bots", {})
        if not isinstance(bots, dict):
            data["bots"] = {}
            bots = data["bots"]
        return bots

    def ensure_default_bots(self) -> None:
        data = self._load()
        bots = self._get_bots_container(data)

        if "math_tutor" not in bots:
            bots["math_tutor"] = BotMarketplaceBot(
                name="Math Tutor",
                description=(
                    "Advanced math solving with emotional, step-by-step teaching. "
                    "Generates practice papers and question sets, supports IIT/CBSE teaching, "
                    "improves weak topics, and advises while solving."
                ),
                skills=[
                    "advanced math solving",
                    "reasoning",
                    "emotional support while teaching",
                    "step-by-step teaching",
                    "practice paper generation",
                    "question generation",
                    "IIT/CBSE teaching",
                    "weak topic improvement",
                    "advising/helping",
                ],
                ratings=4.8,
                creator="Nitro Infinity AI",
                category="math tutor",
                icon="🧮",
            ).to_dict()

        self._save(data)

    def list_bots(self) -> List[Dict[str, Any]]:
        data = self._load()
        bots = self._get_bots_container(data)
        return [bots[k] for k in bots.keys()]

    def get_bot(self, bot_id: str) -> Dict[str, Any]:
        data = self._load()
        bots = self._get_bots_container(data)
        bot = bots.get(bot_id)
        return bot if isinstance(bot, dict) else {}

    def add_bot(self, bot_id: str, bot: BotMarketplaceBot) -> None:
        data = self._load()
        bots = self._get_bots_container(data)
        bots[bot_id] = bot.to_dict()
        self._save(data)


def bot_market_tags(bot: Dict[str, Any]) -> List[str]:
    text = " ".join(
        [
            str(bot.get("name", "")),
            str(bot.get("description", "")),
            " ".join(bot.get("skills", []) or []),
            str(bot.get("category", "")),
        ]
    ).lower()

    # simple synonym expansion
    synonyms = {
        "coding": ["coding", "code", "programming", "developer"],
        "math": ["math", "algebra", "geometry", "calculus", "iIt", "cbse"],
        "tutor": ["tutor", "teacher", "mentoring", "coach"],
        "emotional": ["emotional", "support", "coach", "encourag"],
        "reasoning": ["reasoning", "logic", "explain", "step-by-step"],
        "exam": ["exam", "iIt", "cbse", "paper", "question generation"],
    }

    tags = set()
    for tag, needles in synonyms.items():
        for n in needles:
            if n in text:
                tags.add(tag)
                break

    # fallback category
    if not tags:
        cat = str(bot.get("category", "")).lower().strip()
        if cat:
            tags.add(cat)

    return sorted(tags)


def filter_bots(bots: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
    q = (query or "").strip().lower()
    if not q:
        return bots

    # allow direct tags in search (math/coding/tutor/emotional/reasoning/exam)
    allowed_tags = ["math", "coding", "tutor", "emotional", "reasoning", "exam"]
    q_has_tag = any(t in q for t in allowed_tags)

    filtered: List[Dict[str, Any]] = []
    for b in bots:
        blob = " ".join(
            [
                str(b.get("name", "")),
                str(b.get("description", "")),
                " ".join(b.get("skills", []) or []),
                str(b.get("category", "")),
            ]
        ).lower()

        if q_has_tag:
            tags = set(bot_market_tags(b))
            if any(tag in q for tag in allowed_tags) and any(tag in tags for tag in allowed_tags):
                filtered.append(b)
        else:
            # generic substring match
            if q in blob:
                filtered.append(b)

    # stable-ish sort: highest ratings first
    def rating_val(x: Dict[str, Any]) -> float:
        try:
            return float(x.get("ratings", 0))
        except Exception:
            return 0.0

    filtered.sort(key=rating_val, reverse=True)
    return filtered

