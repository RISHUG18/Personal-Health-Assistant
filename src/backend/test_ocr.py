#!/usr/bin/env python3
"""Test OCR on document-2.pdf using only the ocr/ module (no server, no Supabase, no Gemini).

Usage:
    cd src/backend
    PYTHONPATH=.. python test_ocr.py
"""

import os
import sys
import time

import cv2
import numpy as np
from pdf2image import convert_from_path

# ── Resolve paths ─────────────────────────────────────────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
PROJECT_ROOT = os.path.abspath(os.path.join(SRC_DIR, ".."))
PDF_PATH = os.path.join(PROJECT_ROOT, "docs", "document-2.pdf")

# Make sure `backend.ocr` is importable
sys.path.insert(0, SRC_DIR)

from backend.ocr.preprocessor import preprocess_image
from backend.ocr.ocr_engine import run_ocr

# ── Colours ───────────────────────────────────────────────────────────────────

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def banner(title: str) -> None:
    print(f"\n{CYAN}{BOLD}{'═' * 70}")
    print(f"  {title}")
    print(f"{'═' * 70}{RESET}\n")


def main() -> None:
    banner("OCR TEST — document-2.pdf")

    # ── Check PDF exists ──────────────────────────────────────────────────
    if not os.path.exists(PDF_PATH):
        print(f"{RED}❌ PDF not found: {PDF_PATH}{RESET}")
        sys.exit(1)

    file_size = os.path.getsize(PDF_PATH)
    print(f"  {YELLOW}ℹ  PDF path:  {PDF_PATH}{RESET}")
    print(f"  {YELLOW}ℹ  File size: {file_size:,} bytes{RESET}")

    # ── Convert PDF pages to images ───────────────────────────────────────
    banner("STEP 1: Converting PDF to images (pdf2image)")
    start = time.time()
    pages = convert_from_path(PDF_PATH)
    elapsed = time.time() - start
    print(f"  {GREEN}✅ Converted {len(pages)} page(s) in {elapsed:.2f}s{RESET}")

    # ── Process each page ─────────────────────────────────────────────────
    full_text = ""
    total_confidence = 0.0

    for i, pil_image in enumerate(pages):
        page_num = i + 1
        banner(f"STEP 2.{page_num}: Processing Page {page_num}/{len(pages)}")

        # Convert PIL → OpenCV BGR
        open_cv_image = np.array(pil_image)
        image_bgr = open_cv_image[:, :, ::-1].copy()
        print(f"  Image size: {image_bgr.shape[1]}x{image_bgr.shape[0]} pixels")

        # Preprocess
        print(f"  Running preprocessor (grayscale → denoise → threshold → deskew)...")
        start = time.time()
        processed = preprocess_image(image_bgr)
        preprocess_time = time.time() - start
        print(f"  {GREEN}✅ Preprocessing done in {preprocess_time:.2f}s{RESET}")

        # OCR
        print(f"  Running Tesseract OCR...")
        start = time.time()
        text, confidence = run_ocr(processed)
        ocr_time = time.time() - start
        print(f"  {GREEN}✅ OCR done in {ocr_time:.2f}s — confidence: {confidence:.1f}%{RESET}")

        # Append
        page_header = f"\n--- Page {page_num} ---\n"
        full_text += page_header + text
        total_confidence += confidence

        # Print OCR text for this page
        print(f"\n  {BOLD}── OCR Text (Page {page_num}) {'─' * 40}{RESET}")
        if text.strip():
            # Print with line wrapping for readability
            words = text.split()
            line = "  "
            for word in words:
                if len(line) + len(word) + 1 > 100:
                    print(line)
                    line = "  " + word
                else:
                    line += " " + word if line.strip() else "  " + word
            if line.strip():
                print(line)
        else:
            print(f"  {RED}(empty — no text detected){RESET}")
        print()

    # ── Summary ───────────────────────────────────────────────────────────
    avg_confidence = total_confidence / len(pages) if pages else 0.0

    banner("SUMMARY")
    print(f"  Pages processed:     {len(pages)}")
    print(f"  Total characters:    {len(full_text):,}")
    print(f"  Total words:         {len(full_text.split()):,}")
    print(f"  Average confidence:  {avg_confidence:.1f}%")
    print()

    if avg_confidence >= 80:
        print(f"  {GREEN}{BOLD}✅ OCR quality: GOOD ({avg_confidence:.1f}%){RESET}")
    elif avg_confidence >= 50:
        print(f"  {YELLOW}{BOLD}⚠️  OCR quality: MODERATE ({avg_confidence:.1f}%){RESET}")
    else:
        print(f"  {RED}{BOLD}❌ OCR quality: POOR ({avg_confidence:.1f}%){RESET}")

    # ── Full combined text ────────────────────────────────────────────────
    banner("FULL OCR TEXT (all pages combined)")
    print(full_text.strip())
    print()
    print(f"  {CYAN}{'─' * 70}{RESET}")
    print(f"  {GREEN}✅ OCR test complete.{RESET}")
    print()


if __name__ == "__main__":
    main()
