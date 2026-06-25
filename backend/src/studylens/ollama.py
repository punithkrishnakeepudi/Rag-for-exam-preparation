import json
import httpx
from typing import AsyncIterator
from .config import OLLAMA_BASE_URL, MODEL_NAME, EMBED_MODEL


async def embed(texts: str | list[str]) -> list[list[float]]:
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(
            f"{OLLAMA_BASE_URL}/api/embed",
            json={"model": EMBED_MODEL, "input": texts},
        )
        r.raise_for_status()
        return r.json()["embeddings"]


async def generate(prompt: str, system: str = "") -> str:
    async with httpx.AsyncClient(timeout=600) as client:
        r = await client.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={"model": MODEL_NAME, "prompt": prompt, "system": system, "stream": False},
        )
        r.raise_for_status()
        return r.json()["response"]


async def json_generate(prompt: str, system: str = "") -> str:
    """Enforce JSON output via Ollama format mode — guarantees parseable JSON."""
    async with httpx.AsyncClient(timeout=600) as client:
        r = await client.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "system": system,
                "stream": False,
                "format": "json",
            },
        )
        r.raise_for_status()
        return r.json()["response"]


async def stream(prompt: str, system: str = "", format_json: bool = False) -> AsyncIterator[str]:
    payload: dict = {"model": MODEL_NAME, "prompt": prompt, "system": system, "stream": True}
    if format_json:
        payload["format"] = "json"
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream(
            "POST",
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line:
                    data = json.loads(line)
                    if not data.get("done"):
                        yield data.get("response", "")
