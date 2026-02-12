"""Convenience functions for embedding queries/texts.

Prefer depending on the `Embedder` protocol throughout the codebase.
"""

from __future__ import annotations

import os
from typing import Optional, Sequence

from services.embeddings.interfaces import Embedder
from services.embeddings.sentence_transformer_embedder import SentenceTransformerEmbedder


_DEFAULT_EMBEDDER: Optional[Embedder] = None


def get_default_embedder() -> Embedder:
    """Return (and lazily initialize) the default embedder implementation."""

    global _DEFAULT_EMBEDDER
    if _DEFAULT_EMBEDDER is None:
        model_name = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-base-en-v1.5")
        normalize = os.getenv("EMBEDDING_NORMALIZE", "true").lower() in {"1", "true", "yes"}
        _DEFAULT_EMBEDDER = SentenceTransformerEmbedder(
            model_name=model_name,
            normalize_embeddings=normalize,
        )
    return _DEFAULT_EMBEDDER


def embed_query(query: str, *, embedder: Optional[Embedder] = None) -> list[float]:
    chosen = embedder or get_default_embedder()
    return chosen.embed_query(query)


def embed_texts(texts: Sequence[str], *, embedder: Optional[Embedder] = None) -> list[list[float]]:
    chosen = embedder or get_default_embedder()
    return chosen.embed_texts(texts)
