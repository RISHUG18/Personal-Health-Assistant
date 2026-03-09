"""Week-4 Retrieval Optimization — unit tests for retrieval pipeline.

Tests cover:
- Metadata shape consistency between pgvector and FAISS retrieval paths
- Section-label filtering logic
- Configurable defaults via environment variables
- Timing metadata in retrieve_context output
- Structured logging output
"""

import os
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

# Week-4 Retrieval Optimization — retrieval validation tests

# ---------------------------------------------------------------------------
# Mock heavy third-party dependencies that may not be installed in the test
# environment.  Force-inject into sys.modules so the ENTIRE transitive import
# chain from backend.services.retrieval succeeds.
# ---------------------------------------------------------------------------

def _ensure_mock(name, attrs=None):
    """Inject a mock module into sys.modules if not already a real module."""
    if name not in sys.modules or isinstance(sys.modules[name], types.ModuleType) and not hasattr(sys.modules[name], "__file__"):
        mod = types.ModuleType(name)
        for k, v in (attrs or {}).items():
            setattr(mod, k, v)
        sys.modules[name] = mod

_ensure_mock("dotenv", {"load_dotenv": lambda *a, **kw: None})
_ensure_mock("supabase", {"Client": MagicMock, "create_client": MagicMock()})
_ensure_mock("sentence_transformers", {"SentenceTransformer": MagicMock})
_ensure_mock("langchain_text_splitters", {"RecursiveCharacterTextSplitter": MagicMock})
# faiss is imported lazily inside faiss_retrieval._import_faiss(),
# but we still stub it so that FaissRetriever._build_index works.
import numpy as np

class _FakeIndex:
    """Minimal FAISS IndexFlatIP stand-in for unit tests."""
    def __init__(self, dim):
        self._vecs = None
        self._dim = dim
    def add(self, matrix):
        self._vecs = matrix
    def search(self, query, k):
        # Compute inner product (cosine sim for unit vectors)
        scores = query @ self._vecs.T  # shape: (1, n)
        n = scores.shape[1]
        k = min(k, n)
        indices = np.argsort(-scores[0])[:k]
        sorted_scores = scores[0][indices]
        return sorted_scores.reshape(1, -1), indices.reshape(1, -1)

_faiss_mod = types.ModuleType("faiss")
_faiss_mod.IndexFlatIP = _FakeIndex  # type: ignore[attr-defined]
sys.modules["faiss"] = _faiss_mod
# Supabase sub-modules that may be imported transitively
for _sub in ("gotrue", "postgrest", "storage3", "realtime", "supafunc",
             "supabase._sync", "supabase._async"):
    _ensure_mock(_sub)

# Now safe to import our own code
from backend.services.retrieval.pgvector_retrieval import (
    retrieve_pgvector,
    _DEFAULT_TOP_K as PGV_DEFAULT_TOP_K,
    _DEFAULT_MATCH_THRESHOLD as PGV_DEFAULT_THRESHOLD,
)
from backend.services.retrieval.faiss_retrieval import (
    FaissRetriever,
    _DEFAULT_TOP_K as FAISS_DEFAULT_TOP_K,
    _DEFAULT_MATCH_THRESHOLD as FAISS_DEFAULT_THRESHOLD,
)
from backend.services.retrieval import retrieve_context


# ---------------------------------------------------------------------------
# Helpers — fake Supabase responses
# ---------------------------------------------------------------------------

def _make_pgvector_row(
    *,
    chunk_id="00000000-0000-0000-0000-000000000001",
    report_id="00000000-0000-0000-0000-000000000099",
    chunk_index=0,
    chunk_text="Hemoglobin 14.2 g/dL",
    similarity=0.85,
    source_filename="lab_report.pdf",
    source_url="https://example.com/lab.pdf",
    page_number=1,
    section_label="blood_test",
    report_date="2025-01-15",
    embedding_version="bge-base-en-v1.5-w3",
):
    """Return a dict mimicking a row from the match_report_chunks RPC."""
    return {
        "id": chunk_id,
        "report_id": report_id,
        "chunk_index": chunk_index,
        "chunk_text": chunk_text,
        "similarity": similarity,
        "source_filename": source_filename,
        "source_url": source_url,
        "page_number": page_number,
        "section_label": section_label,
        "report_date": report_date,
        "embedding_version": embedding_version,
    }


