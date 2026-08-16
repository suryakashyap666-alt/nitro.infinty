from __future__ import annotations

from typing import Any, Dict, Optional


class ResponseComposer:
    """Compose final response using emotion, safety, context, and base reply."""

    def compose(
        self,
        user_id: str,
        emotion: str,
        topic: str,
        risk_result: Dict[str, Any],
        base_reply: str,
        learning_update: Any,
        chat_mode: Dict[str, bool],
        include_nudges: bool = False,
    ) -> str:
        strict = bool(chat_mode.get("strict"))
        friendly = bool(chat_mode.get("friendly"))
        fast = bool(chat_mode.get("fast"))
        best = bool(chat_mode.get("best"))

        # Voice permission system notice
        voice_line = ""
        if chat_mode.get("voice_request") and not chat_mode.get("voice_allowed"):
            voice_line = "Please allow microphone permission to use voice features."

        # Safety prefix
        safety_prefix = ""
        if risk_result.get("blocked"):
            safety_prefix = "[Safety] "

        # Emotion prefix (only applied when relevant or in strict mode)
        emotion_prefix = self._emotion_prefix(emotion, strict=strict, friendly=friendly) if (strict or emotion != "neutral") else ""

        # Teaching reinforcement for explicit educational / mistake actions
        teaching_tail = ""
        if isinstance(learning_update, dict) and learning_update:
            if learning_update.get("mistake"):
                teaching_tail = self._teach_after_mistake(topic, emotion)
            elif learning_update.get("correct"):
                teaching_tail = self._teach_after_success(topic, emotion)
        elif include_nudges and not strict and topic in {"algebra", "geometry", "calculus", "coding", "exam"}:
            teaching_tail = self._general_nudge(topic, emotion)

        # Fast/best formatting
        if fast and not best and teaching_tail:
            teaching_tail = "\n" + teaching_tail.splitlines()[0]

        parts = []
        lead = f"{safety_prefix}{emotion_prefix}".strip()
        if lead:
            parts.append(f"{lead} {base_reply}".strip())
        else:
            parts.append(base_reply.strip())

        if voice_line:
            parts.append(voice_line)
        if teaching_tail:
            parts.append(teaching_tail)

        return "\n\n".join(parts).strip()

    def _emotion_prefix(self, emotion: str, strict: bool, friendly: bool) -> str:
        if strict:
            return "[Strict Teacher]"
        if friendly:
            if emotion == "sad":
                return "[Warm Coach]"
            if emotion == "angry":
                return "[Calm Mentor]"
            return ""
        if emotion == "happy":
            return "[Supportive Tutor]"
        if emotion == "sad":
            return "[Empathetic Tutor]"
        if emotion == "angry":
            return "[Calm Mentor]"
        return ""

    def _teach_after_mistake(self, topic: str, emotion: str) -> str:
        if emotion == "angry":
            return "Let’s slow down. Paste your last step and I’ll pinpoint the mismatch."
        return f"Tip: identify the first step where your reasoning diverges, then we'll review the {topic} rule."

    def _teach_after_success(self, topic: str, emotion: str) -> str:
        if emotion == "happy":
            return f"Great job! Ready for the next problem in {topic}?"
        return f"Correct. We can continue with more practice in {topic}."

    def _general_nudge(self, topic: str, emotion: str) -> str:
        if emotion == "sad":
            return f"Whenever you are ready, share your work and we'll go step-by-step through {topic}."
        return f"Share your attempt if you'd like targeted feedback on {topic}."