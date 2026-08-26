import os
from pathlib import Path

from dotenv import load_dotenv


# Load the backend-local environment file when the app is started from any cwd.
load_dotenv(Path(__file__).resolve().parents[2] / ".env")


OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
OPENROUTER_EMBED_MODEL = os.getenv("OPENROUTER_EMBED_MODEL", "openai/text-embedding-3-small")
OPENROUTER_HTTP_REFERER = os.getenv("OPENROUTER_HTTP_REFERER", "")
OPENROUTER_APP_NAME = os.getenv("OPENROUTER_APP_NAME", "StudyLens")
CHROMA_PATH = os.getenv("CHROMA_PATH", "./data/chroma")
DB_URL = os.getenv("DB_URL", "sqlite:///./data/studylens.db")
UPLOAD_PATH = os.getenv("UPLOAD_PATH", "./data/uploads")
ASSETS_PATH = os.getenv("ASSETS_PATH", "./data/assets")

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "256"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "32"))
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "3"))

# Set to true + pip install torch diffusers accelerate Pillow to enable
# SimianLuo/LCM_Dreamshaper_v7: 4-step LCM, ~5s/image on GTX 1650 4GB
ENABLE_IMAGE_GEN = os.getenv("ENABLE_IMAGE_GEN", "false").lower() == "true"
IMAGE_GEN_MODEL = os.getenv("IMAGE_GEN_MODEL", "SimianLuo/LCM_Dreamshaper_v7")
