from __future__ import annotations

import re
from typing import Any, Dict, Optional


class CreativeEngine:
    """Creative writing, poetry, and dialogue engine for Nitro Infinity AI."""

    def __init__(self, storage_path: str = "") -> None:
        pass

    def generate(self, user_id: str, message: str, style: Optional[str] = None) -> Dict[str, Any]:
        low = (message or "").lower()

        if "joke" in low:
            reply = "Why do programmers prefer dark mode? Because light attracts bugs! 🐛"
        elif "riddle" in low:
            reply = "I speak without a mouth and hear without ears. I have no body, but I come alive with wind. What am I?\n\n*(Answer: An echo)*"
        elif "poem" in low:
            reply = (
                "Across the quiet digital expanse,\n"
                "Where circuits dream and photons dance,\n"
                "A spark of thought begins to rise,\n"
                "Connecting earth to boundless skies."
            )
        else:
            reply = (
                "The quiet room filled with a soft hum as the screen flickered to life. "
                "Every line of data represented a new journey waiting to unfold."
            )

        return {"reply": reply, "topic": "creative"}