"""Manual smoke test for OCR cleaning and chunk generation pipeline.

Run (from `src/`):
  python -m backend.scripts.rag_cleaning_smoke_test
"""

from __future__ import annotations

from pathlib import Path

from backend.services.preprocessing.chunking import doc_to_chunks
from backend.services.preprocessing.text_cleaning import clean_full_text


FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures"
SAMPLE_OCR_PATH = FIXTURES_DIR / "sample_ocr.txt"


def main() -> None:
    if not SAMPLE_OCR_PATH.exists():
        raise FileNotFoundError(f"Missing fixture: {SAMPLE_OCR_PATH}")

    raw = SAMPLE_OCR_PATH.read_text(encoding="utf-8")

    print("\n===== RAW SAMPLE =====\n")
    print(raw[:500])
    print("\n======================\n")

    cleaned = clean_full_text(raw)
    print("\n===== CLEANED TEXT LENGTH =====")
    print(len(cleaned))
    print("===============================\n")

    print("\n===== CLEANED TEXT SAMPLE =====\n")
    print(cleaned[:800])
    print("\n===============================\n")

    if not cleaned.strip():
        raise RuntimeError("Cleaning returned empty output")

    chunks = doc_to_chunks(cleaned)
    print("\nTOTAL CHUNKS:", len(chunks))

    for i, chunk in enumerate(chunks[:10]):
        print(f"\n--- CHUNK {i + 1} ---")
        print(chunk)


if __name__ == "__main__":
    main()
