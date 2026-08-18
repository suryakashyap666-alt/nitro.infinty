"""
ai-backend/engines/nitro_brain_engine.py

Asynchronous CoreBrain engine connector.
"""
from __future__ import annotations

import asyncio
import json
import os
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional

from .router import BaseEngine, EngineError

_BRAIN_INSTANCE: Optional[Any] = None


def _get_brain() -> Any:
    global _BRAIN_INSTANCE
    if _BRAIN_INSTANCE is not None:
        return _BRAIN_INSTANCE

    from brain.core import CoreBrain
    from legacy.bots_engine import BotMarketplaceEngine

    data_dir = os.environ.get("NITRO_DATA_DIR")
    if data_dir:
        data_dir = os.path.abspath(data_dir)
    else:
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    os.makedirs(data_dir, exist_ok=True)

    storage_path = os.path.join(data_dir, "nitro_state.json")
    bot_market = BotMarketplaceEngine(storage_path=storage_path)
    _BRAIN_INSTANCE = CoreBrain(storage_path=storage_path, bot_market=bot_market)
    return _BRAIN_INSTANCE


def _sse_delta_chunk(text_piece: str) -> str:
    payload = {
        "id": f"nitro-brain-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion.chunk",
        "choices": [{"index": 0, "delta": {"content": text_piece}, "finish_reason": None}],
    }
    return f"data: {json.dumps(payload)}\n\n"


class NitroBrainEngine(BaseEngine):
    provider_id = "nitro-brain"

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "nitro-brain-v1",
        api_key: Optional[str] = None,
        bot_id: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        last_message = ""
        for m in reversed(messages):
            if m.get("role") == "user" and m.get("content"):
                last_message = str(m["content"])
                break

        if not last_message.strip():
            raise EngineError("No user message content provided.", status_code=400)

        brain = _get_brain()
        guest_user_id = f"guest_{uuid.uuid4().hex[:10]}"

        try:
            result = await asyncio.to_thread(
                brain.handle_message,
                user_id=guest_user_id,
                message=last_message,
                persist_chat=True,
                bot_id=bot_id,
                incoming_language=None,
                conversation_context=messages,
                api_key=api_key,
                model=model,
            )
        except Exception as exc:
            raise EngineError(f"Nitro brain engine execution failed: {exc}", status_code=500) from exc

        reply_text = ""
        if isinstance(result, dict):
            if result.get("imageAction"):
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
            reply_text = str(result.get("reply") or "")
        else:
            reply_text = str(result or "")

        words = reply_text.split(" ")
        for index, word in enumerate(words):
            piece = word if index == len(words) - 1 else f"{word} "
            yield _sse_delta_chunk(piece)