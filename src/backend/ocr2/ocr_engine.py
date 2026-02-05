from PIL import Image
import numpy as np
import torch
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

_PROCESSOR = None
_MODEL = None
_DEVICE = None

def _get_model():
    global _PROCESSOR, _MODEL, _DEVICE
    if _PROCESSOR is None or _MODEL is None or _DEVICE is None:
        _DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
        model_name = "microsoft/trocr-base-handwritten"
        _PROCESSOR = TrOCRProcessor.from_pretrained(model_name)
        _MODEL = VisionEncoderDecoderModel.from_pretrained(model_name).to(_DEVICE)
        _MODEL.eval()
    return _PROCESSOR, _MODEL, _DEVICE

def _bgr_to_pil(image: np.ndarray) -> Image.Image:
    if image.ndim == 2:
        return Image.fromarray(image).convert("RGB")
    if image.shape[2] == 3:
        rgb = image[:, :, ::-1]
        return Image.fromarray(rgb)
    return Image.fromarray(image).convert("RGB")

def _estimate_confidence(output_scores, sequences) -> float:
    if not output_scores:
        return 0.0
    token_scores = []
    for step_scores in output_scores:
        probs = torch.softmax(step_scores, dim=-1)
        max_probs, _ = probs.max(dim=-1)
        token_scores.append(max_probs)
    if not token_scores:
        return 0.0
    stacked = torch.stack(token_scores, dim=0)
    if sequences is not None:
        seq_len = sequences.shape[1]
        stacked = stacked[:seq_len]
    return float(stacked.mean().item() * 100.0)

def run_ocr(image: np.ndarray) -> tuple[str, float]:
    """
    Run TrOCR on an image.
    Returns: (text, confidence)
    """
    processor, model, device = _get_model()
    pil_image = _bgr_to_pil(image)

    inputs = processor(images=pil_image, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=256,
            return_dict_in_generate=True,
            output_scores=True,
        )

    text = processor.batch_decode(outputs.sequences, skip_special_tokens=True)[0]
    confidence = _estimate_confidence(outputs.scores, outputs.sequences)
    return text, confidence
