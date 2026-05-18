import os
import httpx
from chromadb import PersistentClient
from app.core.config import settings

COLLECTION_NAME = "sop_chunks"


class SopRetriever:
    def __init__(self):
        db_path = os.path.abspath(settings.CHROMA_DB_PATH)
        self._client = PersistentClient(path=db_path)
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def _embed(self, text: str) -> list[float]:
        resp = httpx.post(
            f"{settings.API_BASE_URL}/embeddings",
            headers={
                "Authorization": f"Bearer {settings.DASHSCOPE_API_KEY}",
                "Content-Type": "application/json",
            },
            json={"model": settings.EMBEDDING_MODEL_NAME, "input": [text]},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()["data"][0]["embedding"]

    def search(self, query: str, top_k: int = 3) -> tuple[list[str], bool]:
        """Return (chunks, is_confident). is_confident=True when top score >= threshold."""
        if self._collection.count() == 0:
            return [], False

        query_vec = self._embed(query)
        results = self._collection.query(
            query_embeddings=[query_vec],
            n_results=min(top_k, self._collection.count()),
            include=["documents", "distances"],
        )

        docs = results["documents"][0]
        # ChromaDB cosine distance: 0=identical, 1=orthogonal; convert to similarity
        distances = results["distances"][0]
        similarities = [1.0 - d for d in distances]

        is_confident = bool(similarities and similarities[0] >= settings.RAG_SIMILARITY_THRESHOLD)
        return docs, is_confident
