from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parents[4]


@dataclass(frozen=True)
class Settings:
    data_dir: Path = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data"))).resolve()
    sqlite_path: Path = Path(os.getenv("SQLITE_PATH", str(BASE_DIR / "data" / "examlens.db"))).resolve()
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b-instruct")
    temperature: float = float(os.getenv("TEMPERATURE", "0.1"))
    top_k: int = int(os.getenv("TOP_K_RETRIEVAL", "6"))
    max_context_tokens: int = int(os.getenv("MAX_CONTEXT_TOKENS", "1800"))


settings = Settings()
