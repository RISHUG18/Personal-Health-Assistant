"""Tesseract OCR engine wrapper.

Runs Tesseract on a preprocessed image and returns the recognised text
together with an average per-word confidence score.
"""

import numpy as np
import pytesseract


def run_ocr(image: np.ndarray) -> tuple[str, float]:
    """Run Tesseract OCR on a preprocessed image.

    Parameters
    ----------
    image:
        Preprocessed (binary, deskewed) image as a NumPy array.

    Returns
    -------
    tuple[str, float]
        ``(extracted_text, average_confidence)`` where confidence is 0–100.
    """
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    text = " ".join(word for word in data.get("text", []) if word.strip()).strip()

    confidences: list[float] = []
    for conf in data.get("conf", []):
        try:
            value = float(conf)
            if value >= 0:
                confidences.append(value)
        except (TypeError, ValueError):
            continue

    avg_confidence = (
        float(sum(confidences) / len(confidences)) if confidences else 0.0
    )
    return text, avg_confidence
