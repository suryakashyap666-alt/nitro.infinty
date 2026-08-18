"""
ai-backend/engines/router.py

Strict, native Nitro AI Engine Router.
All chat completions, agent queries, and tools route exclusively through Nitro AI.
External third-party providers (OpenAI, Claude, Groq, Qwen, etc.) are excluded.
"""
from __future__ import annotations

import json
import os
import uuid
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional


class EngineError(Exception):
    """Raised for any Nitro engine-level error."""
    def __init__(self, message: str, *, status_code: int = 500) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class BaseEngine(ABC):
    provider_id: str = "nitro"

    @abstractmethod
    def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        api_key: Optional[str] = None,
        bot_id: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        raise NotImplementedError


def _sse_chunk(piece: str) -> str:
    payload = {
        "id": f"nitro-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion.chunk",
        "choices": [{"index": 0, "delta": {"content": piece}, "finish_reason": None}],
    }
    return f"data: {json.dumps(payload)}\n\n"


class NitroNativeEngine(BaseEngine):
    """Direct streaming adapter for Nitro Infinity AI Brain Core."""
    provider_id = "nitro"

    def __init__(self) -> None:
        pass

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "nitro-v1",
        api_key: Optional[str] = None,
        bot_id: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        # Validate Nitro API Key if NITRO_API_KEY environment variable is enforced
        required_key = os.environ.get("NITRO_API_KEY")
        if required_key and api_key != required_key:
            raise EngineError("Invalid or missing Nitro API Key.", status_code=401)

        # Extract latest user message
        last_message = ""
        for m in reversed(messages):
            if m.get("role") == "user" and m.get("content"):
                last_message = str(m["content"])
                break

        if not last_message:
            raise EngineError("No user message content provided.", status_code=400)

        # Lazy import of CoreBrain to prevent circular imports
        from brain.core import CoreBrain
        from legacy.bots_engine import BotMarketplaceEngine

        base_dir = os.path.dirname(os.path.dirname(__file__))
        data_dir = os.environ.get("NITRO_DATA_DIR") or os.path.join(base_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        storage_path = os.path.join(data_dir, "nitro_state.json")

        bot_market = BotMarketplaceEngine(storage_path=storage_path)
        brain = CoreBrain(storage_path=storage_path, bot_market=bot_market)

        user_id = f"api_user_{uuid.uuid4().hex[:8]}"

        result = brain.handle_message(
            user_id=user_id,
            message=last_message,
            persist_chat=True,
            bot_id=bot_id,
            conversation_context=messages,
            api_key=api_key,
            model=model,
        )

        reply_text = result.get("reply", "") if isinstance(result, dict) else str(result)
        if not reply_text:
            reply_text = "Nitro AI has processed your request."

        # Check if an image was generated
        if isinstance(result, dict) and result.get("imageAction"):
            img_action = result.get("imageAction", {})
            img_payload = {
                "type": "image",
                "task": "image_generation",
                "image_data": img_action.get("image", {}).get("data_url"),
                "prompt": img_action.get("prompt"),
                "style": img_action.get("style"),
                "quality": img_action.get("quality"),
            }
            yield f"data: {json.dumps(img_payload)}\n\n"
            return

        # Stream text response tokens
        words = reply_text.split(" ")
        for i, word in enumerate(words):
            piece = word if i == len(words) - 1 else f"{word} "
            yield _sse_chunk(piece)


def resolve_engine(provider_id: str = "nitro") -> BaseEngine:
    """Always resolves to the native Nitro AI Engine."""
    return NitroNativeEngine()