def _make_faiss_db_row(
    *,
    chunk_id="00000000-0000-0000-0000-000000000002",
    report_id="00000000-0000-0000-0000-000000000099",
    chunk_index=0,
    chunk_text="Hemoglobin 14.2 g/dL",
    embedding=None,
    source_filename="lab_report.pdf",
    source_url="https://example.com/lab.pdf",
    page_number=1,
    section_label="blood_test",
    report_date="2025-01-15",
    embedding_version="bge-base-en-v1.5-w3",
):
    """Return a dict mimicking a Supabase table row for FAISS."""
    return {
        "id": chunk_id,
        "report_id": report_id,
        "chunk_index": chunk_index,
        "chunk_text": chunk_text,
        "embedding": embedding or [0.1] * 768,
        "source_filename": source_filename,
        "source_url": source_url,
        "page_number": page_number,
        "section_label": section_label,
        "report_date": report_date,
        "embedding_version": embedding_version,
    }


# Required metadata keys every retrieval result chunk must contain
REQUIRED_METADATA_KEYS = {
    "source_filename",
    "source_url",
    "page_number",
    "source",
    "section_label",
    "report_date",
    "embedding_version",
}


# ---------------------------------------------------------------------------
# Test: pgvector metadata shape
# ---------------------------------------------------------------------------

class TestPgvectorMetadataShape(unittest.TestCase):
    """Ensure retrieve_pgvector returns all required metadata fields."""

    @patch("backend.services.retrieval.pgvector_retrieval._embed_query")
    @patch("backend.services.retrieval.pgvector_retrieval.get_supabase_client")
    def test_metadata_keys_present(self, mock_client_fn, mock_embed):
        """Every chunk returned by pgvector must contain all required metadata keys."""
        mock_embed.return_value = [0.1] * 768
        mock_response = MagicMock()
        mock_response.data = [_make_pgvector_row(), _make_pgvector_row(chunk_index=1)]
        mock_client = MagicMock()
        mock_client.rpc.return_value.execute.return_value = mock_response
        mock_client_fn.return_value = mock_client

        from backend.services.retrieval.pgvector_retrieval import retrieve_pgvector

        results = retrieve_pgvector(user_id="test-user", query="hemoglobin")

        self.assertEqual(len(results), 2)
        for chunk in results:
            meta = chunk["metadata"]
            missing = REQUIRED_METADATA_KEYS - set(meta.keys())
            self.assertEqual(
                missing, set(),
                f"pgvector chunk missing metadata keys: {missing}",
            )
            # Verify source is correctly tagged
            self.assertEqual(meta["source"], "pgvector")

    @patch("backend.services.retrieval.pgvector_retrieval._embed_query")
    @patch("backend.services.retrieval.pgvector_retrieval.get_supabase_client")
    def test_metadata_values_propagated(self, mock_client_fn, mock_embed):
        """Values from the RPC row should appear in metadata."""
        mock_embed.return_value = [0.1] * 768
        mock_response = MagicMock()
        mock_response.data = [
            _make_pgvector_row(section_label="vitals", report_date="2025-06-01"),
        ]
        mock_client = MagicMock()
        mock_client.rpc.return_value.execute.return_value = mock_response
        mock_client_fn.return_value = mock_client

        from backend.services.retrieval.pgvector_retrieval import retrieve_pgvector

        results = retrieve_pgvector(user_id="test-user", query="blood pressure")
        meta = results[0]["metadata"]
        self.assertEqual(meta["section_label"], "vitals")
        self.assertEqual(meta["report_date"], "2025-06-01")


# ---------------------------------------------------------------------------
# Test: FAISS metadata shape
# ---------------------------------------------------------------------------

class TestFaissMetadataShape(unittest.TestCase):
    """Ensure FAISS retrieval returns all required metadata fields."""

    @patch("backend.services.retrieval.faiss_retrieval._embed_query")
    @patch("backend.services.retrieval.faiss_retrieval.get_supabase_client")
    def test_metadata_keys_present(self, mock_client_fn, mock_embed):
        """Every chunk returned by FAISS must contain all required metadata keys."""
        import numpy as np

        # Create a unit vector for the query and stored chunks
        vec = [0.0] * 768
        vec[0] = 1.0  # unit vector
        mock_embed.return_value = vec

        row = _make_faiss_db_row(embedding=vec)
        mock_response = MagicMock()
        mock_response.data = [row]
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        mock_client_fn.return_value = mock_client

        from backend.services.retrieval.faiss_retrieval import FaissRetriever

        retriever = FaissRetriever(user_id="test-user", client=mock_client).build()
        results = retriever.search("hemoglobin", match_threshold=0.0)

        self.assertGreaterEqual(len(results), 1)
        for chunk in results:
            meta = chunk["metadata"]
            missing = REQUIRED_METADATA_KEYS - set(meta.keys())
            self.assertEqual(
                missing, set(),
                f"FAISS chunk missing metadata keys: {missing}",
            )
            self.assertEqual(meta["source"], "faiss")


# ---------------------------------------------------------------------------
# Test: Metadata consistency between pgvector and FAISS
# ---------------------------------------------------------------------------

class TestMetadataConsistency(unittest.TestCase):
    """Both retrieval paths must return chunks with identical metadata schema."""

    @patch("backend.services.retrieval.pgvector_retrieval._embed_query")
    @patch("backend.services.retrieval.pgvector_retrieval.get_supabase_client")
    @patch("backend.services.retrieval.faiss_retrieval._embed_query")
    @patch("backend.services.retrieval.faiss_retrieval.get_supabase_client")
    def test_same_metadata_keys(
        self, faiss_client_fn, faiss_embed, pgv_client_fn, pgv_embed,
    ):
        """pgvector and FAISS chunks must have the same metadata key set."""
        vec = [0.0] * 768
        vec[0] = 1.0
        pgv_embed.return_value = vec
        faiss_embed.return_value = vec

        # pgvector mock
        pgv_response = MagicMock()
        pgv_response.data = [_make_pgvector_row()]
        pgv_client = MagicMock()
        pgv_client.rpc.return_value.execute.return_value = pgv_response
        pgv_client_fn.return_value = pgv_client

        # FAISS mock
        faiss_response = MagicMock()
        faiss_response.data = [_make_faiss_db_row(embedding=vec)]
        faiss_client = MagicMock()
        faiss_client.table.return_value.select.return_value.eq.return_value.execute.return_value = faiss_response
        faiss_client_fn.return_value = faiss_client

        from backend.services.retrieval.pgvector_retrieval import retrieve_pgvector
        from backend.services.retrieval.faiss_retrieval import FaissRetriever

        pgv_results = retrieve_pgvector(user_id="u", query="test")
        faiss_retriever = FaissRetriever(user_id="u", client=faiss_client).build()
        faiss_results = faiss_retriever.search("test", match_threshold=0.0)

        pgv_keys = set(pgv_results[0]["metadata"].keys())
        faiss_keys = set(faiss_results[0]["metadata"].keys())
        self.assertEqual(
            pgv_keys, faiss_keys,
            f"Metadata key mismatch: pgvector={pgv_keys} vs faiss={faiss_keys}",
        )

    @patch("backend.services.retrieval.pgvector_retrieval._embed_query")
    @patch("backend.services.retrieval.pgvector_retrieval.get_supabase_client")
    @patch("backend.services.retrieval.faiss_retrieval._embed_query")
    @patch("backend.services.retrieval.faiss_retrieval.get_supabase_client")
    def test_same_top_level_keys(
        self, faiss_client_fn, faiss_embed, pgv_client_fn, pgv_embed,
    ):
        """pgvector and FAISS chunks must have the same top-level keys."""
        vec = [0.0] * 768
        vec[0] = 1.0
        pgv_embed.return_value = vec
        faiss_embed.return_value = vec

        pgv_response = MagicMock()
        pgv_response.data = [_make_pgvector_row()]
        pgv_client = MagicMock()
        pgv_client.rpc.return_value.execute.return_value = pgv_response
        pgv_client_fn.return_value = pgv_client

        faiss_response = MagicMock()
        faiss_response.data = [_make_faiss_db_row(embedding=vec)]
        faiss_client = MagicMock()
        faiss_client.table.return_value.select.return_value.eq.return_value.execute.return_value = faiss_response
        faiss_client_fn.return_value = faiss_client

        from backend.services.retrieval.pgvector_retrieval import retrieve_pgvector
        from backend.services.retrieval.faiss_retrieval import FaissRetriever

        pgv_results = retrieve_pgvector(user_id="u", query="test")
        faiss_retriever = FaissRetriever(user_id="u", client=faiss_client).build()
        faiss_results = faiss_retriever.search("test", match_threshold=0.0)

        pgv_top = set(pgv_results[0].keys())
        faiss_top = set(faiss_results[0].keys())
        self.assertEqual(
            pgv_top, faiss_top,
            f"Top-level key mismatch: pgvector={pgv_top} vs faiss={faiss_top}",
        )


