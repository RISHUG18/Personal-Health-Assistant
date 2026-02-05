from langchain_text_splitters import RecursiveCharacterTextSplitter, CharacterTextSplitter
import re
from typing import List

HEADING_RE = re.compile(r"(^[A-Z][A-Z\s]{3,}$)|(^\w+ Panel\b)|^(Results:?)", re.MULTILINE)

def split_into_sections(raw_text: str) -> List[str]:
    """
    Very light-weight section splitter:
    - split where headings appear (all-caps lines or 'Panel' headings)
    - fall back to whole document if no headings detected
    """

    headings = [(m.start(), m.group(0).strip()) for m in HEADING_RE.finditer(raw_text)]
    if not headings:
        return [raw_text.strip()]

    spans = []
    starts = [pos for pos,_ in headings] + [len(raw_text)]
    
    for i, (pos, title) in enumerate(headings):
        start = pos
        end = starts[i+1]
        spans.append(raw_text[start:end].strip())
    return spans if spans else [raw_text.strip()]

# Heuristic: lines that look like "<TestName> ... <number> <unit>" are kept as single rows
MEASUREMENT_RE = re.compile(r"([A-Za-z0-9 %\-\+\(\)\/]+)\s+[:\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z/%µμ]*)")

def extract_table_rows(section_text: str) -> List[str]:
    """
    Turn lines that look like measurements into single-line chunks.
    Otherwise return empty list (so recursive splitter will handle).
    """
    rows = []
    for line in section_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if MEASUREMENT_RE.search(line):
            rows.append(line)
    return rows

#  Recursive splitting 
def recursive_split(text: str, chunk_size: int = 300, chunk_overlap: int = 50) -> List[str]:
    """
    Token-aware recursive splitter using the langchain package.
    """
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_text(text)

# Public pipeline 
def doc_to_chunks(ocr_text: str, chunk_size: int = 300, chunk_overlap: int = 50) -> List[str]:
    """
    1) Section pre-split
    2) Extract measurement rows as individual chunks
    3) Recursive split the remaining section text
    """
    final_chunks = []
    sections = split_into_sections(ocr_text)
    for sec in sections:
        rows = extract_table_rows(sec)
        if rows:
            for r in rows:
                final_chunks.append(r)
            remainder = "\n".join([l for l in sec.splitlines() if not MEASUREMENT_RE.search(l)])
            if remainder.strip():
                final_chunks.extend(recursive_split(remainder, chunk_size, chunk_overlap))
        else:
            final_chunks.extend(recursive_split(sec, chunk_size, chunk_overlap))

    filtered = []
    seen = set()
    for c in final_chunks:
        c = c.strip()
        if not c or len(c) < 10:
            continue
        if c in seen:
            continue
        seen.add(c)
        filtered.append(c)
    return filtered
