"""SentenceTransformers-based embedding provider."""
"""
    This file implements the Embedder interface using the SentenceTransformers library.
    It provides methods to embed single queries and batches of texts into vector representations.
"""

from __future__ import annotations #don't evaulate type annotations at runtime, which can help with forward references and reduce overhead

from dataclasses import dataclass
from typing import Sequence

from sentence_transformers import SentenceTransformer


@dataclass(frozen=True) #using dataclass to automatically generate init and other methods, and frozen=True to make it immutable
class SentenceTransformerEmbedder:
    """Concrete embedder using a local SentenceTransformers model."""

    model_name: str = "BAAI/bge-base-en-v1.5"
    normalize_embeddings: bool = True #normalize the output vectors to unit length, which can be beneficial for similarity comparisons

    def _load_model(self) -> SentenceTransformer:
        return SentenceTransformer(self.model_name)

    def embed_query(self, text: str) -> list[float]:
        if not text or not text.strip(): #input validation
            raise ValueError("query text must be non-empty")
        model = self._load_model() #load the model
        vector = model.encode(text, normalize_embeddings=self.normalize_embeddings) #encode the text into a vector, applying normalization if specified
        return vector.tolist()  

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        clean = []
        for text in texts:
            text = text.strip()
            if text:
                clean.append(text)
        if not clean:
            return []
        model = self._load_model()
        vectors = model.encode(clean, normalize_embeddings=self.normalize_embeddings)
        return [v.tolist() for v in vectors]
