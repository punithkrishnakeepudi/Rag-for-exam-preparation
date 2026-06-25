import chromadb
from .config import CHROMA_PATH

_client = None


def get_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=CHROMA_PATH)
    return _client


def get_collection(notebook_id: int):
    return get_client().get_or_create_collection(
        name=f"notebook_{notebook_id}",
        metadata={"hnsw:space": "cosine"},
    )
