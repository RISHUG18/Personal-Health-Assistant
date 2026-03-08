"""Chunking utilities for splitting cleaned OCR text into retrieval-ready chunks.

# Week-3 RAG ingestion improvement
# - Sentence-aware splitting to avoid cutting mid-sentence
# - Section label inference via keyword heuristics
# - Chunks carry section_label metadata for downstream indexing
"""

import re
from typing import Dict, List

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


# ---------------------------------------------------------------------------
# Week-3 RAG ingestion improvement — sentence-aware splitting
# ---------------------------------------------------------------------------

_SENTENCE_END_RE = re.compile(r"(?<=[.!?])\s+")


def _sentence_aware_split(
    text: str, chunk_size: int = 300, chunk_overlap: int = 50,
) -> List[str]:
    """Split *text* into chunks that respect sentence boundaries.

    Strategy
    --------
    1. Split text into sentences using a regex on sentence-ending punctuation.
    2. Greedily accumulate sentences until the chunk would exceed *chunk_size*.
    3. If a single sentence exceeds *chunk_size*, fall back to the LangChain
       ``RecursiveCharacterTextSplitter`` for that sentence only.
    4. Maintain an overlap window by carrying trailing sentences from the
       previous chunk into the next (up to *chunk_overlap* characters).
    """
    sentences = _SENTENCE_END_RE.split(text)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return []

    # Fast path: everything fits in one chunk already
    if len(text) <= chunk_size:
        return [text.strip()] if text.strip() else []

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for sent in sentences:
        sent_len = len(sent)

        # If a single sentence is longer than chunk_size, sub-split it
        if sent_len > chunk_size:
            # Flush any accumulated sentences first
            if current:
                chunks.append(" ".join(current))
                current, current_len = [], 0
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size, chunk_overlap=chunk_overlap,
            )
            chunks.extend(splitter.split_text(sent))
            continue

        # Would adding this sentence exceed the limit?
        projected = current_len + (1 if current else 0) + sent_len
        if projected > chunk_size and current:
            chunks.append(" ".join(current))
            # Overlap: carry trailing sentences whose total length ≤ overlap
            overlap_buf: list[str] = []
            overlap_len = 0
            for prev in reversed(current):
                if overlap_len + len(prev) + 1 > chunk_overlap:
                    break
                overlap_buf.insert(0, prev)
                overlap_len += len(prev) + 1
            current = overlap_buf
            current_len = sum(len(s) for s in current) + max(0, len(current) - 1)

        current.append(sent)
        current_len += (1 if len(current) > 1 else 0) + sent_len

    if current:
        chunks.append(" ".join(current))

    return chunks


def recursive_split(text: str, chunk_size: int = 300, chunk_overlap: int = 50) -> List[str]:
    """Recursive character splitter (LangChain) for non-tabular text.

    # Week-3 RAG ingestion improvement — now delegates to sentence-aware
    # splitting to produce chunks with complete sentences.
    """
    return _sentence_aware_split(text, chunk_size, chunk_overlap)


# ---------------------------------------------------------------------------
# Week-3 RAG ingestion improvement — section label inference
# ---------------------------------------------------------------------------

_SECTION_KEYWORDS: Dict[str, List[str]] = {
    "blood_test": [
        "hemoglobin", "hba1c", "cholesterol", "triglyceride", "hdl", "ldl",
        "rbc", "wbc", "platelet", "hematocrit", "mcv", "mch", "mchc",
        "creatinine", "urea", "bun", "glucose", "fasting", "albumin",
        "bilirubin", "sgot", "sgpt", "alt", "ast", "alkaline phosphatase",
        "ggt", "iron", "ferritin", "transferrin", "esr", "cbc",
        "blood count", "blood panel", "lipid", "liver function",
        "renal function", "kidney function", "thyroid", "tsh", "t3", "t4",
        "vitamin d", "vitamin b12", "folate", "calcium", "potassium",
        "sodium", "chloride", "magnesium", "phosphorus", "uric acid",
        "hematology", "complete blood", "electrolyte",
    ],
    "sleep_data": [
        "sleep score", "deep sleep", "rem sleep", "light sleep",
        "sleep duration", "sleep quality", "insomnia", "apnea",
        "sleep stage", "sleep efficiency", "awake time",
        "total sleep", "sleep cycle",
    ],
    "imaging": [
        "mri", "ct scan", "x-ray", "xray", "ultrasound", "sonography",
        "echocardiogram", "echo", "pet scan", "mammogram", "dexa",
        "bone density", "radiograph", "fluoroscopy", "angiography",
        "imaging", "scan report", "radiology",
    ],
    "vitals": [
        "blood pressure", "systolic", "diastolic", "heart rate",
        "pulse", "spo2", "oxygen saturation", "temperature",
        "respiratory rate", "bmi", "body mass index",
        "weight", "height",
    ],
    "summary": [
        "summary", "impression", "conclusion", "diagnosis",
        "recommendation", "follow up", "follow-up", "advice",
        "assessment", "plan", "prognosis", "clinical note",
    ],
}


def infer_section_label(text: str) -> str:
    """Infer a section label for a chunk based on keyword heuristics.

    # Week-3 RAG ingestion improvement
    Returns one of: blood_test, sleep_data, imaging, vitals, summary, other.
    """
    lower = text.lower()
    scores: Dict[str, int] = {}
    for label, keywords in _SECTION_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in lower)
        if score > 0:
            scores[label] = score
    if not scores:
        return "other"
    return max(scores, key=scores.get)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Week-3 RAG ingestion improvement — chunk-with-metadata output
# ---------------------------------------------------------------------------

def doc_to_chunks(
    ocr_text: str, chunk_size: int = 300, chunk_overlap: int = 50,
) -> List[str]:
    """Convert cleaned OCR text into a list of retrieval-ready chunks.

    Backward-compatible: returns plain strings.
    Use :func:`doc_to_chunks_with_metadata` for enriched output.
    """
    return [c["text"] for c in doc_to_chunks_with_metadata(ocr_text, chunk_size, chunk_overlap)]


def doc_to_chunks_with_metadata(
    ocr_text: str, chunk_size: int = 300, chunk_overlap: int = 50,
) -> List[Dict[str, str]]:
    """Convert cleaned OCR text into chunks with section_label metadata.

    # Week-3 RAG ingestion improvement

    Each returned dict has:
    - ``text``: the chunk text
    - ``section_label``: inferred section label (blood_test | sleep_data | imaging | vitals | summary | other)
    """
    final_chunks: list[Dict[str, str]] = []
    sections = split_into_sections(ocr_text)

    for sec in sections:
        rows = extract_table_rows(sec)
        raw_chunks: list[str] = []
        if rows:
            raw_chunks.extend(rows)
            remainder = "\n".join(
                [line for line in sec.splitlines() if not MEASUREMENT_RE.search(line)]
            )
            if remainder.strip():
                raw_chunks.extend(recursive_split(remainder, chunk_size, chunk_overlap))
        else:
            raw_chunks.extend(recursive_split(sec, chunk_size, chunk_overlap))

        # Infer section label from the *entire* section for consistency
        section_label = infer_section_label(sec)

        for chunk_text in raw_chunks:
            final_chunks.append({
                "text": chunk_text.strip(),
                "section_label": section_label,
            })

    # Deduplicate and filter
    filtered: list[Dict[str, str]] = []
    seen: set[str] = set()
    for item in final_chunks:
        text = item["text"]
        if not text or len(text) < 10:
            continue
        if text in seen:
            continue
        seen.add(text)
        filtered.append(item)
    return filtered
