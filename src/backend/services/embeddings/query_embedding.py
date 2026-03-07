"""Convenience functions for embedding queries/texts.

Prefer depending on the `Embedder` protocol throughout the codebase.
"""

#This file provides utility functions for embedding queries and texts, abstracting away the details of the underlying embedding implementation. 
#It allows other parts of the codebase to easily obtain vector representations of text without needing to know which specific embedding model is being used.

from __future__ import annotations

import os
from typing import Optional, Sequence #optional - indicates that a value can be of a specified type or None

from backend.services.embeddings.interfaces import Embedder
from backend.services.embeddings.sentence_transformer_embedder import SentenceTransformerEmbedder


_DEFAULT_EMBEDDER: Optional[Embedder] = None #lazy loading of the default embedder instance, which can be configured via environment variables for flexibility without code changes


def get_default_embedder() -> Embedder:
    """Return (and lazily initialize) the default embedder implementation."""

    global _DEFAULT_EMBEDDER #modify the global variable 
    if _DEFAULT_EMBEDDER is None:
        #we can use env variables to configure the default embedder, allowing for flexibility without code changes
        model_name = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-base-en-v1.5")
        normalize = os.getenv("EMBEDDING_NORMALIZE", "true").lower() in {"1", "true", "yes"}
        _DEFAULT_EMBEDDER = SentenceTransformerEmbedder(
            model_name=model_name,
            normalize_embeddings=normalize,
        )
    return _DEFAULT_EMBEDDER

#API for embedding queries and texts, which other modules can use without needing to know about the specific embedder implementation.
#Inputs - query: a natural language string to be embedded, embedder: an optional Embedder instance to use instead of the default. 
#Outputs - a list of floats representing the embedded query vector.
def embed_query(query: str, *, embedder: Optional[Embedder] = None) -> list[float]:
    chosen = embedder or get_default_embedder()
    return chosen.embed_query(query)

#API for embedding multiple texts at once, which can be more efficient than embedding them one by one.
#Inputs - texts: a sequence of natural language strings to be embedded, embedder: an optional Embedder instance to use instead of the default. 
#Outputs - a list of lists of floats, where each inner list is the embedded vector for the corresponding input text.
def embed_texts(texts: Sequence[str], *, embedder: Optional[Embedder] = None) -> list[list[float]]:
    chosen = embedder or get_default_embedder()
    return chosen.embed_texts(texts)
