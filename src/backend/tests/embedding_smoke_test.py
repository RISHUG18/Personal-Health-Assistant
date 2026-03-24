"""Manual smoke test for query/chunk embeddings.

Uses the embedding service abstraction so production code can depend on the
`Embedder` interface.

Run (from `src/`):
  python -m backend.scripts.embedding_smoke_test
"""

from __future__ import annotations

from pathlib import Path

from backend.services.embeddings.query_embedding import get_default_embedder
from backend.services.preprocessing.chunking import doc_to_chunks
from backend.services.preprocessing.text_cleaning import clean_full_text


FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures"
SAMPLE_OCR_PATH = FIXTURES_DIR / "sample_ocr.txt"


def main() -> None:
    if not SAMPLE_OCR_PATH.exists():
        raise FileNotFoundError(f"Missing fixture: {SAMPLE_OCR_PATH}")

    raw = SAMPLE_OCR_PATH.read_text(encoding="utf-8")
    cleaned = clean_full_text(raw)
    chunks = doc_to_chunks(cleaned)
    if not chunks:
        raise RuntimeError("No chunks produced; cannot test embeddings")

    embedder = get_default_embedder()
    vectors = embedder.embed_texts(chunks[:8])

    print("Total chunks (sampled):", min(8, len(chunks)))
    print("Embedding dimension:", len(vectors[0]) if vectors else 0)
    print("\nSample vector (first 10 values):")
    print(vectors[0][:10] if vectors else [])


if __name__ == "__main__":
    main()
