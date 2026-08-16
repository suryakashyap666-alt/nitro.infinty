"""
ai-backend/engines/nitro_brain_engine.py

Adapter exposing the Nitro Infinity AI brain (CoreBrain) as a selectable BaseEngine.
Passes full conversation history and parameters to CoreBrain for dynamic reasoning.
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

    try:
        from brain.core import CoreBrain
    except ImportError as exc:
        raise EngineError(
            "Nitro brain engine is unavailable: could not import brain.core.CoreBrain. "
            "Ensure ai-backend/ is on PYTHONPATH.",
            status_code=500,
        ) from exc

    data_dir = os.environ.get("NITRO_DATA_DIR")
    if data_dir:
        data_dir = os.path.abspath(data_dir)
    else:
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    os.makedirs(data_dir, exist_ok=True)

    storage_path = os.path.join(data_dir, "nitro_state.json")
    _BRAIN_INSTANCE = CoreBrain(storage_path=storage_path, bot_market=None)
    return _BRAIN_INSTANCE


def _last_user_message(messages: List[Dict[str, str]]) -> str:
    for entry in reversed(messages):
        if entry.get("role") == "user" and entry.get("content"):
            return str(entry["content"])
    if messages:
        return str(messages[-1].get("content") or "")
    return ""


def _sse_delta_chunk(text_piece: str) -> str:
    payload = {
        "id": f"nitro-brain-{uuid.uuid4().hex}",
        "object": "chat.completion.chunk",
        "choices": [{"index": 0, "delta": {"content": text_piece}, "finish_reason": None}],
    }
    return f"data: {json.dumps(payload)}\n\n"


class NitroBrainEngine(BaseEngine):
    """
    Routes chat requests through CoreBrain with full conversation history.
    """

    provider_id = "nitro-brain"

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        api_key: Optional[str],
    ) -> AsyncGenerator[str, None]:
        user_text = _last_user_message(messages)
        if not user_text.strip():
            raise EngineError("No user message content provided.", status_code=400)

        brain = _get_brain()
        guest_user_id = f"guest_{uuid.uuid4().hex}"

        try:
            result = await asyncio.to_thread(
                brain.handle_message,
                user_id=guest_user_id,
                message=user_text,
                persist_chat=False,
                bot_id=None,
                incoming_language=None,
                conversation_context=messages,
                api_key=api_key,
                model=model,
            )
        except Exception as exc:  # noqa: BLE001
            raise EngineError(f"Nitro brain engine failed: {exc}", status_code=500) from exc

        reply_text = ""
        if isinstance(result, dict):
            reply_text = str(result.get("reply") or "")
        else:
            reply_text = str(result or "")

        if not reply_text:
            reply_text = "(The Nitro brain did not return a reply.)"

        words = reply_text.split(" ")
        for index, word in enumerate(words):
            piece = word if index == len(words) - 1 else f"{word} "
            yield _sse_delta_chunk(piece)