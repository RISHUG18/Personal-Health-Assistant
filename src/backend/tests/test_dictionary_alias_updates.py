import shutil
from pathlib import Path

from backend.labs import normalize_test_name
from backend.labs import normalization as normalization_module
from backend.labs.normalization import add_aliases_by_code, reset_catalog_cache


def test_add_aliases_by_code_updates_dictionary(tmp_path) -> None:
    source_path = Path(normalization_module._DATA_PATH)
    temp_path = tmp_path / "lab_test_dictionary.json"
    shutil.copyfile(source_path, temp_path)

    original_path = normalization_module._DATA_PATH
    normalization_module._DATA_PATH = temp_path
    reset_catalog_cache()

    try:
        counts = add_aliases_by_code({"HB": ["haemoglobin reading"]})
        assert counts["HB"] >= 1

        result = normalize_test_name("haemoglobin reading")
        assert result["test_code"] == "HB"
        assert result["canonical_name"] == "Hemoglobin"
    finally:
        normalization_module._DATA_PATH = original_path
        reset_catalog_cache()
