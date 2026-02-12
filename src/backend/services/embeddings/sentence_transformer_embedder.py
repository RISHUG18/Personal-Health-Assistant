"""SentenceTransformers-based embedding provider."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from sentence_transformers import SentenceTransformer


@dataclass(frozen=True)
class SentenceTransformerEmbedder:
    """Concrete embedder using a local SentenceTransformers model."""

    model_name: str = "BAAI/bge-base-en-v1.5"
    normalize_embeddings: bool = True

    def _load_model(self) -> SentenceTransformer:
        return SentenceTransformer(self.model_name)

    def embed_query(self, text: str) -> list[float]:
        if not text or not text.strip():
            raise ValueError("query text must be non-empty")
        model = self._load_model()
        vector = model.encode(text, normalize_embeddings=self.normalize_embeddings)
        return vector.tolist()  # type: ignore[no-any-return]

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        clean = [t for t in (t.strip() for t in texts) if t]
        if not clean:
            return []
        model = self._load_model()
        vectors = model.encode(clean, normalize_embeddings=self.normalize_embeddings)
        return [v.tolist() for v in vectors]
