"""Image preprocessing pipeline for OCR.

Applies grayscale conversion, denoising, adaptive thresholding, and deskewing
to improve Tesseract OCR accuracy on scanned medical report images.
"""

import cv2
import numpy as np


def preprocess_image(image: np.ndarray) -> np.ndarray:
    """Preprocess an image for better OCR accuracy.

    Pipeline: Grayscale → Denoise → Adaptive Threshold → Deskew.

    Parameters
    ----------
    image:
        BGR colour image as a NumPy array (OpenCV format).

    Returns
    -------
    np.ndarray
        Binary (black-and-white), deskewed image ready for OCR.
    """
    # 1. Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # 2. Denoise
    denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)

    # 3. Adaptive thresholding → binary image
    binary = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )

    # 4. Deskew
    coords = np.column_stack(np.where(binary > 0))
    if coords.shape[0] == 0:
        return binary

    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    (h, w) = binary.shape[:2]
    center = (w // 2, h // 2)
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        binary, rotation_matrix, (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )

    return rotated
