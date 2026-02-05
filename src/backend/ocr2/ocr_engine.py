import numpy as np
import pytesseract

def run_ocr(image: np.ndarray) -> tuple[str, float]:
    """
    Run Tesseract OCR on an image.
    Returns: (text, confidence)
    """
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    text = " ".join(word for word in data.get("text", []) if word).strip()

    confidences = []
    for conf in data.get("conf", []):
        try:
            value = float(conf)
            if value >= 0:
                confidences.append(value)
        except (TypeError, ValueError):
            continue

    avg_confidence = float(sum(confidences) / len(confidences)) if confidences else 0.0
    return text, avg_confidence