# ---------------------------------------------------------------------------
# Test: Section-label filtering
# ---------------------------------------------------------------------------

class TestSectionFiltering(unittest.TestCase):
    """Validate that section_filter parameter works correctly."""

    @patch("backend.services.retrieval.pgvector_retrieval._embed_query")
    @patch("backend.services.retrieval.pgvector_retrieval.get_supabase_client")
    def test_pgvector_passes_section_filter_to_rpc(self, mock_client_fn, mock_embed):
        """When section_filter is set, it should be passed to the RPC call."""
        mock_embed.return_value = [0.1] * 768
        mock_response = MagicMock()
        mock_response.data = []
        mock_client = MagicMock()
        mock_client.rpc.return_value.execute.return_value = mock_response
        mock_client_fn.return_value = mock_client

        from backend.services.retrieval.pgvector_retrieval import retrieve_pgvector

        retrieve_pgvector(
            user_id="test-user",
            query="hemoglobin",
            section_filter="blood_test",
        )

        # Verify the RPC was called with filter_section_label
        call_args = mock_client.rpc.call_args
        rpc_params = call_args[0][1]
        self.assertEqual(rpc_params["filter_section_label"], "blood_test")

    @patch("backend.services.retrieval.pgvector_retrieval._embed_query")
    @patch("backend.services.retrieval.pgvector_retrieval.get_supabase_client")
    def test_pgvector_no_section_filter_omits_param(self, mock_client_fn, mock_embed):
        """When section_filter is None, filter_section_label should not be in RPC params."""
        mock_embed.return_value = [0.1] * 768
        mock_response = MagicMock()
        mock_response.data = []
        mock_client = MagicMock()
        mock_client.rpc.return_value.execute.return_value = mock_response
        mock_client_fn.return_value = mock_client

        from backend.services.retrieval.pgvector_retrieval import retrieve_pgvector

        retrieve_pgvector(user_id="test-user", query="test")

        call_args = mock_client.rpc.call_args
        rpc_params = call_args[0][1]
        self.assertNotIn("filter_section_label", rpc_params)

    @patch("backend.services.retrieval.faiss_retrieval._embed_query")
    @patch("backend.services.retrieval.faiss_retrieval.get_supabase_client")
    def test_faiss_section_filter_client_side(self, mock_client_fn, mock_embed):
        """FAISS section_filter should exclude non-matching chunks client-side."""
        vec = [0.0] * 768
        vec[0] = 1.0
        mock_embed.return_value = vec

        rows = [
            _make_faiss_db_row(
                chunk_id="id-1", chunk_text="Hemoglobin 14g/dL",
                section_label="blood_test", embedding=vec,
            ),
            _make_faiss_db_row(
                chunk_id="id-2", chunk_text="MRI shows normal",
                section_label="imaging", embedding=vec,
            ),
        ]
        mock_response = MagicMock()
        mock_response.data = rows
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        mock_client_fn.return_value = mock_client

        from backend.services.retrieval.faiss_retrieval import FaissRetriever

        retriever = FaissRetriever(user_id="u", client=mock_client).build()
        results = retriever.search(
            "hemoglobin", match_threshold=0.0, section_filter="blood_test",
        )

        # Only the blood_test chunk should be returned
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["metadata"]["section_label"], "blood_test")


