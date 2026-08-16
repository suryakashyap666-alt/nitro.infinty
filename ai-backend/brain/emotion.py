from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, asdict
from typing import Any, Dict


@dataclass
class UserEmotionState:
    emotion: str = "neutral"  # happy|sad|angry|neutral
    last_signal: str = ""


class EmotionEngine:
    """Keeps per-user emotion state persisted to storage_path."""

    def __init__(self, storage_path: str) -> None:
        self.storage_path = storage_path
        self._ensure_storage()

        self._patterns = {
            "happy": [
                r"\b(happy|great|awesome|amazing|good job|nice|love|fantastic|yay|wonderful)\b",
                r"\b(congrats|congratulations)\b",
            ],
            "sad": [
                r"\b(sad|down|depressed|unhappy|sorry|regret|cry|tired|hopeless)\b",
                r"\b(i can’t|i cant|i cannot)\b",
            ],
            "angry": [
                r"\b(angry|mad|furious|hate|annoyed|rage|worse|stupid|idiot)\b",
                r"\b(what\s+the\s+hell|ridiculous)\b",
            ],
        }

    def _ensure_storage(self) -> None:
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        if not os.path.exists(self.storage_path):
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump({"users": {}}, f)

    def _load(self) -> Dict[str, Any]:
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"users": {}}

    def _save(self, data: Dict[str, Any]) -> None:
        tmp = self.storage_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.storage_path)

    def get_or_init_user(self, user_id: str) -> UserEmotionState:
        data = self._load()
        users = data.setdefault("users", {})
        u = users.setdefault(user_id, {})
        emotion = u.get("emotion")
        if not emotion:
            u["emotion"] = asdict(UserEmotionState())
        return UserEmotionState(**u["emotion"])

    def detect_and_update(self, user_id: str, message: str) -> str:
        state = self.get_or_init_user(user_id)
        msg = message.lower().strip()

        detected = "neutral"
        best_score = 0
        best_signal = ""

        # scoring: count matched keywords per emotion bucket
        for emotion, patterns in self._patterns.items():
            score = 0
            for p in patterns:
                if re.search(p, msg, flags=re.IGNORECASE):
                    score += 1
            if score > best_score:
                best_score = score
                detected = emotion

        # Update only if a signal is present; otherwise keep last emotion.
        if best_score > 0:
            state.emotion = detected
            # keep last matched signal roughly
            best_signal = detected
        
        data = self._load()
        users = data.setdefault("users", {})
        users.setdefault(user_id, {})["emotion"] = asdict(state)
        self._save(data)
        return state.emotion

