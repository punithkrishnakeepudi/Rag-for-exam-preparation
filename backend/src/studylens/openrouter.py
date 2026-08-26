"""OpenRouter client used by StudyLens generation and retrieval pipelines."""

import json
from typing import AsyncIterator

import httpx

from .config import (
    OPENROUTER_API_KEY,
    OPENROUTER_APP_NAME,
    OPENROUTER_BASE_URL,
    OPENROUTER_EMBED_MODEL,
    OPENROUTER_HTTP_REFERER,
    OPENROUTER_MODEL,
)


def _headers() -> dict[str, str]:
    if not OPENROUTER_API_KEY:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not configured. Add it to backend/.env "
            "or export it before starting StudyLens."
        )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "X-OpenRouter-Title": OPENROUTER_APP_NAME,
    }
    if OPENROUTER_HTTP_REFERER:
        headers["HTTP-Referer"] = OPENROUTER_HTTP_REFERER
    return headers


def _messages(prompt: str, system: str = "") -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return messages


def _payload(prompt: str, system: str = "", *, stream: bool = False) -> dict:
    return {
        "model": OPENROUTER_MODEL,
        "messages": _messages(prompt, system),
        "stream": stream,
    }


def _raise_api_error(response: httpx.Response) -> None:
    if not response.is_error:
        return
    try:
        detail = response.json().get("error", {}).get("message")
    except (ValueError, TypeError, httpx.ResponseNotRead):
        detail = None
    if response.is_error:
        if detail:
            raise RuntimeError(f"OpenRouter request failed: {detail}")
        response.raise_for_status()


async def embed(texts: str | list[str]) -> list[list[float]]:
    """Return embeddings in the same order as the input strings."""
    inputs = [texts] if isinstance(texts, str) else texts
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            f"{OPENROUTER_BASE_URL}/embeddings",
            headers=_headers(),
            json={"model": OPENROUTER_EMBED_MODEL, "input": inputs},
        )
    _raise_api_error(response)
    data = response.json().get("data", [])
    if len(data) != len(inputs):
        raise RuntimeError(
            f"OpenRouter returned {len(data)} embeddings for {len(inputs)} inputs."
        )
    return [item["embedding"] for item in sorted(data, key=lambda item: item.get("index", 0))]


async def generate(prompt: str, system: str = "") -> str:
    async with httpx.AsyncClient(timeout=600) as client:
        response = await client.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers=_headers(),
            json=_payload(prompt, system),
        )
    _raise_api_error(response)
    return response.json()["choices"][0]["message"].get("content", "")


async def json_generate(prompt: str, system: str = "") -> str:
    """Request valid JSON using OpenRouter's JSON response mode."""
    payload = _payload(prompt, system)
    payload["response_format"] = {"type": "json_object"}
    async with httpx.AsyncClient(timeout=600) as client:
        response = await client.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers=_headers(),
            json=payload,
        )
    _raise_api_error(response)
    return response.json()["choices"][0]["message"].get("content", "")


async def stream(
    prompt: str, system: str = "", format_json: bool = False
) -> AsyncIterator[str]:
    """Yield text deltas from an OpenRouter Server-Sent Events response."""
    payload = _payload(prompt, system, stream=True)
    if format_json:
        payload["response_format"] = {"type": "json_object"}

    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream(
            "POST",
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers=_headers(),
            json=payload,
        ) as response:
            if response.is_error:
                # Body must be read before .json() on a streaming response.
                await response.aread()
                _raise_api_error(response)
            async for line in response.aiter_lines():
                if not line or line.startswith(":"):
                    continue
                if not line.startswith("data:"):
                    continue
                raw = line[5:].strip()
                if raw == "[DONE]":
                    break
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if data.get("error"):
                    raise RuntimeError(
                        f"OpenRouter stream failed: {data['error'].get('message', 'unknown error')}"
                    )
                choices = data.get("choices", [])
                if choices:
                    content = choices[0].get("delta", {}).get("content")
                    if content:
                        yield content
