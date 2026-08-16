from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class ChatRequest:
    user_id: str
    message: str
    guest_mode: bool = False
    bot_id: str | None = None
    detected_language: str | None = None  # auto-detected or user-specified


@dataclass
class ChatResponse:
    reply: str
    timestamp: str
    emotion: str
    topic: str
    detected_language: str = 'en'  # language of AI response


@dataclass
class HistoryResponse:
    chat_history: List[Dict[str, Any]]


@dataclass
class SaraswatiLoginRequest:
    account_id: str
    password: str


@dataclass
class SaraswatiLoginResponse:
    user_id: str
    display_name: str
    email: str = ''
    provider: str = 'saraswati'
    token: str = ''


@dataclass
class AuthVerifyResponse:
    user_id: str
    display_name: str
    email: str = ''
    provider: str = 'saraswati'
    token: str = ''
    valid: bool = True

