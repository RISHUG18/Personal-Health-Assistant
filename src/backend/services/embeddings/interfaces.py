"""Interfaces for embedding providers (DIP-friendly)."""

from __future__ import annotations

from typing import Protocol, Sequence


class Embedder(Protocol):
    def embed_query(self, text: str) -> list[float]:
        """Embed a single query string into a vector."""

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        """Embed multiple texts into vectors."""
