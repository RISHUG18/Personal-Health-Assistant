"""Interfaces for embedding providers (Dependency Inversion Principle - friendly)."""

from __future__ import annotations

from typing import Protocol, Sequence


class Embedder(Protocol): #any class that implements this protocol can be used as an embedder
    #declaring the interface for embedding queries and texts, without tying to a specific implementation
    def embed_query(self, text: str) -> list[float]:
        """Embed a single query string into a vector."""

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        """Embed multiple texts into vectors."""
