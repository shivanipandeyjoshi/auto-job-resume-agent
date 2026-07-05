from __future__ import annotations

from pathlib import Path
from typing import Any

import chromadb
from sentence_transformers import SentenceTransformer


class ChromaStore:
    """Persist embeddings for job descriptions and resume text using ChromaDB."""

    def __init__(self, persist_dir: str | Path | None = None) -> None:
        self.persist_dir = Path(persist_dir or "jobs/chroma")
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        self.collection = self.client.get_or_create_collection(name="job_embeddings")
        self.model = self._load_model()

    def _load_model(self) -> SentenceTransformer:
        """Load the sentence-transformers embedding model, falling back to a simple stub if unavailable."""

        try:
            return SentenceTransformer("all-MiniLM-L6-v2")
        except Exception:
            class _FallbackModel:
                def encode(self, texts: list[str]) -> list[list[float]]:
                    return [[float(len(text))] for text in texts]

            return _FallbackModel()  # type: ignore[return-value]

    def add_documents(self, documents: list[dict[str, Any]]) -> None:
        """Store documents with generated embeddings."""

        if not documents:
            return
        texts = [item["text"] for item in documents]
        ids = [item["id"] for item in documents]
        embeddings = self.model.encode(texts)
        metadatas = [item.get("metadata") or {"source": "local"} for item in documents]
        self.collection.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)

    def query(self, query_text: str, n_results: int = 3) -> list[dict[str, Any]]:
        """Query stored documents for the closest semantic matches."""

        if not query_text.strip():
            return []
        embedding = self.model.encode([query_text])[0]
        results = self.collection.query(query_embeddings=[embedding], n_results=n_results)
        return [
            {
                "id": result_id,
                "document": document,
                "metadata": metadata,
                "distance": distance,
            }
            for result_id, document, metadata, distance in zip(
                results["ids"][0],
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            )
        ]
