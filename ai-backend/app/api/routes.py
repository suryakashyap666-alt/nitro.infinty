"""
ai-backend/app/api/routes.py

POST /api/v1/chat — Main authenticated Nitro AI chat endpoint (SSE Streaming & Direct).
"""
from __future__ import annotations

import json
from typing import List, Literal, Optional

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

from engines.router import EngineError, resolve_engine

router = APIRouter(prefix="/api/v1", tags=["chat"])


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(..., min_length=1)


class ChatRequestPayload(BaseModel):
    modelId: Optional[str] = Field(default="nitro-v1", description="Nitro AI model identifier")
    providerId: Optional[str] = Field(default="nitro", description="Set to 'nitro'")
    botId: Optional[str] = Field(default=None, description="Optional custom bot ID")
    messages: List[ChatMessage] = Field(..., min_length=1)
    userApiKey: Optional[str] = Field(default=None, description="Nitro API Key")
    stream: Optional[bool] = Field(default=True, description="Enable SSE streaming output")

    @field_validator("messages")
    @classmethod
    def messages_not_empty(cls, value: List[ChatMessage]) -> List[ChatMessage]:
        if not value:
            raise ValueError("messages must contain at least one entry.")
        return value


async def _sse_stream(payload: ChatRequestPayload, api_key: Optional[str]):
    try:
        engine = resolve_engine("nitro")
    except EngineError as exc:
        yield f"event: error\ndata: {exc.message}\n\n"
        yield "data: [DONE]\n\n"
        return

    raw_messages = [{"role": m.role, "content": m.content} for m in payload.messages]

    try:
        async for sse_line in engine.stream_chat(
            messages=raw_messages,
            model=payload.modelId or "nitro-v1",
            api_key=api_key or payload.userApiKey,
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
    authorization: Optional[str] = Header(None),
) -> StreamingResponse:
    # Resolve API Key from Authorization header or payload
    api_key = payload.userApiKey
    if authorization and authorization.startswith("Bearer "):
        api_key = authorization.split(" ", 1)[1].strip()

    return StreamingResponse(
        _sse_stream(payload, api_key),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )