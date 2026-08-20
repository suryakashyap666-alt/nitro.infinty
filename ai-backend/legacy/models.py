from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ChatRequest:
    user_id: str
    message: str
    guest_mode: bool = False
    bot_id: str | None = None
    detected_language: str | None = None


@dataclass
class ChatResponse:
    reply: str
    timestamp: str
    emotion: str
    topic: str
    detected_language: str = "en"