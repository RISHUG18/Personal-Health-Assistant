"""SentenceTransformers-based embedding provider.

This file implements the `Embedder` interface using the SentenceTransformers library.
It provides methods to embed individual queries and batches of texts into dense vector representations.
"""

from __future__ import annotations

import functools
from dataclasses import dataclass
from typing import Sequence

from sentence_transformers import SentenceTransformer


@functools.lru_cache(maxsize=4)
def _get_cached_model(model_name: str) -> SentenceTransformer:
    """Load and cache a SentenceTransformer model by name.

    The LRU cache means the heavy model file (~500 MB for bge-base-en-v1.5)
    is read from disk exactly once per unique model_name per process, then
    kept in memory for all subsequent embed_query / embed_texts calls.
    """
    return SentenceTransformer(model_name)


@dataclass(frozen=True) #using dataclass to automatically generate init and other methods, and frozen=True to make it immutable
class SentenceTransformerEmbedder:
    """Concrete embedder using a local SentenceTransformers model."""

    model_name: str = "BAAI/bge-base-en-v1.5"
    normalize_embeddings: bool = True #normalize the output vectors to unit length, so that we can use cosime similarity as a distance metric in retrieval

    def embed_query(self, text: str) -> list[float]:
        if not text or not text.strip():
            raise ValueError("query text must be non-empty")
        # _get_cached_model returns the already-loaded model on every call
        # after the first — no disk I/O on repeated calls.
        model = _get_cached_model(self.model_name)
        vector = model.encode(text, normalize_embeddings=self.normalize_embeddings)
        return vector.tolist()

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        """Embed multiple texts in one batched model call."""
        clean = [t.strip() for t in texts if t.strip()]
        if not clean:
            return []
        model = _get_cached_model(self.model_name)
        vectors = model.encode(clean, normalize_embeddings=self.normalize_embeddings)
        return [v.tolist() for v in vectors]
