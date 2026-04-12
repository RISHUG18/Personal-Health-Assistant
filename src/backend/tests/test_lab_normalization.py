from backend.labs import normalize_test_name


def test_exact_match_returns_full_confidence() -> None:
    result = normalize_test_name("Hemoglobin")
    assert result["test_code"] == "HB"
    assert result["canonical_name"] == "Hemoglobin"
    assert result["confidence"] == 1.0


def test_alias_with_ocr_noise_is_normalized() -> None:
    result = normalize_test_name("H.B (g/dl)")
    assert result["test_code"] == "HB"
    assert result["canonical_name"] == "Hemoglobin"
    assert result["confidence"] >= 0.93


def test_fuzzy_matching_handles_slight_ocr_error() -> None:
    result = normalize_test_name("potasssium")
    assert result["test_code"] == "K"
    assert result["canonical_name"] == "Potassium"
    assert result["confidence"] >= 0.85
