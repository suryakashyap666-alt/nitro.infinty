from __future__ import annotations

import json
import os
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from time import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Firebase Firestore and Realtime Database optional imports
try:
    import firebase_admin
    from firebase_admin import firestore, db as rtdb
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False


@dataclass
class ChatMemoryEvent:
    message: str
    reply: str
    emotion: str
    topic: str
    ts: str


class MemoryEngine:
    """Persists chat history, mistakes, weak topics, and bot configurations per user.
    Synchronizes automatically with Firebase Firestore / Realtime DB when configured,
    with robust local JSON fallback.
    """

    def __init__(self, storage_path: str) -> None:
        self.storage_path = storage_path
        self._firestore_client = None
        self._init_firebase()
        self._ensure_storage()

    def _init_firebase(self) -> None:
        if FIREBASE_AVAILABLE:
            try:
                if firebase_admin._apps:
                    self._firestore_client = firestore.client()
            except Exception as e:
                logger.debug("Firestore client initialization bypassed: %s", e)

    def _ensure_storage(self) -> None:
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        if not os.path.exists(self.storage_path):
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump({"users": {}, "bots": {}, "web_cache": {}}, f)

    def _load(self) -> Dict[str, Any]:
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"users": {}, "bots": {}, "web_cache": {}}

    def _save(self, data: Dict[str, Any]) -> None:
        tmp = self.storage_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.storage_path)

    def _utc(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _is_guest(self, user_id: str) -> bool:
        return isinstance(user_id, str) and user_id.startswith("guest_")

    def _sync_to_firestore(self, user_id: str, u_state: Dict[str, Any]) -> None:
        if self._firestore_client and not self._is_guest(user_id):
            try:
                doc_ref = self._firestore_client.collection("nitro_users").document(user_id)
                doc_ref.set(u_state, merge=True)
            except Exception as e:
                logger.debug("Firestore sync error: %s", e)

    def _record_image_feedback(self, image_key: str, feedback: str) -> None:
        if not image_key or feedback not in ["like", "dislike"]:
            return
        data = self._load()
        data.setdefault("image_feedback", {})
        fb = data["image_feedback"]
        fb.setdefault(image_key, {"likes": 0, "dislikes": 0})
        if feedback == "like":
            fb[image_key]["likes"] += 1
        else:
            fb[image_key]["dislikes"] += 1
        self._save(data)

    def get_image_feedback(self, image_key: str) -> Dict[str, int]:
        data = self._load()
        fb = data.get("image_feedback", {})
        return fb.get(image_key, {"likes": 0, "dislikes": 0})

    def get_all_image_feedback(self) -> Dict[str, Dict[str, int]]:
        data = self._load()
        return data.get("image_feedback", {})

    def load_user_state(self, user_id: str) -> Dict[str, Any]:
        data = self._load()
        users = data.setdefault("users", {})
        u = users.setdefault(user_id, {})

        u.setdefault("chat_history", [])
        u.setdefault("mistakes", [])
        u.setdefault("weak_topics", {})
        u.setdefault("coding_history", [])
        u.setdefault("preferred_language", "en")
        u.setdefault("language_history", [])
        u.setdefault("voice_preferences", {"enabled": True, "voice_language": None})
        u.setdefault("profile", {})
        u.setdefault("bot_languages", {})
        u.setdefault("bot_voice_preferences", {})
        u.setdefault("profession", {"name": None, "level": "beginner"})
        u.setdefault("profession_interests", [])
        u.setdefault("profession_workflows", [])
        u.setdefault("profession_tools", [])
        u.setdefault("profession_learning", {})
        u.setdefault("favorites", [])
        u.setdefault("preferred_sources", [])
        u.setdefault("search_history", [])
        u.setdefault("learning_interests", [])
        u.setdefault("image_history", [])
        u.setdefault("bot_image", {})

        return u

    def append_message(self, user_id: str, message: str, reply: str, emotion: str, topic: str) -> None:
        if self._is_guest(user_id):
            return
        data = self._load()
        users = data.setdefault("users", {})
        u = users.setdefault(user_id, {})
        u.setdefault("chat_history", [])
        entry = {
            "message": message,
            "reply": reply,
            "emotion": emotion,
            "topic": topic,
            "ts": self._utc(),
        }
        u["chat_history"].append(entry)
        self._save(data)
        self._sync_to_firestore(user_id, u)

    def append_image_history(self, user_id: str, image_action: Dict[str, Any], max_len: int = 200) -> None:
        if self._is_guest(user_id) or not image_action:
            return
        data = self._load()
        users = data.setdefault("users", {})
        u = users.setdefault(user_id, {})
        u.setdefault("image_history", [])
        hist = u.get("image_history") or []
        hist.append({"action": image_action, "ts": self._utc()})
        u["image_history"] = hist[-max_len:]
        self._save(data)
        self._sync_to_firestore(user_id, u)

    def get_image_history(self, user_id: str, max_len: int = 200) -> List[Dict[str, Any]]:
        u = self.load_user_state(user_id)
        return list((u.get("image_history") or [])[-max_len:])

    def record_mistake(self, user_id: str, result: Dict[str, Any]) -> None:
        if self._is_guest(user_id):
            return
        data = self._load()
        users = data.setdefault("users", {})
        u = users.setdefault(user_id, {})
        u.setdefault("mistakes", [])
        u["mistakes"].append({
            "topic": result.get("topic", "general"),
            "ts": self._utc(),
            "detail": result,
        })
        self._save(data)
        self._sync_to_firestore(user_id, u)

    def load_bot_language_policy(self, user_id: str, bot_id: str) -> Dict[str, Any]:
        u = self.load_user_state(user_id)
        bot_languages = u.get("bot_languages") or {}
        return bot_languages.get(bot_id) or {"useGlobalLanguageSystem": True}

    def load_bot_preferred_language(self, user_id: str, bot_id: str) -> str | None:
        u = self.load_user_state(user_id)
        bot_languages = u.get("bot_languages") or {}
        bot = bot_languages.get(bot_id) or {}
        return bot.get("preferredLanguage")

    def load_bot_education_policy(self, user_id: str, bot_id: str) -> Dict[str, Any]:
        u = self.load_user_state(user_id)
        edu = u.get("bot_education") or {}
        return edu.get(bot_id) or {"educationEnabled": False}

    def load_bot_web_policy(self, user_id: str, bot_id: str) -> Dict[str, Any]:
        u = self.load_user_state(user_id)
        web = u.get("bot_web") or {}
        return web.get(bot_id) or {"webSearchEnabled": False, "allowedWebCategories": [], "trustedSources": []}

    def load_bot_image_policy(self, user_id: str, bot_id: str) -> Dict[str, Any]:
        u = self.load_user_state(user_id)
        img = u.get("bot_image") or {}
        return img.get(bot_id) or {"imageGenerationEnabled": True, "imageDetectionEnabled": True}

    def set_bot_image_policy(self, user_id: str, bot_id: str, policy_state: Dict[str, Any]) -> None:
        if self._is_guest(user_id):
            return
        data = self._load()
        users = data.setdefault("users", {})
        u = users.setdefault(user_id, {})
        u.setdefault("bot_image", {})
        u["bot_image"][bot_id] = policy_state
        self._save(data)
        self._sync_to_firestore(user_id, u)

    def load_bot_profession_policy(self, user_id: str, bot_id: str) -> Dict[str, Any]:
        u = self.load_user_state(user_id)
        prof = u.get("bot_profession") or {}
        return prof.get(bot_id) or {"professionEnabled": False}

    def load_bot_context_policy(self, user_id: str, bot_id: str) -> Dict[str, Any]:
        u = self.load_user_state(user_id)
        ctx = u.get("bot_context") or {}
        return ctx.get(bot_id) or {
            "contextUnderstandingEnabled": False,
            "useUserHistoryUnderstanding": False,
            "useWebAssistance": False,
        }

    def append_language_history(self, user_id: str, lang_code: str, max_len: int = 20) -> None:
        if self._is_guest(user_id):
            return
        data = self._load()
        users = data.setdefault("users", {})
        u = users.setdefault(user_id, {})
        u.setdefault("language_history", [])
        hist = u.get("language_history") or []
        if not hist or hist[-1] != lang_code:
            hist.append(lang_code)
        u["language_history"] = hist[-max_len:]
        self._save(data)