"""Unit tests for text cleaning helpers used by the RAG preprocessing flow."""

import unittest

from backend.services.preprocessing.text_cleaning import break_into_lines, clean_full_text, remove_junk


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


if __name__ == "__main__":
    unittest.main()
