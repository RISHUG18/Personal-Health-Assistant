Avnish Uba


# `chunking.py` — OCR Text → RAG Chunks

This module implements the **RAG chunking step** for our medical report pipeline.

Its purpose is to convert raw **OCR-extracted text** from printed (non-handwritten) medical PDFs into clean, retrievable text chunks that can later be embedded and stored in the vector database.

---

##  What this file does

Given OCR text from a report, it produces a list of chunks such that:

* Lab/table measurement lines stay intact
  (e.g., `LDL: 190 mg/dL`)
* Narrative sections (doctor notes, observations) are split into coherent paragraphs
* Chunks are sized appropriately for embedding models and LLM context limits

---

## Pipeline Overview

The chunking process has 3 stages:

### 1. Section Splitting (Heading-based)

The code first detects report headings such as:

* `LIPID PANEL`
* `CBC PANEL`
* `Results:`

and splits the document into logical sections.

Function:

```python
split_into_sections(raw_text)
```

This helps prevent mixing unrelated parts of the report in the same chunk.

---

### 2. Measurement Row Extraction

Medical reports often contain lab values in table-like form:

```
Hemoglobin: 12.5 g/dL
Vitamin D: 18 ng/mL
LDL: 190 mg/dL
```

Such lines are detected using a regex heuristic and extracted as individual chunks.

Function:

```python
extract_table_rows(section_text)
```

This ensures numerical results remain self-contained evidence units.

---

### 3. Recursive Chunking for Remaining Text

Any remaining narrative text (consultation notes, explanations, etc.) is split using:

```python
RecursiveCharacterTextSplitter
```

Default settings:

* `chunk_size = 300`
* `chunk_overlap = 50`

Function:

```python
recursive_split(text)
```

This preserves paragraph/sentence boundaries where possible.

---

## Main Entry Point

Use the function:

```python
doc_to_chunks(ocr_text)
```

Example:

```python
from chunking import doc_to_chunks

chunks = doc_to_chunks(ocr_text)

for c in chunks:
    print(c)
```

Output:

* List of chunk strings (`List[str]`)
* Ready for embedding (Gemini) and insertion into pgvector

---

## Example Test

Create a quick test script:

```python
from chunking import doc_to_chunks

sample_text = """
LIPID PANEL
LDL: 190 mg/dL
HDL: 45 mg/dL

Consultation Notes:
Patient reports fatigue and low energy.
Lifestyle changes recommended.
"""

chunks = doc_to_chunks(sample_text)

for i, c in enumerate(chunks, 1):
    print(f"--- Chunk {i} ---")
    print(c)
```

Run:

```bash
python test_chunking.py
```

Expected output:

* Measurement lines as standalone chunks
* Consultation notes chunked separately

---

## Notes / Scope

* This chunking is designed for **printed OCR reports only**
* Handwritten report OCR is out of scope for this project
* Metadata attachment (user_id, report_id, embedding_model) happens in the ingestion layer after chunking

---

## Used By

This module is part of the **RAG Ingestion Pipeline**:

```
OCR Text → Chunking (this file) → Embeddings → Vector DB → Retrieval → Gemini
```

