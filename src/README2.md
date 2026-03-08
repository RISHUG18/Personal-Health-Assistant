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



# RAG Text Cleaning & Chunking

## Purpose

src/backend/services/text_cleaning.py
src/backend/services/rag_cleaning_test.py

Converted raw OCR output from medical reports into **clean, structured text chunks** that can later be embedded into a vector database for retrieval (RAG).

It sits between:

```
OCR output → cleaning → chunking → embeddings (next step)
```

---

# What has been implemented

## 1. OCR Text Cleaning

Raw OCR output from medical reports is extremely noisy.
Common problems observed:

* Repeated lab headers/footers on every page
* Broken words due to OCR
* Random spacing and line breaks
* Page markers like `--- Page 1 ---`
* Address blocks and boilerplate text
* Multi-line table rows split incorrectly

Cleaning module performs:

* Page splitting
* Header/footer removal
* Whitespace normalization
* Removal of repeated boilerplate
* Preservation of medical values and units

Output is a **single clean text blob** suitable for chunking.

---


### Key design decisions

#### Section-based splitting

We first try to split document into logical sections:

* LIVER PANEL
* CBC
* LIPID PANEL
* etc.

This keeps related tests together.

#### Measurement row detection

Lines like:

```
Hemoglobin 10 g/dL
Vitamin D 20 ng/mL
```

are kept as **individual chunks**.

Reason:
These are most useful for retrieval.

#### Recursive splitting

Remaining text split using:

```
RecursiveCharacterTextSplitter
```

Maintains semantic coherence.


---

# Output format

Final output:

```
List[str]
```

Each item = one semantic chunk ready for embedding.

Saved locally to:

```
sample_chunks.txt
```

Used later for embedding + vector DB.

---

# Problems discovered during testing

## 1. OCR extremely noisy

OCR output varies heavily across reports:

* Different lab formats
* Misread units
* Broken lines
* Random spacing

Cleaning must remain flexible.

---

## 2. Over-cleaning risk

Initial cleaning removed entire text accidentally.

Cause:

* Over-aggressive header removal
* Regex matching too broadly

Fix:

* Made cleaning conservative
* Only remove obvious repeated boilerplate

---

## 3. Chunk quality issues

Some chunks still look like:

```
Estimated 107
Cee 1.73
```

Reason:
OCR table misalignment.

This will improve later when:

* Structured extraction improves
* Cleaning heuristics improve

---

## 4. One-report bias

Current testing uses only 1 report format.

Risk:
Different labs → different structure.

Solution :
Test on multiple report formats.

---

# Current status

Completed:

* Cleaning pipeline prototype
* Chunking pipeline working
* Sample chunks generated
* Ready for embedding phase




# RAG Ingestion: Supabase → Cleaning → Chunking

## What existed before

Earlier, the RAG preprocessing pipeline worked only on **local sample OCR files** (`sample_ocr.txt`).
This was useful for testing cleaning and chunking logic but did not reflect real project flow.

There was **no connection to actual OCR data stored in Supabase**, so the pipeline was isolated from the real backend.

---

## What has been implemented now

The RAG preprocessing pipeline is now connected to **real OCR data stored in Supabase**.

### Current flow

1. User uploads PDF → OCR runs → OCR text stored in Supabase
2. Using `report_id`, OCR text is fetched from Supabase
3. Text passes through RAG preprocessing pipeline:

   * Cleaning (remove headers, junk, noise)
   * Chunking (convert into meaningful retrieval chunks)
4. Chunks are printed and ready for embedding + vector DB storage

---

## Files involved

### `supabase_client.py`

* Provides Supabase connection
* Fetches OCR text using `report_id`

### `rag_cleaning_test.py`

* Fetches OCR text from Supabase
* Runs:

  * `clean_full_text()`
  * `doc_to_chunks()`
* Prints chunk output for verification

### `text_cleaning.py`

Removes:

* repeated headers
* metadata noise
* irrelevant text

Keeps:

* medical values
* meaningful report content

### `chunking.py`

Converts cleaned OCR into:

* measurement-based chunks
* section-based chunks
* recursive semantic chunks

---

## Why this matters

This connects the **real backend OCR pipeline** to the **RAG ingestion pipeline**.

We now have:

Real PDF → OCR → Supabase → Cleaning → Chunking → (next: embeddings → vector DB)

---

## Chunk Metadata for RAG Citations (Week-2 Change)

### Problem

The RAG pipeline could retrieve relevant chunks, but the **retrieval response lacked citation metadata**. The `context_schema.json` contract requires every chunk to carry:

```json
"metadata": {
  "source_filename": "Lab_Report_Oct_2025.pdf",
  "source_url": "https://…/medical-reports/…/Lab_Report_Oct_2025.pdf",
  "page_number": 2
}
```

Before this change, `pgvector_retrieval.py` and `faiss_retrieval.py` returned:

```json
"metadata": { "source": "pgvector" }
```

This meant the AI chat and frontend **could not show where a fact came from** — no filename, no link, no page reference.

### What was changed

#### 1. SQL Migration — `002_add_report_chunk_metadata.sql`

Extends the `report_chunks` table with three nullable columns:

| Column | Type | Purpose |
|---|---|---|
| `source_filename` | `TEXT` | Original report filename for citations |
| `source_url` | `TEXT` | Supabase Storage public URL |
| `page_number` | `INT` | Page origin of the chunk (best-effort) |

The `match_report_chunks` RPC function is also updated to:
- Return the three new columns
- `COALESCE` with `medical_reports` via `LEFT JOIN` so that chunks indexed **before** this migration still get metadata at query time

#### 2. Indexing — `indexer.py`

`index_report()` now accepts optional `source_filename`, `source_url`, and `page_number` kwargs. These are written into every chunk row during upsert.

#### 3. OCR Controller — `reports_controller.py`

`run_ocr_on_report()` passes `source_file_name` and `public_url` (already available from the Supabase upload) into `index_report()` during auto-indexing.

#### 4. Retrieval — `pgvector_retrieval.py` + `faiss_retrieval.py`

Both retrieval paths now return contract-compliant metadata:

```python
"metadata": {
    "source_filename": row.get("source_filename"),
    "source_url":      row.get("source_url"),
    "page_number":     row.get("page_number"),
    "source":          "pgvector",  # or "faiss"
}
```

FAISS retrieval additionally backfills metadata from `medical_reports` for pre-migration chunks that have `NULL` metadata columns — matching the `COALESCE` behaviour of the pgvector RPC.

### Metadata flow through the system

```
PDF Upload
  │
  ▼
run_ocr_on_report()          ← produces source_file_name + public_url
  │
  ▼
index_report(                ← receives metadata as kwargs
  source_filename=…,
  source_url=…,
)
  │
  ▼
report_chunks table          ← stores metadata per chunk row
  │
  ├──▶ pgvector RPC         ← COALESCE fallback via LEFT JOIN medical_reports
  │
  └──▶ FAISS SELECT          ← backfill query to medical_reports for NULLs
         │
         ▼
   { "metadata": { "source_filename", "source_url", "page_number" } }
         │
         ▼
   context_builder           ← passes metadata dict into RetrievedChunk
         │
         ▼
   RAG response / Gemini prompt
```

### Known limitations

- **`page_number` is currently `None`** for multi-page PDFs. The OCR step inserts `--- Page N ---` markers into the text, but the chunking pipeline doesn't yet parse them into per-chunk page numbers. This is tracked for a future improvement.
- The extra `"source": "pgvector"` / `"source": "faiss"` key is not in the contract schema but is kept for debugging/observability.

### How to apply

1. Run migration 001 first (if not already applied), then 002:
   ```sql
   -- In Supabase SQL Editor:
   \i src/db/migrations/001_add_report_chunks.sql
   \i src/db/migrations/002_add_report_chunk_metadata.sql
   ```
2. Re-index existing reports to populate metadata columns:
   ```bash
   cd src/
   python -m backend.scripts.ingest_supabase_reports \
     --user-id <UUID> --limit 10 \
     --verify-query "Why is my iron low?"
   ```


# Week-3: RAG Ingestion & Metadata Quality Improvements

## Background

Before Week-3, the RAG ingestion pipeline:

- **Chunked text using character-count splitting only** — the `RecursiveCharacterTextSplitter` would cut mid-sentence, producing chunks like `"Hemoglobin is 14.2 g/dL which is sl"` and `"ightly above normal range."`, hurting retrieval relevance.
- **Had no section labeling** — every chunk was treated as undifferentiated text. There was no way to filter or boost by medical category (blood test vs imaging vs vitals).
- **Was missing key metadata** — chunks stored `user_id`, `report_id`, `source_filename`, and `source_url`, but lacked `report_date`, `section_label`, and `embedding_version`. This made it impossible to filter by date, know what kind of data a chunk contained, or detect stale embeddings.
- **Had no re-embedding support** — if the embedding model or chunking strategy changed, there was no way to identify which chunks needed regeneration.

## What Changed

