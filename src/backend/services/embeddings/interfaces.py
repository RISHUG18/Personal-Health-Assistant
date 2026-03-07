"""Interfaces for embedding providers"""

from __future__ import annotations #future annotations allow us to use type hints that refer to classes that are defined later in the code, enabling more flexible and readable type annotations without needing to worry about the order of class definitions

from typing import Protocol, Sequence
#sequence - anything that you can iterate over, like lists or tuples
#protocol - a way to define an interface that other classes can implement, without needing to inherit from a specific base class.

class Embedder(Protocol): #any class that implements this protocol can be used as an embedder
    #declaring the interface for embedding queries and texts, without tying to a specific implementation
    def embed_query(self, text: str) -> list[float]:
        """Embed a single query string into a vector."""

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        """Embed multiple texts into vectors."""
