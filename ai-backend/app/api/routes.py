"""
ai-backend/app/api/routes.py

POST /api/v1/chat — SSE streaming chat completion endpoint.
"""

from __future__ import annotations

from typing import List, Literal, Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

from engines.router import EngineError, resolve_engine

router = APIRouter(prefix="/api/v1", tags=["chat"])


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(..., min_length=1)


class ChatRequestPayload(BaseModel):
    providerId: str = Field(..., min_length=1, description="e.g. 'nitro', 'openai', 'groq', 'openrouter'")
    modelId: str = Field(..., min_length=1, description="Upstream model identifier")
    messages: List[ChatMessage] = Field(..., min_length=1)
    userApiKey: Optional[str] = Field(
        default=None,
        description="Caller-supplied key for external providers; optional for Nitro.",
    )

    @field_validator("messages")
    @classmethod
    def messages_not_empty(cls, value: List[ChatMessage]) -> List[ChatMessage]:
        if not value:
            raise ValueError("messages must contain at least one entry.")
        return value


async def _sse_stream(payload: ChatRequestPayload):
    try:
        engine = resolve_engine(payload.providerId)
    except EngineError as exc:
        yield f"event: error\ndata: {exc.message}\n\n"
        yield "data: [DONE]\n\n"
        return

    raw_messages = [{"role": m.role, "content": m.content} for m in payload.messages]

    try:
        async for sse_line in engine.stream_chat(
            messages=raw_messages,
            model=payload.modelId,
            api_key=payload.userApiKey,
        ):
            if sse_line:
                yield sse_line

    except EngineError as exc:
        yield f"event: error\ndata: {exc.message}\n\n"

    except Exception as exc:  # noqa: BLE001
        yield f"event: error\ndata: Unexpected server error: {exc}\n\n"

    finally:
        yield "data: [DONE]\n\n"


@router.post("/chat")
async def chat(payload: ChatRequestPayload) -> StreamingResponse:
    return StreamingResponse(
        _sse_stream(payload),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )