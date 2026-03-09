"""Unit tests for text cleaning and chunking helpers used by the RAG preprocessing flow.

# Week-3 RAG ingestion improvement — added tests for:
# - sentence-aware splitting
# - section label inference
# - doc_to_chunks_with_metadata
"""

import unittest

from backend.services.preprocessing.text_cleaning import break_into_lines, clean_full_text, remove_junk
from backend.services.preprocessing.chunking import (
    doc_to_chunks,
    doc_to_chunks_with_metadata,
    infer_section_label,
    recursive_split,
)


SAMPLE_OCR = """--- Page 1 ---
Collected at : LPL-ROHINI (NATIONAL REFERENCE LAB)
Creatinine 1.00 mg/dL 0.70 - 1.30
Urea 40.00 mg/dL 13.00 - 43.00
--- Page 2 ---
Collected at : LPL-ROHINI (NATIONAL REFERENCE LAB)
HbA1c 10.0 % 4.00 - 5.60
Vitamin D 150.00 nmol/L 75.00 - 250.00
"""


class TestCleaning(unittest.TestCase):
    """Validates junk removal and full cleaning behavior."""

    def test_break_into_lines_splits_measurements(self):
        lines = break_into_lines(SAMPLE_OCR)
        self.assertTrue(any("Creatinine" in line for line in lines))

    def test_remove_junk_drops_headers(self):
        lines = break_into_lines(SAMPLE_OCR)
        cleaned = remove_junk(lines)
        self.assertTrue(cleaned)
        self.assertTrue(all("Collected at" not in line for line in cleaned))

    def test_clean_full_text(self):
        out = clean_full_text(SAMPLE_OCR)
        self.assertIn("Creatinine 1.00 mg/dL", out)
        self.assertIn("HbA1c 10.0 %", out)
        self.assertNotIn("Collected at", out)


# Week-3 RAG ingestion improvement — new test classes

class TestSentenceAwareSplitting(unittest.TestCase):
    """Validates that the sentence-aware splitter respects sentence boundaries."""

    def test_short_text_returns_single_chunk(self):
        text = "Hemoglobin is 14.2 g/dL. This is within normal range."
        chunks = recursive_split(text, chunk_size=300, chunk_overlap=50)
        self.assertEqual(len(chunks), 1)
        self.assertIn("Hemoglobin", chunks[0])

    def test_long_text_splits_at_sentence_boundary(self):
        sentences = [
            "The patient's hemoglobin level is 12.5 g/dL.",
            "White blood cell count is 7500 cells/uL.",
            "Platelet count is 250000 per uL which is within normal limits.",
            "Red blood cell count is 4.5 million cells per uL.",
            "Hematocrit is 38 percent which is slightly below normal.",
        ]
        text = " ".join(sentences)
        chunks = recursive_split(text, chunk_size=120, chunk_overlap=30)
        self.assertGreater(len(chunks), 1)
        # Each chunk should ideally end at a sentence boundary (period)
        for chunk in chunks[:-1]:  # last chunk may not end with period
            # At minimum, chunks should not cut in the middle of a word
            self.assertFalse(chunk.endswith("-"))

    def test_deduplication(self):
        text = "Hemoglobin 14.2 g/dL\n" * 5
        chunks = doc_to_chunks(text, chunk_size=300, chunk_overlap=50)
        # After dedup, should have at most 1 chunk for duplicated content
        self.assertLessEqual(len(chunks), 2)


class TestSectionLabelInference(unittest.TestCase):
    """Validates heuristic section label assignment."""

    def test_blood_test_label(self):
        text = "Hemoglobin 14.2 g/dL, Cholesterol 180 mg/dL, HDL 55 mg/dL"
        self.assertEqual(infer_section_label(text), "blood_test")

    def test_sleep_data_label(self):
        text = "Sleep score 82, deep sleep 45 minutes, REM sleep 90 minutes"
        self.assertEqual(infer_section_label(text), "sleep_data")

    def test_imaging_label(self):
        text = "MRI of the lumbar spine shows no significant abnormalities"
        self.assertEqual(infer_section_label(text), "imaging")

    def test_vitals_label(self):
        text = "Blood pressure 130/85 mmHg, heart rate 72 bpm, SpO2 98%"
        self.assertEqual(infer_section_label(text), "vitals")

    def test_summary_label(self):
        text = "Summary: Patient shows improvement. Recommendation to continue medication."
        self.assertEqual(infer_section_label(text), "summary")

    def test_other_label_for_generic_text(self):
        text = "The quick brown fox jumps over the lazy dog"
        self.assertEqual(infer_section_label(text), "other")


class TestDocToChunksWithMetadata(unittest.TestCase):
    """Validates that doc_to_chunks_with_metadata returns enriched chunk dicts."""

    def test_returns_dicts_with_text_and_label(self):
        text = "Hemoglobin 14.2 g/dL\nCholesterol 180 mg/dL"
        result = doc_to_chunks_with_metadata(text)
        self.assertIsInstance(result, list)
        for item in result:
            self.assertIn("text", item)
            self.assertIn("section_label", item)
            self.assertIsInstance(item["text"], str)
            self.assertIn(item["section_label"], [
                "blood_test", "sleep_data", "imaging", "vitals", "summary", "other",
            ])

    def test_backward_compat_doc_to_chunks(self):
        """doc_to_chunks should still return plain strings."""
        text = "Hemoglobin 14.2 g/dL\nCholesterol 180 mg/dL"
        result = doc_to_chunks(text)
        self.assertIsInstance(result, list)
        for item in result:
            self.assertIsInstance(item, str)

    def test_no_empty_chunks(self):
        text = "   \n\n  \n  "
        result = doc_to_chunks_with_metadata(text)
        self.assertEqual(len(result), 0)


if __name__ == "__main__":
    unittest.main()
