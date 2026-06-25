import os

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL_NAME = os.getenv("MODEL_NAME", "qwen2.5")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
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
