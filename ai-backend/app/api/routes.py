from __future__ import annotations

import json
import os
from typing import List, Literal, Optional

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field, field_validator

from engines.router import EngineError, resolve_engine

router = APIRouter(prefix="/api/v1", tags=["chat"])


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(..., min_length=1)


class ChatRequestPayload(BaseModel):
    modelId: Optional[str] = Field(default="nitro-v1", description="Nitro AI model identifier")
    botId: Optional[str] = Field(default=None, description="Optional custom bot ID")
    messages: List[ChatMessage] = Field(..., min_length=1)
    userApiKey: Optional[str] = Field(default=None, description="Nitro API Key")
    stream: Optional[bool] = Field(default=True, description="Enable SSE streaming")

    @field_validator("messages")
    @classmethod
    def messages_not_empty(cls, value: List[ChatMessage]) -> List[ChatMessage]:
        if not value:
            raise ValueError("messages must contain at least one entry.")
        return value


def _verify_api_key(
    payload_key: Optional[str],
    header_key: Optional[str],
    auth_header: Optional[str],
) -> Optional[str]:
    server_key = os.environ.get("NITRO_API_KEY")
    if not server_key:
        return payload_key or header_key

    provided_key = header_key or payload_key
    if not provided_key and auth_header and auth_header.startswith("Bearer "):
        provided_key = auth_header.split(" ", 1)[1].strip()

    if provided_key != server_key:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid Nitro API Key.")

    return provided_key


async def _sse_stream(payload: ChatRequestPayload, verified_key: Optional[str]):
    engine = resolve_engine("nitro")
    raw_messages = [{"role": m.role, "content": m.content} for m in payload.messages]

    try:
        async for sse_line in engine.stream_chat(
            messages=raw_messages,
            model=payload.modelId or "nitro-v1",
            api_key=verified_key,
            bot_id=payload.botId,
        ):
            if sse_line:
                yield sse_line
    except EngineError as exc:
        yield f"event: error\ndata: {exc.message}\n\n"
    except Exception as exc:  # noqa: BLE001
        yield f"event: error\ndata: Nitro engine error: {exc}\n\n"
    finally:
        yield "data: [DONE]\n\n"


@router.post("/chat")
async def chat(
    payload: ChatRequestPayload,
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    authorization: Optional[str] = Header(default=None),
):
    verified_key = _verify_api_key(payload.userApiKey, x_api_key, authorization)

    if payload.stream is False:
        from brain.core import CoreBrain
        from legacy.bots_engine import BotMarketplaceEngine

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        data_dir = os.environ.get("NITRO_DATA_DIR") or os.path.join(base_dir, "data")
        storage_path = os.path.join(data_dir, "nitro_state.json")

        bot_market = BotMarketplaceEngine(storage_path=storage_path)
        brain = CoreBrain(storage_path=storage_path, bot_market=bot_market)

        last_message = payload.messages[-1].content
        raw_history = [{"role": m.role, "content": m.content} for m in payload.messages]

        result = brain.handle_message(
            user_id="api_client",
            message=last_message,
            persist_chat=True,
            bot_id=payload.botId,
            conversation_context=raw_history,
            api_key=verified_key,
            model=payload.modelId,
        )

        return JSONResponse(content={
            "ok": True,
            "reply": result.get("reply", ""),
            "topic": result.get("topic", "general"),
            "emotion": result.get("emotion", "neutral"),
            "imageAction": result.get("imageAction"),
        })

    return StreamingResponse(
        _sse_stream(payload, verified_key),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )