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




Here is a **short, clean README** you can paste for your previous task
(chunking + cleaning work).
Keep it inside:

```
src/backend/services/README_chunking.md
```

or inside main backend README.

---




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




