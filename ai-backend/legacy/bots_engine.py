from __future__ import annotations

import json
import os
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

    educationEnabled: bool = False
    useGlobalLanguageSystem: bool = True
    selectedLanguages: List[str] | None = None
    preferredLanguage: str | None = None
    voicePreferences: Dict[str, Any] | None = None
    webSearchEnabled: bool = False
    allowedWebCategories: List[str] | None = None
    trustedSources: List[str] | None = None
    contextUnderstandingEnabled: bool = False
    userHistoryUnderstandingEnabled: bool = False
    webAssistanceEnabled: bool = False
    imageGenerationEnabled: bool = True
    imageDetectionEnabled: bool = True
    professionEnabled: bool = False
    professionCategories: List[str] | None = None
    workflowAssistanceEnabled: bool = False

    def to_dict(self) -> Dict[str, Any]:
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
            "useGlobalLanguageSystem": bool(self.useGlobalLanguageSystem),
            "selectedLanguages": list(self.selectedLanguages or []),
            "preferredLanguage": self.preferredLanguage,
            "voicePreferences": self.voicePreferences or {},
            "supportedLanguages": supported,
            "voiceSupport": True,
            "autoDetectLanguage": auto_detect,
            "educationEnabled": bool(self.educationEnabled),
            "webSearchEnabled": bool(self.webSearchEnabled),
            "allowedWebCategories": list(self.allowedWebCategories or []),
            "trustedSources": list(self.trustedSources or []),
            "imageGenerationEnabled": bool(self.imageGenerationEnabled),
            "imageDetectionEnabled": bool(self.imageDetectionEnabled),
            "professionEnabled": bool(self.professionEnabled),
            "professionCategories": list(self.professionCategories or []),
            "workflowAssistanceEnabled": bool(self.workflowAssistanceEnabled),
            "contextUnderstandingEnabled": bool(self.contextUnderstandingEnabled),
            "userHistoryUnderstandingEnabled": bool(self.userHistoryUnderstandingEnabled),
            "webAssistanceEnabled": bool(self.webAssistanceEnabled),
        }


class BotMarketplaceEngine:
    """Persists marketplace bots inside nitro_state.json under a top-level `bots` key."""

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
                description="Step-by-step math and calculus problem solving with educational coaching.",
                skills=[
                    "algebra",
                    "calculus",
                    "step-by-step solving",
                    "practice question generation",
                    "weak topic improvement",
                ],
                ratings=4.9,
                creator="Nitro Infinity AI",
                category="math tutor",
                icon="🧮",
                educationEnabled=True,
            ).to_dict()

        if "code_architect" not in bots:
            bots["code_architect"] = BotMarketplaceBot(
                name="Code Architect",
                description="Python, React, and FastAPI coding assistant with debugging and code generation.",
                skills=[
                    "python",
                    "fastapi",
                    "react",
                    "debugging",
                    "code generation",
                ],
                ratings=4.8,
                creator="Nitro Infinity AI",
                category="coding",
                icon="💻",
                workflowAssistanceEnabled=True,
            ).to_dict()

        self._save(data)

    def list_bots(self) -> List[Dict[str, Any]]:
        data = self._load()
        bots = self._get_bots_container(data)
        return list(bots.values())

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


def filter_bots(bots: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
    q = (query or "").strip().lower()
    if not q:
        return bots

    filtered: List[Dict[str, Any]] = []
    for b in bots:
        blob = " ".join([
            str(b.get("name", "")),
            str(b.get("description", "")),
            " ".join(b.get("skills", []) or []),
            str(b.get("category", "")),
        ]).lower()

        if q in blob:
            filtered.append(b)

    return filtered