### 1. Sentence-Aware Chunking
The `recursive_split()` function now delegates to `_sentence_aware_split()`, which:
- Splits text into sentences first (on `.`, `!`, `?` boundaries).
- Greedily accumulates sentences up to `chunk_size` (default 300 chars).
- Falls back to `RecursiveCharacterTextSplitter` only for individual sentences that exceed `chunk_size`.
- Maintains overlap by carrying trailing sentences (not raw characters) into the next chunk.

Measurement lines (e.g. `Hemoglobin 14.2 g/dL`) are still extracted as single-line chunks — this behaviour is unchanged.

### 2. Section Label Inference
A new `infer_section_label(text)` function assigns one of six labels to each chunk:

| Label | Example Keywords |
|-------|-----------------|
| `blood_test` | hemoglobin, cholesterol, hba1c, cbc, lipid, thyroid |
| `sleep_data` | sleep score, deep sleep, rem sleep, insomnia |
| `imaging` | mri, ct scan, x-ray, ultrasound, radiology |
| `vitals` | blood pressure, heart rate, spo2, temperature |
| `summary` | summary, impression, diagnosis, recommendation |
| `other` | (default when no keywords match) |

The label is inferred from the **entire section** (not individual chunks) for consistency, then attached to every chunk from that section.

### 3. New Metadata Fields
Every stored chunk now includes:

| Field | Source | Purpose |
|-------|--------|---------|
| `section_label` | Keyword heuristics in `chunking.py` | Filter/boost retrieval by medical category |
| `report_date` | Passed from controller (upload timestamp) | Temporal filtering of chunks |
| `embedding_version` | `EMBEDDING_VERSION` constant in `indexer.py` | Detect stale embeddings after model changes |

### 4. Re-Embedding Support
Two new functions in `indexer.py`:
- **`reindex_report()`** — explicit entry-point to re-chunk and re-embed a report.
- **`find_stale_reports()`** — queries for `report_id`s whose chunks have an outdated `embedding_version`.

Together these enable a background job pattern: find stale → fetch OCR text → reindex.

## Files Modified

| File | Change |
|------|--------|
| `backend/services/preprocessing/chunking.py` | Sentence-aware splitting, `infer_section_label()`, `doc_to_chunks_with_metadata()` |
| `backend/services/retrieval/indexer.py` | Stores 3 new metadata fields, `EMBEDDING_VERSION` constant, `reindex_report()`, `find_stale_reports()` |
| `backend/services/retrieval/pgvector_retrieval.py` | Returns `section_label`, `report_date`, `embedding_version` in metadata dict |
| `backend/services/retrieval/faiss_retrieval.py` | Fetches and returns 3 new metadata fields |
| `backend/services/retrieval/__init__.py` | Exports `reindex_report`, `find_stale_reports` |
| `backend/controllers/reports_controller.py` | Passes `source_filename` and `report_date` to `index_report()` |
| `db/migrations/003_add_chunk_section_metadata.sql` | Adds 3 columns + index + updated `match_report_chunks` RPC |
| `backend/tests/test_text_cleaning.py` | 12 new tests for sentence splitting, section labeling, metadata output |

## Metadata Flow

```
OCR text
  → clean_full_text()          — removes junk, splits concatenated lines
  → doc_to_chunks_with_metadata()
      ├─ section_label          — inferred from keywords in each section
      └─ chunk text             — sentence-aware, non-overlapping sections
  → embed_texts()              — 768-dim bge-base-en-v1.5 vectors
  → upsert report_chunks       — stores section_label, report_date, embedding_version
  → retrieve (pgvector/FAISS)  — returns all metadata in result dict
  → context_builder            — metadata dict passes through to Gemini
```

## Backward Compatibility

- `doc_to_chunks()` still returns `List[str]` — existing callers are unaffected.
- The `match_report_chunks` RPC keeps the same name and input parameters; only the output columns are widened.
- Pre-existing chunks with `NULL` new columns get `COALESCE` defaults: `'other'` for `section_label`, parent `report_date` via JOIN fallback.
- All existing API routes and response shapes are unchanged.

## How to Apply

1. Run `db/migrations/003_add_chunk_section_metadata.sql` in the Supabase SQL editor.
2. Deploy the updated Python code.
3. (Optional) Re-index existing reports:
   ```python
   from backend.services.retrieval import find_stale_reports, reindex_report
   stale = find_stale_reports()
   for report_id in stale:
       # fetch user_id and ocr_text from medical_reports, then:
       reindex_report(report_id=report_id, user_id=..., ocr_text=...)
   ```