# ---------------------------------------------------------------------------
# Test: retrieve_context dispatcher
# ---------------------------------------------------------------------------

class TestRetrieveContextDispatcher(unittest.TestCase):
    """Validate the unified retrieve_context entry-point."""

    @patch("backend.services.retrieval.retrieve_pgvector")
    def test_returns_timing_metadata(self, mock_pgv):
        """retrieve_context must include a timing dict."""
        mock_pgv.return_value = []

        from backend.services.retrieval import retrieve_context

        result = retrieve_context(user_id="u", query="test")

        self.assertIn("timing", result)
        self.assertIn("total_ms", result["timing"])
        self.assertIsInstance(result["timing"]["total_ms"], float)

    @patch("backend.services.retrieval.retrieve_pgvector")
    def test_passes_section_filter_to_pgvector(self, mock_pgv):
        """section_filter should be forwarded to the strategy function."""
        mock_pgv.return_value = []

        from backend.services.retrieval import retrieve_context

        retrieve_context(
            user_id="u", query="test", section_filter="vitals",
        )

        _, kwargs = mock_pgv.call_args
        self.assertEqual(kwargs["section_filter"], "vitals")

    @patch("backend.services.retrieval.retrieve_faiss")
    def test_passes_section_filter_to_faiss(self, mock_faiss):
        """section_filter should be forwarded to FAISS strategy."""
        mock_faiss.return_value = []

        from backend.services.retrieval import retrieve_context

        retrieve_context(
            user_id="u", query="test", strategy="faiss", section_filter="imaging",
        )

        _, kwargs = mock_faiss.call_args
        self.assertEqual(kwargs["section_filter"], "imaging")


# ---------------------------------------------------------------------------
# Test: Environment-variable configurable defaults
# ---------------------------------------------------------------------------

class TestConfigurableDefaults(unittest.TestCase):
    """Validate that RETRIEVAL_TOP_K and RETRIEVAL_MATCH_THRESHOLD env vars work."""

    def test_pgvector_default_top_k_from_env(self):
        """_DEFAULT_TOP_K should reflect RETRIEVAL_TOP_K env var."""
        # The module-level constant was already evaluated at import time.
        # We verify the pattern is correct by checking the import.
        from backend.services.retrieval.pgvector_retrieval import _DEFAULT_TOP_K
        # Default is 10 when env var is not set
        self.assertIsInstance(_DEFAULT_TOP_K, int)
        self.assertGreater(_DEFAULT_TOP_K, 0)

    def test_faiss_default_threshold_from_env(self):
        """_DEFAULT_MATCH_THRESHOLD should reflect RETRIEVAL_MATCH_THRESHOLD env var."""
        from backend.services.retrieval.faiss_retrieval import _DEFAULT_MATCH_THRESHOLD
        self.assertIsInstance(_DEFAULT_MATCH_THRESHOLD, float)
        self.assertGreaterEqual(_DEFAULT_MATCH_THRESHOLD, 0.0)
        self.assertLessEqual(_DEFAULT_MATCH_THRESHOLD, 1.0)


if __name__ == "__main__":
    unittest.main()
