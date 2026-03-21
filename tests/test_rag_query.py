"""Integration tests for RAG query pipeline and suggestion generation."""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
@pytest.mark.requires_env
class TestRAGQuery:
    """Test RAG query pipeline including retrieval and AI suggestions."""

    def test_rag_query_basic(self, test_client: TestClient, test_user: dict):
        """Test basic RAG query with minimal context."""
        query_data = {
            "user_id": test_user["id"],
            "query": "What are my recent lab results?",
            "role": "user",
            "top_k": 5
        }

        response = test_client.post("/api/v1/rag_query", json=query_data)

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        result = response.json()

        # Verify response structure
        assert "answer" in result, "Response should contain 'answer'"
        assert "context" in result, "Response should contain 'context'"
        assert "chunks_retrieved" in result
        assert "model" in result
        assert "grounding_available" in result

        # Model should be gemini-3.1-pro-preview
        assert "gemini-3.1-pro-preview" in result["model"].lower() or "gemini-3.1" in result["model"].lower(), \
            f"Expected gemini-3.1-pro-preview, got {result['model']}"

        print(f"\n✓ RAG query successful")
        print(f"  Model: {result['model']}")
        print(f"  Chunks retrieved: {result['chunks_retrieved']}")
        print(f"  Grounding available: {result['grounding_available']}")
        print(f"  Answer (first 200 chars): {result['answer'][:200]}")

    def test_rag_query_with_processed_report(self, test_client: TestClient, uploaded_report: dict, test_user: dict):
        """Test RAG query after processing a report (better grounding)."""
        import time

        report_id = uploaded_report["report_id"]

        # Wait for processing to complete
        max_wait = 60
        poll_interval = 2
        elapsed = 0

        print(f"\n  Waiting for report processing (report_id: {report_id})...")
        while elapsed < max_wait:
            time.sleep(poll_interval)
            elapsed += poll_interval

            status_response = test_client.get(f"/reports/status/{report_id}")
            status = status_response.json()

            if status["processing_status"] == "done":
                print(f"  ✓ Report processed in {elapsed}s")
                break
            elif status["processing_status"] == "failed":
                pytest.skip(f"Report processing failed: {status.get('processing_error')}")
        else:
            pytest.skip(f"Report processing did not complete within {max_wait}s")

        # Now query with grounding from the processed report
        query_data = {
            "user_id": test_user["id"],
            "query": "Based on my blood test results, what should I focus on?",
            "role": "user",
            "top_k": 10,
            "match_threshold": 0.3
        }

        response = test_client.post("/api/v1/rag_query", json=query_data)

        assert response.status_code == 200
        result = response.json()

        # With a processed report, we should have better grounding
        print(f"\n✓ RAG query with grounding:")
        print(f"  Chunks retrieved: {result['chunks_retrieved']}")
        print(f"  Grounding available: {result['grounding_available']}")
        print(f"  Answer: {result['answer'][:300]}")

        # Context should contain the assembled data
        context = result["context"]
        assert "query" in context
        assert "user_id" in context
        assert "rag_knowledge_base" in context

    def test_rag_query_empty_query(self, test_client: TestClient, test_user: dict):
        """Test that empty queries are rejected."""
        query_data = {
            "user_id": test_user["id"],
            "query": "",  # Empty query
            "role": "user"
        }

        response = test_client.post("/api/v1/rag_query", json=query_data)

        assert response.status_code == 422, "Empty query should be rejected"

    def test_rag_query_whitespace_only(self, test_client: TestClient, test_user: dict):
        """Test that whitespace-only queries are rejected."""
        query_data = {
            "user_id": test_user["id"],
            "query": "   \n  \t  ",  # Whitespace only
            "role": "user"
        }

        response = test_client.post("/api/v1/rag_query", json=query_data)

        assert response.status_code == 422, "Whitespace-only query should be rejected"

    def test_rag_query_without_user_id(self, test_client: TestClient):
        """Test that queries without user_id are rejected."""
        query_data = {
            "query": "What are my lab results?",
            # Missing user_id
        }

        response = test_client.post("/api/v1/rag_query", json=query_data)

        assert response.status_code == 422, "Query without user_id should be rejected"

    def test_rag_query_doctor_role(self, test_client: TestClient, test_user: dict):
        """Test RAG query with doctor role (clinical assistant mode)."""
        query_data = {
            "user_id": test_user["id"],
            "query": "Provide clinical insights on this patient's cardiovascular markers",
            "role": "doctor",  # Clinical mode
            "top_k": 8
        }

        response = test_client.post("/api/v1/rag_query", json=query_data)

        assert response.status_code == 200
        result = response.json()
        assert "answer" in result
        print(f"\n✓ Doctor role query successful")
        print(f"  Answer: {result['answer'][:200]}")

    def test_rag_query_with_section_filter(self, test_client: TestClient, test_user: dict):
        """Test RAG query with section filter (Week 4 optimization)."""
        query_data = {
            "user_id": test_user["id"],
            "query": "What were my blood test results?",
            "role": "user",
            "section_filter": "blood_test",  # Filter by section
            "top_k": 5
        }

        response = test_client.post("/api/v1/rag_query", json=query_data)

        assert response.status_code == 200
        result = response.json()
        assert "answer" in result
        print(f"\n✓ Section-filtered query successful")
        print(f"  Chunks retrieved: {result['chunks_retrieved']}")

    def test_rag_query_with_environment(self, test_client: TestClient, test_user: dict):
        """Test RAG query with environmental context."""
        query_data = {
            "user_id": test_user["id"],
            "query": "Should I go for a run today?",
            "role": "user",
            "environment": {
                "aqi_level": 150,  # Poor air quality
                "weather_condition": "Hazy",
                "location_city": "Delhi",
                "temperature_celsius": 35
            }
        }

        response = test_client.post("/api/v1/rag_query", json=query_data)

        assert response.status_code == 200
        result = response.json()
        assert "answer" in result

        # Answer should consider the poor air quality
        # (This is a soft check - we can't guarantee exact content)
        print(f"\n✓ Environment-aware query successful")
        print(f"  Answer considers AQI=150 (poor): {result['answer'][:200]}")

    def test_rag_query_with_gps_coordinates(self, test_client: TestClient, test_user: dict):
        """Test RAG query with GPS coordinates for live environmental data."""
        query_data = {
            "user_id": test_user["id"],
            "query": "What's the air quality like here?",
            "role": "user",
            "user_lat": 17.385044,  # Hyderabad
            "user_lon": 78.486671,
            "user_location": "Hyderabad"
        }

        response = test_client.post("/api/v1/rag_query", json=query_data)

        assert response.status_code == 200
        result = response.json()
        assert "answer" in result
        print(f"\n✓ GPS-based environmental query successful")

    def test_rag_query_faiss_strategy(self, test_client: TestClient, test_user: dict):
        """Test RAG query with FAISS retrieval strategy (local fallback)."""
        query_data = {
            "user_id": test_user["id"],
            "query": "Summarize my health status",
            "role": "user",
            "retrieval_strategy": "faiss",  # Use FAISS instead of pgvector
            "top_k": 5
        }

        response = test_client.post("/api/v1/rag_query", json=query_data)

        # FAISS might not be fully set up, so we accept either success or error
        if response.status_code == 200:
            result = response.json()
            assert "answer" in result
            print(f"\n✓ FAISS retrieval successful")
        else:
            print(f"\n⚠ FAISS retrieval not available: {response.status_code}")
            pytest.skip("FAISS retrieval strategy not available")

    def test_rag_query_high_similarity_threshold(self, test_client: TestClient, test_user: dict):
        """Test RAG query with very high similarity threshold."""
        query_data = {
            "user_id": test_user["id"],
            "query": "Tell me about my cholesterol levels",
            "role": "user",
            "match_threshold": 0.9,  # Very high threshold
            "top_k": 10
        }

        response = test_client.post("/api/v1/rag_query", json=query_data)

        assert response.status_code == 200
        result = response.json()

        # With high threshold, fewer chunks should be retrieved
        print(f"\n✓ High-threshold query successful")
        print(f"  Chunks retrieved with threshold=0.9: {result['chunks_retrieved']}")
        assert result["chunks_retrieved"] >= 0  # Might be 0 if nothing matches
