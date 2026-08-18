"""
ai-backend/engines/router.py

Strict, provider-agnostic AI engine layer for Nitro Infinity AI.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx


class EngineError(Exception):
    """Raised for any engine-level failure (auth, network, bad upstream response)."""

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


def _resolve_default_model(model: Optional[str]) -> str:
    if model and model != "nitro-v1":
        return model
    return "google/gemma-2-9b-it:free"


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
                    yield (
                        f"data: [{error_prefix} upstream error {response.status_code}: "
                        f"{body.decode(errors='replace')[:500]}]\n\n"
                    )
                    yield "data: [DONE]\n\n"
                    return

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        yield f"{line.strip()}\n\n"

    except httpx.TimeoutException as exc:
        raise EngineError(f"Upstream request timed out: {exc}", status_code=504) from exc
    except httpx.RequestError as exc:
        raise EngineError(f"Upstream request failed: {exc}", status_code=502) from exc


class NitroEngine(BaseEngine):
    provider_id = "nitro"

    def __init__(
        self,
        base_url: Optional[str] = None,
        system_api_key_env: str = "NITRO_SYSTEM_API_KEY",
    ) -> None:
        self._base_url = base_url or os.environ.get("NITRO_API_BASE", "https://openrouter.ai").rstrip("/")
        self._system_api_key_env = system_api_key_env

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        api_key: Optional[str],
    ) -> AsyncGenerator[str, None]:
        resolved_key = api_key or os.environ.get(self._system_api_key_env)

        if not resolved_key:
            raise EngineError(
                "No Nitro API key supplied and NITRO_SYSTEM_API_KEY is not configured on the server.",
                status_code=500,
            )

        url = f"{self._base_url}/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {resolved_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": _resolve_default_model(model),
            "messages": messages,
            "stream": True,
        }

        async for sse_line in _stream_raw_sse_passthrough(
            url=url,
            headers=headers,
            payload=payload,
            error_prefix="Nitro/OpenRouter",
        ):
            yield sse_line


class OpenAICompatibleEngine(BaseEngine):
    provider_id = "openai-compatible"

    def __init__(self, base_url: str, is_openrouter: bool = False) -> None:
        if not base_url:
            raise ValueError("OpenAICompatibleEngine requires a non-empty base_url.")
        if is_openrouter:
            resolved_root = os.environ.get("NITRO_API_BASE", "https://openrouter.ai").rstrip("/")
            self._base_url = f"{resolved_root}/api/v1"
        else:
            self._base_url = base_url.rstrip("/")
        self._is_openrouter = is_openrouter

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        api_key: Optional[str],
    ) -> AsyncGenerator[str, None]:
        if not api_key:
            raise EngineError(
                "This provider requires a user-supplied API key. Add one in settings and try again.",
                status_code=400,
            )

        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        resolved_model = _resolve_default_model(model) if self._is_openrouter else model
        payload = {
            "model": resolved_model,
            "messages": messages,
            "stream": True,
        }

        async for sse_line in _stream_raw_sse_passthrough(
            url=url,
            headers=headers,
            payload=payload,
            error_prefix="Upstream",
        ):
            yield sse_line


_OPENAI_COMPATIBLE_BASE_URLS: Dict[str, str] = {
    "openai": "https://api.openai.com/v1",
    "groq": "https://api.groq.com/openai/v1",
    "openrouter": "https://openrouter.ai/api/v1",
    "together": "https://api.together.xyz/v1",
}


def resolve_engine(provider_id: str) -> BaseEngine:
    normalized = (provider_id or "").strip().lower()

    if normalized == "nitro":
        return NitroEngine()

    if normalized == "openrouter":
        return OpenAICompatibleEngine(base_url=_OPENAI_COMPATIBLE_BASE_URLS["openrouter"], is_openrouter=True)

    if normalized in _OPENAI_COMPATIBLE_BASE_URLS:
        return OpenAICompatibleEngine(base_url=_OPENAI_COMPATIBLE_BASE_URLS[normalized])

    raise EngineError(
        f"Unknown providerId '{provider_id}'. Valid options: nitro, {', '.join(_OPENAI_COMPATIBLE_BASE_URLS.keys())}.",
        status_code=400,
    )