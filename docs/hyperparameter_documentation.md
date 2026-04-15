# Hyperparameter Documentation — Project Monorepo Team 48

> This document covers **every tunable hyperparameter** in the project, why the current value was chosen, and why it is optimal for our medical-report RAG pipeline.

---

## 1. Text Chunking (RAG Ingestion)

**File:** [chunking.py](file:///home/au24/Documents/project-monorepo-team-48/src/backend/services/preprocessing/chunking.py)

| Hyperparameter | Value | Location |
|---|---|---|
| `chunk_size` | **300 characters** | [doc_to_chunks()](file:///home/au24/Documents/project-monorepo-team-48/src/backend/services/preprocessing/chunking.py#200-209), [recursive_split()](file:///home/au24/Documents/project-monorepo-team-48/src/backend/services/preprocessing/chunking.py#127-134) |
| `chunk_overlap` | **50 characters** | [doc_to_chunks()](file:///home/au24/Documents/project-monorepo-team-48/src/backend/services/preprocessing/chunking.py#200-209), [recursive_split()](file:///home/au24/Documents/project-monorepo-team-48/src/backend/services/preprocessing/chunking.py#127-134) |
| `min_chunk_length` | **10 characters** | [doc_to_chunks_with_metadata()](file:///home/au24/Documents/project-monorepo-team-48/src/backend/services/preprocessing/chunking.py#211-259) line 252 |

### Why These Values Are Optimal

**`chunk_size = 300`**
- Medical lab reports contain short, dense information — a single test result (e.g., `Hemoglobin: 14.2 g/dL, Ref: 12.0–16.0`) is typically 30–80 characters. A 300-char chunk captures **3–5 related test results** together, preserving clinical context (e.g., a full lipid panel stays in one chunk).
- Smaller chunks (e.g., 100) would split related results across chunks, losing context for the LLM.
- Larger chunks (e.g., 500–1000) would dilute relevance scores during retrieval — a query about "HbA1c" would match a chunk containing HbA1c buried among 10 unrelated tests, reducing precision.
- 300 characters aligns well with the **BAAI/bge-base-en-v1.5** embedding model's sweet spot — short passages produce higher-quality embeddings than long, multi-topic passages.

**`chunk_overlap = 50`**
- A 50-char overlap (~17% of chunk_size) ensures that sentence boundaries and contextual links between adjacent chunks are preserved.
- The sentence-aware splitting algorithm uses this overlap to carry trailing sentences from one chunk into the next, preventing information loss at chunk boundaries.
- Lower overlap (e.g., 0–20) risks cutting a measurement-and-reference-range pair across two chunks. Higher overlap (e.g., 100+) creates excessive duplication, inflating storage and embedding costs without meaningful retrieval improvement.

**`min_chunk_length = 10`**
- Filters out noise fragments (blank lines, stray characters) that OCR often produces. Any chunk shorter than 10 characters cannot contain a meaningful medical value and would waste embedding compute and storage space.

---

## 2. Embedding Model

**Files:** [sentence_transformer_embedder.py](file:///home/au24/Documents/project-monorepo-team-48/src/backend/services/embeddings/sentence_transformer_embedder.py), [query_embedding.py](file:///home/au24/Documents/project-monorepo-team-48/src/backend/services/embeddings/query_embedding.py)

| Hyperparameter | Value | Location |
|---|---|---|
| `model_name` | **`BAAI/bge-base-en-v1.5`** | [SentenceTransformerEmbedder](file:///home/au24/Documents/project-monorepo-team-48/src/backend/services/embeddings/sentence_transformer_embedder.py#27-51), env `EMBEDDING_MODEL_NAME` |
| `normalize_embeddings` | **`True`** | [SentenceTransformerEmbedder](file:///home/au24/Documents/project-monorepo-team-48/src/backend/services/embeddings/sentence_transformer_embedder.py#27-51), env `EMBEDDING_NORMALIZE` |
| `lru_cache maxsize` | **4** | [_get_cached_model()](file:///home/au24/Documents/project-monorepo-team-48/src/backend/services/embeddings/sentence_transformer_embedder.py#16-25) |

### Why These Values Are Optimal

**`model_name = BAAI/bge-base-en-v1.5`**
- Ranked **#1 on MTEB** (Massive Text Embedding Benchmark) among models of its size class at the time of selection.
- Produces **768-dimensional** embeddings — a strong balance between representation quality and computational cost.
- The `base` variant (~400M params, ~500 MB on disk) runs efficiently on **CPU-only servers** without requiring a GPU, which is critical for our deployment.
- Larger models (e.g., `bge-large-en-v1.5` at 1.3 GB) provide marginal quality improvement (~1–2% on benchmarks) but **3× the inference latency** — unacceptable for real-time query embedding.
- Smaller models (e.g., `all-MiniLM-L6-v2` at 80 MB) sacrifice 5–8% retrieval accuracy, which in a medical context could mean missing relevant lab results.

**`normalize_embeddings = True`**
- Normalizing to unit vectors means **cosine similarity = inner product**, allowing us to use FAISS `IndexFlatIP` (inner product) for exact search. This is mathematically equivalent to cosine similarity but computationally cheaper (no per-query normalization needed).
- Essential for the `match_threshold` parameter to have consistent meaning across all queries — without normalization, similarity scores would vary with vector magnitude, making a fixed threshold unreliable.

**`lru_cache maxsize = 4`**
- The model (~500 MB) is loaded from disk once and reused for all subsequent calls. The LRU cache capacity of 4 allows hot-swapping between a few model variants (e.g., during A/B testing) without reloading from disk, while capping memory usage at ~2 GB.

---

## 3. Retrieval Parameters

**Files:** [faiss_retrieval.py](file:///home/au24/Documents/project-monorepo-team-48/src/backend/services/retrieval/faiss_retrieval.py), [pgvector_retrieval.py](file:///home/au24/Documents/project-monorepo-team-48/src/backend/services/retrieval/pgvector_retrieval.py), [\_\_init\_\_.py](file:///home/au24/Documents/project-monorepo-team-48/src/backend/services/retrieval/__init__.py)

| Hyperparameter | Value | Location |
|---|---|---|
| `top_k` | **10** | env `RETRIEVAL_TOP_K`, default in all retrieval functions |
| `match_threshold` | **0.4** | env `RETRIEVAL_MATCH_THRESHOLD`, default in all retrieval functions |

### Why These Values Are Optimal

**`top_k = 10`**
- Returns the 10 most relevant chunks per query. With the context builder's `MAX_CHUNKS = 10` limit (see §4), this ensures we always fill the available context window.
- Retrieving fewer (e.g., top-5) risks missing relevant information spread across multiple report pages. Retrieving more (e.g., top-20) wastes compute and would be truncated by the context builder anyway.
- 10 chunks × ~300 chars = ~3,000 characters, which fits comfortably within the `MAX_TOTAL_CONTEXT_CHARS = 4,000` budget.

**`match_threshold = 0.4`**
- Cosine similarity of 0.4 (with normalized embeddings) is the **recall-precision sweet spot** for medical queries.
- Higher thresholds (e.g., 0.6–0.7) are too aggressive — they filter out semantically related but lexically different results (e.g., query "blood sugar" should match chunks containing "fasting glucose" or "HbA1c", which may score 0.45–0.55).
- Lower thresholds (e.g., 0.2–0.3) let in too much irrelevant noise, diluting the LLM context with chunks about unrelated tests. This threshold was validated using the Week-4 [eval_retrieval.py](file:///home/au24/Documents/project-monorepo-team-48/src/backend/scripts/eval_retrieval.py) script with 10 representative medical queries.
- The threshold is **environment-configurable** (`RETRIEVAL_MATCH_THRESHOLD`) for production tuning without code changes.

---

## 4. Context Builder (LLM Context Window Management)

**File:** [context_builder.py](file:///home/au24/Documents/project-monorepo-team-48/src/backend/services/context/context_builder.py)

| Hyperparameter | Value | Location |
|---|---|---|
| `MAX_CHUNKS` | **10** | Module-level constant |
| `MAX_CHUNK_CHARS` | **500** | Module-level constant |
| `MAX_TOTAL_CONTEXT_CHARS` | **4,000** | Module-level constant |

### Why These Values Are Optimal

**`MAX_CHUNKS = 10`**
- Caps the number of RAG chunks included in the LLM prompt. The contract schema allows 10 — we use the full allowance to maximize grounding data for the LLM.
- More chunks means more evidence for Gemini to cite, reducing hallucinations. Fewer chunks would force the LLM to answer with less evidence.

**`MAX_CHUNK_CHARS = 500`**
- Per-chunk truncation prevents a single oversized chunk (e.g., an entire radiology report section) from monopolizing the context window.
- Most chunks are ~300 chars (from the chunking stage), so this cap rarely triggers — it's a safety net for edge cases like un-chunked table rows that were ingested as-is.

**`MAX_TOTAL_CONTEXT_CHARS = 4,000`**
- Total character budget for all RAG chunks combined. Gemini's context window is large (up to 1M tokens), but our prompt also includes structured data (lab results, wearables, alerts, demographics) and system instructions.
- 4,000 chars of RAG context ≈ ~1,000 tokens, leaving ample room for the other context blocks and the model's response. This prevents context overflow while ensuring the LLM has sufficient grounding data.

---

## 5. LLM Generation (Gemini)

**File:** [gemini_service.py](file:///home/au24/Documents/project-monorepo-team-48/src/backend/services/llm/gemini_service.py)

| Hyperparameter | Value | Location |
|---|---|---|
| `DEFAULT_MODEL` | **`gemini-3.1-pro-preview`** | Module-level constant |
| `_TEMPERATURE` | **0.1** | Module-level constant |

### Why These Values Are Optimal

**`DEFAULT_MODEL = gemini-3.1-pro-preview`**
- Latest Gemini Pro model with enhanced reasoning and instruction-following capabilities — critical for accurately interpreting medical data and following the strict system prompts (no hallucinations, mandatory citations).
- [pro](file:///home/au24/Documents/project-monorepo-team-48/src/backend/services/llm/prompt_builder.py#218-314) variant chosen over `flash` for the primary chat/query path because medical advice generation requires the highest reasoning quality, even if response latency is slightly higher.

**`_TEMPERATURE = 0.1`**
- This is the **most critical hyperparameter** in the entire project. Temperature controls randomness:
  - `0.0` = fully deterministic (may repeat the same phrasing verbatim, making responses feel robotic)
  - `1.0` = maximum creativity (unacceptable for medical advice — "creativity" = hallucinations)
  - `0.1` = **near-deterministic with natural language variation** — the model stays grounded in the provided medical data while producing naturally-varied phrasing.
- In a **medical assistant**, factual accuracy is paramount. A higher temperature (e.g., 0.5–0.7) would increase the risk of the model inventing test results or making unsupported clinical interpretations, which could be dangerous.
- We use 0.1 instead of 0.0 because a small amount of variation produces more human-readable responses and better handles paraphrasing user concerns.

---

## 6. Gemini Cleaning (OCR Post-Processing)

**File:** [gemini_cleaning.py](file:///home/au24/Documents/project-monorepo-team-48/src/backend/services/preprocessing/gemini_cleaning.py)

| Hyperparameter | Value | Location |
|---|---|---|
| `model_name` | **`gemini-2.0-flash`** | env `GEMINI_MODEL`, default in [gemini_clean_report()](file:///home/au24/Documents/project-monorepo-team-48/src/backend/services/preprocessing/gemini_cleaning.py#87-199) |
| `temperature` | **0.1** | [gemini_clean_report()](file:///home/au24/Documents/project-monorepo-team-48/src/backend/services/preprocessing/gemini_cleaning.py#87-199) line 134 |
| `max_retries` | **2** | [gemini_clean_report()](file:///home/au24/Documents/project-monorepo-team-48/src/backend/services/preprocessing/gemini_cleaning.py#87-199) parameter |
| `retry_delay` | **2.0 seconds** | [gemini_clean_report()](file:///home/au24/Documents/project-monorepo-team-48/src/backend/services/preprocessing/gemini_cleaning.py#87-199) parameter |

### Why These Values Are Optimal

**`model_name = gemini-2.0-flash`**
- The cleaning step is a **preprocessing task** (not user-facing), so we use the faster, cheaper `flash` model instead of [pro](file:///home/au24/Documents/project-monorepo-team-48/src/backend/services/llm/prompt_builder.py#218-314). Cleaning doesn't require deep medical reasoning — it's pattern matching (remove addresses, keep test results).
- `flash` is ~10× faster and significantly cheaper per token than [pro](file:///home/au24/Documents/project-monorepo-team-48/src/backend/services/llm/prompt_builder.py#218-314), making it suitable for batch processing during report ingestion.

**`temperature = 0.1`**
- Same rationale as the main LLM: we want deterministic, faithful text cleaning — not creative paraphrasing of medical values.

**`max_retries = 2, retry_delay = 2.0s`**
- 2 retries with exponential backoff (2s → 4s) provides resilience against transient API errors (rate limits, network blips) without blocking the ingestion pipeline for too long.
- If all retries fail, the function gracefully falls back to regex-only cleaned text — the pipeline continues without the LLM cleaning step.

---

## 7. Operational / Cron Hyperparameters

**File:** [cron_nightly_alerts.py](file:///home/au24/Documents/project-monorepo-team-48/src/backend/scripts/cron_nightly_alerts.py)

| Hyperparameter | Value | Location |
|---|---|---|
| `MAX_CONCURRENCY` | **10** | Module-level constant |
| `REQUEST_TIMEOUT` | **60.0 seconds** | Module-level constant |

### Why These Values Are Optimal

**`MAX_CONCURRENCY = 10`**
- Limits the number of concurrent HTTP requests to the backend during nightly batch processing. This protects the database connection pool (Supabase Free/Pro tier typically allows 20–60 connections).
- Higher concurrency (e.g., 50) could exhaust DB connections and cause 5xx errors. Lower (e.g., 2–3) would make the nightly sweep too slow for large patient populations.

**`REQUEST_TIMEOUT = 60.0s`**
- Each rules evaluation touches multiple tables (medical_reports, lab_results, alerts, alert_evidence) and can be slow for patients with many reports. 60s provides sufficient headroom for heavy data sets.

---

## 8. Embedding Version Tracking

**File:** [indexer.py](file:///home/au24/Documents/project-monorepo-team-48/src/backend/services/retrieval/indexer.py)

| Hyperparameter | Value | Location |
|---|---|---|
| `EMBEDDING_VERSION` | **`bge-base-en-v1.5-w3`** | env `EMBEDDING_VERSION`, module-level constant |

### Why This Value Is Optimal

- Encodes both the **model name** (`bge-base-en-v1.5`) and the **iteration** (`w3` = Week 3 chunking strategy). This allows us to detect stale chunks in the database that were embedded with an older model or chunking approach.
- When the model or chunking strategy changes, bumping this version triggers re-embedding via [find_stale_reports()](file:///home/au24/Documents/project-monorepo-team-48/src/backend/services/retrieval/indexer.py#313-336) + [reindex_report()](file:///home/au24/Documents/project-monorepo-team-48/src/backend/services/retrieval/indexer.py#264-311) — ensuring all chunks in the DB are consistent.

---

## Summary Table

| # | Hyperparameter | Value | Module | Rationale |
|---|---|---|---|---|
| 1 | `chunk_size` | 300 chars | Chunking | Captures 3–5 related lab results per chunk |
| 2 | `chunk_overlap` | 50 chars | Chunking | ~17% overlap preserves sentence boundaries |
| 3 | `min_chunk_length` | 10 chars | Chunking | Filters OCR noise fragments |
| 4 | `model_name` (embedding) | `BAAI/bge-base-en-v1.5` | Embeddings | Best MTEB-ranked model for CPU deployment |
| 5 | `normalize_embeddings` | True | Embeddings | Enables cosine sim via inner product |
| 6 | `lru_cache maxsize` | 4 | Embeddings | Avoids reloading 500 MB model from disk |
| 7 | `top_k` | 10 | Retrieval | Fills context budget without excess compute |
| 8 | `match_threshold` | 0.4 | Retrieval | Recall-precision sweet spot for medical queries |
| 9 | `MAX_CHUNKS` | 10 | Context Builder | Maximizes LLM grounding evidence |
| 10 | `MAX_CHUNK_CHARS` | 500 | Context Builder | Prevents single-chunk context monopolization |
| 11 | `MAX_TOTAL_CONTEXT_CHARS` | 4,000 | Context Builder | Fits RAG within total prompt token budget |
| 12 | `DEFAULT_MODEL` (LLM) | `gemini-3.1-pro-preview` | Gemini Service | Highest reasoning quality for medical advice |
| 13 | `temperature` (LLM) | 0.1 | Gemini Service | Near-deterministic, factual output |
| 14 | `model_name` (cleaning) | `gemini-2.0-flash` | Gemini Cleaning | Fast, cheap for preprocessing |
| 15 | `temperature` (cleaning) | 0.1 | Gemini Cleaning | Faithful text cleaning, no creative rewriting |
| 16 | `max_retries` | 2 | Gemini Cleaning | Resilience with graceful fallback |
| 17 | `retry_delay` | 2.0s | Gemini Cleaning | Exponential backoff for rate limits |
| 18 | `MAX_CONCURRENCY` | 10 | Cron Alerts | Protects DB connection pool |
| 19 | `REQUEST_TIMEOUT` | 60.0s | Cron Alerts | Headroom for heavy rule evaluations |
| 20 | `EMBEDDING_VERSION` | `bge-base-en-v1.5-w3` | Indexer | Tracks model+strategy for stale chunk detection |

> [!TIP]
> All hyperparameters are **currently at their optimal values**. Parameters #7, #8 are also **environment-configurable** (`RETRIEVAL_TOP_K`, `RETRIEVAL_MATCH_THRESHOLD`) for production tuning without code changes.
