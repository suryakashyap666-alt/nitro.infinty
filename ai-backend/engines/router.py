"""
ai-backend/engines/router.py

Strict, provider-agnostic free-tier AI engine layer for Nitro Infinity AI.
Connects all free-tier providers: Google AI Studio (Gemini 1.5 Flash), GroqCloud,
OpenRouter Free, Hugging Face Serverless, and local Nitro Brain.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx


class EngineError(Exception):
    """Raised for any engine-level failure."""

    def __init__(self, message: str, *, status_code: int = 502) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class BaseEngine(ABC):
    provider_id: str = "base"

    @abstractmethod
    def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        api_key: Optional[str],
    ) -> AsyncGenerator[str, None]:
        raise NotImplementedError


def _resolve_free_model(provider_id: str, model: Optional[str]) -> str:
    """Resolves default free-tier models when unspecified."""
    if model and model not in ("nitro-v1", "default"):
        return model

    defaults = {
        "nitro": "meta-llama/llama-3.3-70b-instruct:free",
        "openrouter": "deepseek/deepseek-r1:free",
        "groq": "llama-3.3-70b-versatile",
        "gemini": "gemini-1.5-flash",
        "huggingface": "black-forest-labs/FLUX.1-schnell",
        "nitro-brain": "nitro-brain-v1",
    }
    return defaults.get(provider_id, "meta-llama/llama-3.3-70b-instruct:free")


async def _stream_raw_sse_passthrough(
    *,
    url: str,
    headers: Dict[str, str],
    payload: Dict[str, Any],
    error_prefix: str,
) -> AsyncGenerator[str, None]:
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    error_msg = body.decode(errors="replace")[:500]
                    yield f"data: [{error_prefix} status {response.status_code}: {error_msg}]\n\n"
                    yield "data: [DONE]\n\n"
                    return

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        yield f"{line.strip()}\n\n"

    except httpx.TimeoutException as exc:
        raise EngineError(f"{error_prefix} request timed out: {exc}", status_code=504) from exc
    except httpx.RequestError as exc:
        raise EngineError(f"{error_prefix} connection failed: {exc}", status_code=502) from exc


class GeminiFreeEngine(BaseEngine):
    """
    Google AI Studio Gemini 1.5 Flash Free Tier Engine.
    Uses OpenAI-compatible endpoint available in Google AI Studio.
    """

    provider_id = "gemini"

    def __init__(self) -> None:
        self._base_url = "https://generativelanguage.googleapis.com/v1beta/openai"

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        api_key: Optional[str],
    ) -> AsyncGenerator[str, None]:
        resolved_key = (
            api_key
            or os.environ.get("GOOGLE_AI_STUDIO_API_KEY")
            or os.environ.get("GEMINI_API_KEY")
        )

        if not resolved_key:
            raise EngineError(
                "Google AI Studio API key not found. Set GOOGLE_AI_STUDIO_API_KEY in your "
                "environment or enter it in the client UI (100% free at aistudio.google.com).",
                status_code=400,
            )

        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {resolved_key}",
            "Content-Type": "application/json",
        }
        resolved_model = _resolve_free_model("gemini", model)
        payload = {
            "model": resolved_model,
            "messages": messages,
            "stream": True,
        }

        async for sse_line in _stream_raw_sse_passthrough(
            url=url,
            headers=headers,
            payload=payload,
            error_prefix="Google AI Studio (Gemini 1.5 Flash)",
        ):
            yield sse_line


class GroqFreeEngine(BaseEngine):
    """GroqCloud Free Tier Engine (LPU inference)."""

    provider_id = "groq"

    def __init__(self) -> None:
        self._base_url = "https://api.groq.com/openai/v1"

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        api_key: Optional[str],
    ) -> AsyncGenerator[str, None]:
        resolved_key = api_key or os.environ.get("GROQ_API_KEY")
        if not resolved_key:
            raise EngineError(
                "Groq API key not found. Set GROQ_API_KEY in environment or client settings "
                "(free tier available at console.groq.com).",
                status_code=400,
            )

        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {resolved_key}",
            "Content-Type": "application/json",
        }
        resolved_model = _resolve_free_model("groq", model)
        payload = {
            "model": resolved_model,
            "messages": messages,
            "stream": True,
        }

        async for sse_line in _stream_raw_sse_passthrough(
            url=url,
            headers=headers,
            payload=payload,
            error_prefix="Groq Free Tier",
        ):
            yield sse_line


class OpenRouterFreeEngine(BaseEngine):
    """OpenRouter Free Tier Hub (DeepSeek-R1, Qwen Coder, Llama 3)."""

    provider_id = "openrouter"

    def __init__(self) -> None:
        resolved_root = os.environ.get("NITRO_API_BASE", "https://openrouter.ai").rstrip("/")
        self._base_url = f"{resolved_root}/api/v1"

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        api_key: Optional[str],
    ) -> AsyncGenerator[str, None]:
        resolved_key = (
            api_key
            or os.environ.get("OPENROUTER_API_KEY")
            or os.environ.get("NITRO_SYSTEM_API_KEY")
        )

        url = f"{self._base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "HTTP-Referer": "https://nitro-ai.local",
            "X-Title": "Nitro Infinity AI Free",
        }
        if resolved_key:
            headers["Authorization"] = f"Bearer {resolved_key}"

        resolved_model = _resolve_free_model("openrouter", model)
        payload = {
            "model": resolved_model,
            "messages": messages,
            "stream": True,
        }

        async for sse_line in _stream_raw_sse_passthrough(
            url=url,
            headers=headers,
            payload=payload,
            error_prefix="OpenRouter Free Tier",
        ):
            yield sse_line


class HuggingFaceFreeEngine(BaseEngine):
    """Hugging Face Free Inference API (FLUX.1 Schnell & Stable Diffusion)."""

    provider_id = "huggingface"

    def __init__(self) -> None:
        self._base_url = "https://api-inference.huggingface.co/v1"

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        api_key: Optional[str],
    ) -> AsyncGenerator[str, None]:
        resolved_key = api_key or os.environ.get("HUGGINGFACE_API_KEY") or os.environ.get("HF_TOKEN")
        if not resolved_key:
            raise EngineError(
                "Hugging Face API key not found. Set HUGGINGFACE_API_KEY in environment or client "
                "(free tier available at huggingface.co/settings/tokens).",
                status_code=400,
            )

        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {resolved_key}",
            "Content-Type": "application/json",
        }
        resolved_model = _resolve_free_model("huggingface", model)
        payload = {
            "model": resolved_model,
            "messages": messages,
            "stream": True,
        }

        async for sse_line in _stream_raw_sse_passthrough(
            url=url,
            headers=headers,
            payload=payload,
            error_prefix="Hugging Face Free API",
        ):
            yield sse_line


class NitroDefaultEngine(BaseEngine):
    """First-party Nitro automated free-tier pipeline."""

    provider_id = "nitro"

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        api_key: Optional[str],
    ) -> AsyncGenerator[str, None]:
        # Priority 1: Google AI Studio if key configured
        if api_key or os.environ.get("GOOGLE_AI_STUDIO_API_KEY"):
            gemini_eng = GeminiFreeEngine()
            async for chunk in gemini_eng.stream_chat(messages, model, api_key):
                yield chunk
            return

        # Priority 2: OpenRouter Free Tier
        openrouter_eng = OpenRouterFreeEngine()
        async for chunk in openrouter_eng.stream_chat(messages, model, api_key):
            yield chunk


def resolve_engine(provider_id: str) -> BaseEngine:
    """Dynamically resolve a free-tier provider instance."""
    normalized = (provider_id or "").strip().lower()

    if normalized == "nitro":
        return NitroDefaultEngine()

    if normalized == "nitro-brain":
        from .nitro_brain_engine import NitroBrainEngine

        return NitroBrainEngine()

    if normalized == "gemini":
        return GeminiFreeEngine()

    if normalized == "groq":
        return GroqFreeEngine()

    if normalized == "openrouter":
        return OpenRouterFreeEngine()

    if normalized in ("huggingface", "hf"):
        return HuggingFaceFreeEngine()

    # Fallback to OpenRouter Free
    return OpenRouterFreeEngine()