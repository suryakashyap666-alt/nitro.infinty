"""
ai-backend/app/api/routes.py

POST /api/v1/chat — The versioned entrypoint for Nitro Infinity AI.
Intercepts image generation requests before token delta streaming, produces a
clean structured JSON payload with a Data URI, and blocks raw text/binary leaks.
"""

from __future__ import annotations

import json
import uuid
from typing import AsyncGenerator, List, Literal, Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

from engines.router import EngineError, resolve_engine
from legacy.image.image_system import (
    detect_image_intent,
    generate_image_fake,
    plan_style_and_quality,
    safety_block,
)

router = APIRouter(prefix="/api/v1", tags=["chat"])


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(..., min_length=1)


class ChatRequestPayload(BaseModel):
    providerId: str = Field(default="nitro", description="e.g. 'nitro', 'groq', 'gemini', 'openrouter'")
    modelId: str = Field(default="nitro-v1", description="Upstream model identifier")
    messages: List[ChatMessage] = Field(..., min_length=1)
    userApiKey: Optional[str] = Field(default=None, description="Caller-supplied API key")

    @field_validator("messages")
    @classmethod
    def messages_not_empty(cls, value: List[ChatMessage]) -> List[ChatMessage]:
        if not value:
            raise ValueError("messages must contain at least one entry.")
        return value


def _get_last_user_prompt(messages: List[ChatMessage]) -> str:
    for m in reversed(messages):
        if m.role == "user" and m.content.strip():
            return m.content.strip()
    return messages[-1].content.strip()


async def _handle_image_generation(prompt: str) -> AsyncGenerator[str, None]:
    """Generates the image and returns a single clean JSON SSE frame containing the image Data URI."""
    block_reason = safety_block(prompt)
    if block_reason:
        payload = {
            "id": f"err-{uuid.uuid4().hex[:6]}",
            "type": "text",
            "content": f"[Safety] Image request blocked: {block_reason}",
        }
        yield f"data: {json.dumps(payload)}\n\n"
        yield "data: [DONE]\n\n"
        return

    plan = plan_style_and_quality(prompt)
    gen = generate_image_fake(prompt=prompt, plan=plan)

    img_data = gen.get("image", {})
    data_uri = img_data.get("data_url") or img_data.get("external_url") or ""

    # Return a structured JSON frame instead of streaming thousands of text tokens
    payload = {
        "id": f"img-{uuid.uuid4().hex[:6]}",
        "type": "image",
        "task": "image_generation",
        "prompt": prompt,
        "style": plan.style,
        "quality": plan.quality,
        "image_data": data_uri,
    }

    yield f"data: {json.dumps(payload)}\n\n"
    yield "data: [DONE]\n\n"


async def _sse_stream(payload: ChatRequestPayload) -> AsyncGenerator[str, None]:
    """
    Async generator bridging text/code streaming and structured image generation.
    """
    user_prompt = _get_last_user_prompt(payload.messages)
    image_intent = detect_image_intent(user_prompt)

    # 1. Image Generation Intent Route: Intercept to prevent text stream flooding
    if image_intent and image_intent.action == "generate":
        async for chunk in _handle_image_generation(image_intent.prompt):
            yield chunk
        return

    # 2. Standard Text / Code Reasoning Route
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
    except Exception as exc:
        yield f"event: error\ndata: Unexpected server error: {exc}\n\n"
    finally:
        yield "data: [DONE]\n\n"


@router.post("/chat")
async def chat(payload: ChatRequestPayload) -> StreamingResponse:
    """
    Stream chat completions or return clean image payloads over text/event-stream.
    """
    return StreamingResponse(
        _sse_stream(payload),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )