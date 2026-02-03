import uuid
from typing import Dict


def retrieve_mock_context(user_id: str, query: str) -> Dict:
    """
    STUB: Simulates a RAG retrieval from a Vector Database.
    Used for Week 1 UI development & API contract testing.
    """
    base_storage_url = (
        "https://zooiydijrzwfbrzxvseh.supabase.co/storage/v1/object/public/medical-reports/"
        f"{user_id}"
    )

    return {
        "query_used": query,
        "retrieved_chunks": [
            {
                "chunk_id": str(uuid.uuid4()),
                "text_content": (
                    "Patient's Hemoglobin A1c is 6.2%, which places them in the "
                    "pre-diabetes range (5.7% - 6.4%). Dietary changes are recommended."
                ),
                "relevance_score": 0.89,
                "metadata": {
                    "source_filename": "Lab_Report_Oct_2025.pdf",
                    "source_url": f"{base_storage_url}/Lab_Report_Oct_2025.pdf",
                    "page_number": 2,
                },
            },
            {
                "chunk_id": str(uuid.uuid4()),
                "text_content": (
                    "Vitamin D deficiency noted (18 ng/mL). Patient reported fatigue "
                    "and muscle weakness during the consultation."
                ),
                "relevance_score": 0.85,
                "metadata": {
                    "source_filename": "Consultation_Notes_Nov.pdf",
                    "source_url": f"{base_storage_url}/Consultation_Notes_Nov.pdf",
                    "page_number": 1,
                },
            },
            {
                "chunk_id": str(uuid.uuid4()),
                "text_content": (
                    "Blood Pressure reading: 135/85 mmHg. Slightly elevated compared "
                    "to previous visit (120/80 mmHg)."
                ),
                "relevance_score": 0.72,
                "metadata": {
                    "source_filename": "Vitals_Log_Sept.pdf",
                    "source_url": f"{base_storage_url}/Vitals_Log_Sept.pdf",
                    "page_number": 4,
                },
            },
        ],
    }
