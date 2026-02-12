"""Chunking utilities for splitting cleaned OCR text into retrieval-ready chunks."""

import re
from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter


HEADING_RE = re.compile(r"(^[A-Z][A-Z\s]{3,}$)|(^\w+ Panel\b)|^(Results:?)", re.MULTILINE)


def split_into_sections(raw_text: str) -> List[str]:
    """Light-weight section splitter based on heading-like patterns."""

    headings = [(m.start(), m.group(0).strip()) for m in HEADING_RE.finditer(raw_text)]
    if not headings:
        return [raw_text.strip()]

    spans: list[str] = []
    starts = [pos for pos, _ in headings] + [len(raw_text)]

    for i, (pos, _title) in enumerate(headings):
        start = pos
        end = starts[i + 1]
        spans.append(raw_text[start:end].strip())
    return spans if spans else [raw_text.strip()]


MEASUREMENT_RE = re.compile(
    r"([A-Za-z0-9 %\-\+\(\)\/]+)\s+[:\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z/%µμ]*)"
)


def extract_table_rows(section_text: str) -> List[str]:
    """Extract measurement-like rows as single-line chunks."""

    rows: list[str] = []
    for line in section_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if MEASUREMENT_RE.search(line):
            rows.append(line)
    return rows


def recursive_split(text: str, chunk_size: int = 300, chunk_overlap: int = 50) -> List[str]:
    """Recursive character splitter (LangChain) for non-tabular text."""

    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_text(text)


def doc_to_chunks(ocr_text: str, chunk_size: int = 300, chunk_overlap: int = 50) -> List[str]:
    """Convert cleaned OCR text into a list of retrieval-ready chunks."""

    final_chunks: list[str] = []
    sections = split_into_sections(ocr_text)
    for sec in sections:
        rows = extract_table_rows(sec)
        if rows:
            final_chunks.extend(rows)
            remainder = "\n".join(
                [line for line in sec.splitlines() if not MEASUREMENT_RE.search(line)]
            )
            if remainder.strip():
                final_chunks.extend(recursive_split(remainder, chunk_size, chunk_overlap))
        else:
            final_chunks.extend(recursive_split(sec, chunk_size, chunk_overlap))

    filtered: list[str] = []
    seen: set[str] = set()
    for chunk in final_chunks:
        chunk = chunk.strip()
        if not chunk or len(chunk) < 10:
            continue
        if chunk in seen:
            continue
        seen.add(chunk)
        filtered.append(chunk)
    return filtered
