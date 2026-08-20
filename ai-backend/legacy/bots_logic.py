from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


def create_bot_reply(user_text: str, creator: str = "Nitro AI", conversation_state: Dict[str, Any] = None) -> Dict[str, Any]:
    state = conversation_state or {}
    text = (user_text or "").strip()

    if text.lower() == "the ai is now done":
        return {
            "reply": "Bot configuration finalized and saved to Marketplace.",
            "done": True,
            "botDraft": state,
        }

    return {
        "reply": f"Draft updated with instructions: '{text}'. When finished, say: 'The AI is now done'.",
        "done": False,
        "botDraft": state,
    }