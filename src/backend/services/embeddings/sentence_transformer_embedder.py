"""SentenceTransformers-based embedding provider.

Implements the `Embedder` interface using SentenceTransformers.
"""

'''
Embeddings are a way to represent text (or other data) as vectors of numbers, capturing semantic meaning.
This module provides an implementation of the `Embedder` interface using the SentenceTransformers library,
which allows us to convert queries and texts into dense vector representations that can be used for similarity search in retrieval tasks.
'''

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from sentence_transformers import SentenceTransformer


@dataclass(frozen=True) #using dataclass to automatically generate init and other methods, and frozen=True to make it immutable
class SentenceTransformerEmbedder:
    """Concrete embedder using a local SentenceTransformers model."""

    model_name: str = "BAAI/bge-base-en-v1.5"
    normalize_embeddings: bool = True #normalize the output vectors to unit length, so that we can use cosime similarity as a distance metric in retrieval

    def _load_model(self) -> SentenceTransformer:
        return SentenceTransformer(self.model_name)

    def embed_query(self, text: str) -> list[float]:
        if not text or not text.strip(): #input validation
            raise ValueError("query text must be non-empty")
        model = self._load_model() #load the model
        vector = model.encode(text, normalize_embeddings=self.normalize_embeddings) #encode the text into a vector, applying normalization if specified
        return vector.tolist()  #convert the numpy array to a regular list of floats for easier storage and compatibility with other components

# The embed_texts method is similar to embed_query but processes multiple texts at once, returning a list of vectors.
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
