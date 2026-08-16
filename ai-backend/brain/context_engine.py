from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from .memory import MemoryEngine
from .topic_detector import TopicDetector


class ContextEngine:
    """Lightweight context understanding engine.

    Responsibilities:
    - Resolve pronouns and simple references using recent chat history
    - Detect intent completeness and suggest clarifications when confidence is low
    - Expose a small API used by CoreBrain to enrich messages
    This is intentionally simple and rule-based to keep it lightweight and safe.
    """

    def __init__(self, storage_path: str) -> None:
        self.memory = MemoryEngine(storage_path=storage_path)
        self.topic_detector = TopicDetector()

    def _last_user_messages(self, user_id: str, limit: int = 6) -> List[Dict[str, Any]]:
        state = self.memory.load_user_state(user_id)
        hist = state.get("chat_history") or []
        return list(hist[-limit:])

    def _resolve_pronoun(self, user_id: str, message: str) -> (str, Dict[str, str]):
        # Very small heuristic: if message uses 'it', 'they', 'that', attempt to find
        # the most recent noun phrase from prior user messages or bot replies.
        lowered = message.lower()
        pronouns = [" it ", " it?", " they ", " them ", " that ", " those ", " this "]
        resolved: Dict[str, str] = {}
        if not any(p in lowered for p in pronouns):
            return message, resolved

        recent = self._last_user_messages(user_id, limit=8)
        # gather candidate noun tokens from recent conversation (messages and replies)
        candidates: List[str] = []
        for ev in reversed(recent):
            for side in ("message", "reply"):
                txt = ev.get(side) or ""
                # crude noun extraction: pick longer words sequences excluding stopwords
                tokens = re.findall(r"[A-Za-z0-9_\-]{3,}", txt)
                for t in reversed(tokens[-6:]):
                    if len(t) > 2 and t.lower() not in ("the", "this", "that", "it", "they", "them", "a", "an", "and", "or"):
                        candidates.append(t)
        if not candidates:
            return message, resolved

        top = candidates[0]
        # Replace simple pronouns with top candidate (best-effort)
        new_msg = re.sub(r"\bit\b", top, message, flags=re.I)
        new_msg = re.sub(r"\bthey\b", top, new_msg, flags=re.I)
        new_msg = re.sub(r"\bthem\b", top, new_msg, flags=re.I)
        resolved_map = {"it": top}
        return new_msg, resolved_map

    def _detect_incomplete(self, message: str) -> (bool, Optional[List[str]]):
        # Heuristics for incomplete/ambiguous questions
        msg = (message or "").strip()
        if not msg:
            return True, None
        # If message is just a short pronoun or single-word question
        if len(msg.split()) <= 3 and ("?" in msg or msg.endswith("?")):
            return False, None
        # If message looks like a follow-up with pronouns only
        if re.match(r"^(it|that|this|they|them)[\.,!?\s]*$", msg.lower()):
            return True, None
        # If message contains a vague referent like 'How much RAM does it need' without previous referent
        if re.search(r"\b(it|that|this|they)\b", msg, flags=re.I) and len(msg.split()) <= 10:
            return True, None
        return False, None

    def analyze_message(self, user_id: str, message: str, bot_id: Optional[str] = None, use_saved_history: bool = True, use_user_prefs: bool = True) -> Dict[str, Any]:
        """Return analysis with keys:
        - resolved_message: possibly rewritten message with resolved references
        - confidence: float 0..1
        - intent: simple label
        - possible_meanings: list[str]
        - clarification: optional suggested clarifying question when confidence is low
        - resolved_references: mapping pronoun->referent
        """
        out: Dict[str, Any] = {
            "resolved_message": message,
            "confidence": 1.0,
            "intent": None,
            "possible_meanings": [],
            "clarification": None,
            "resolved_references": {},
        }

        # Guest users: avoid long-term memory by default
        is_guest = isinstance(user_id, str) and user_id.startswith("guest_")
        history_allowed = use_saved_history and (not is_guest)

        # Quick topic detection
        try:
            intent = self.topic_detector.detect_topic(message)
            out["intent"] = intent
        except Exception:
            out["intent"] = "general"

        # Resolve pronouns using recent history if allowed
        try:
            if history_allowed:
                resolved_msg, resolved_map = self._resolve_pronoun(user_id, message)
                out["resolved_message"] = resolved_msg
                out["resolved_references"] = resolved_map
            else:
                out["resolved_message"] = message
        except Exception:
            out["resolved_message"] = message

        # Detect incompleteness
        incomplete, _ = self._detect_incomplete(message)
        if incomplete:
            out["confidence"] = 0.25
            # produce a small clarification prompt when low confidence
            out["possible_meanings"] = ["referent_missing", "ambiguous_intent"]
            out["clarification"] = "I see two possible meanings. Did you mean the previous topic, or something new?"

        return out
