'''
This file is just for developer safety testing/automated diagnostics
'''

import unittest
from text_cleaning import split_pages_from_blob, remove_repeated_headers, clean_text_single, clean_full_text

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
    def test_split_pages(self):
        pages = split_pages_from_blob(SAMPLE_OCR)
        self.assertTrue(len(pages) >= 2)
        self.assertIn("Creatinine", pages[0])

    def test_remove_repeated_headers(self):
        pages = split_pages_from_blob(SAMPLE_OCR)
        cleaned = remove_repeated_headers(pages, threshold=0.4)
        # header "Collected at" appears on both pages and should be removed
        for p in cleaned:
            self.assertNotIn("Collected at", p)

    def test_clean_text_single(self):
        page = "Collected at : LPL-ROHINI\nCreatinine 1.00 mg/dL 0.70 - 1.30\nSome narrative text here"
        cleaned = clean_text_single(page)
        self.assertIn("Creatinine 1.00 mg/dL", cleaned)
        self.assertIn("Some narrative text", cleaned)
        self.assertNotIn("Collected at", cleaned)

    def test_clean_full_text(self):
        out = clean_full_text(SAMPLE_OCR)
        # should contain the lab values but not the "Collected at" header
        self.assertIn("Creatinine 1.00 mg/dL", out)
        self.assertIn("HbA1c 10.0 %", out)
        self.assertNotIn("Collected at", out)

if __name__ == "__main__":
    unittest.main()
