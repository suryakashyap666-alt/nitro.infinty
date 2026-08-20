from __future__ import annotations

import re


class EmotionEngine:
    """Detects and tracks sentiment and emotional context."""

    def __init__(self, storage_path: str = "") -> None:
        pass

    def detect_and_update(self, user_id: str, message: str) -> str:
        low = (message or "").lower()
        if any(k in low for k in ["happy", "great", "awesome", "love", "yay", "amazing"]):
            return "happy"
        if any(k in low for k in ["sad", "unhappy", "depressed", "tired", "hopeless"]):
            return "sad"
        if any(k in low for k in ["angry", "hate", "mad", "furious", "annoyed"]):
            return "angry"
        return "neutral"