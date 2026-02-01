import pytesseract
from PIL import Image
import numpy as np

def run_ocr(image: np.ndarray) -> tuple[str, float]:
    """
    Run Tesseract OCR on an image.
    Returns: (text, confidence)
    """
    # Convert numpy array back to PIL image for pytesseract
    pil_image = Image.fromarray(image)
    
    # Get detailed data including confidence
    data = pytesseract.image_to_data(pil_image, output_type=pytesseract.Output.DICT)
    text = pytesseract.image_to_string(pil_image)
    
    # Calculate average confidence of non-empty words
    confidences = [int(conf) for conf in data['conf'] if conf != '-1']
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    
    return text, avg_confidence
