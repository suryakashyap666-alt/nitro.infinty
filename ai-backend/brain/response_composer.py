from __future__ import annotations

from typing import Any, Dict, Optional


class ResponseComposer:
    """Composes clean, natural, and personality-aligned conversational responses.
    Avoids robotic bracketed tags or repetitive boilerplate.
    """

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
        clean_reply = (base_reply or "").strip()

        # 1. Safety Block Enforcement
        if risk_result.get("blocked"):
            return f"⚠️ {clean_reply}"

        # 2. Add subtle conversational tone adaptation without robotic bracket tags
        prefix = ""
        if strict:
            prefix = "Let's focus strictly on the steps:\n\n"
        elif emotion == "sad":
            prefix = ""
        elif emotion == "angry":
            prefix = ""

        # 3. Dynamic Teaching/Mistake feedback (applied smoothly)
        teaching_tail = ""
        if isinstance(learning_update, dict) and learning_update:
            if learning_update.get("mistake"):
                teaching_tail = f"\n\n*Note on this step:* Take a look at how the {topic} rule was applied here and see if you can spot the pivot point."
            elif learning_update.get("correct") and topic in {"algebra", "calculus", "coding"}:
                teaching_tail = "\n\nNicely done! Ready for the next one, or do you want to explore this further?"

        parts = []
        if prefix:
            parts.append(prefix)
        parts.append(clean_reply)
        if teaching_tail:
            parts.append(teaching_tail)

        return "".join(parts).strip()