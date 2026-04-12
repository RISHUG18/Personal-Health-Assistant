"""Master lab-test dictionary loading and normalization."""

from __future__ import annotations

import json
import threading
import re
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path
from typing import Iterable

from supabase import Client

try:
    from rapidfuzz import fuzz, process
except ModuleNotFoundError:  # pragma: no cover - exercised only in minimal local envs
    fuzz = None
    process = None

CONFIDENCE_THRESHOLD = 0.85
_DATA_CANDIDATES = (
    Path(__file__).resolve().parents[1] / "data" / "lab_test_dictionary.json",
    Path(__file__).resolve().parents[1] / "rules" / "lab_test_dictionary.json",
)
_DATA_PATH = next((path for path in _DATA_CANDIDATES if path.exists()), _DATA_CANDIDATES[0])
_REFERENCE_TABLES_SEEDED = False
_REFERENCE_TABLES_LOCK = threading.Lock()
_UNIT_PATTERN = re.compile(
    r"\b(?:mg\/dl|mg\/l|g\/dl|g\/l|mmol\/l|umol\/l|µmol\/l|ng\/ml|ng\/dl|pg\/ml|"
    r"iu\/l|u\/l|miu\/ml|µiu\/ml|meq\/l|10\^3\/ul|10\^6\/ul|x10\^3\/ul|x10\^6\/ul|"
    r"cells\/ul|\/ul|\/µl|mm\/hr|mg\/24hr|ml\/min\/1\.73m2|ml\/min|ratio|%)\b",
    re.IGNORECASE,
)
_PUNCT_PATTERN = re.compile(r"[^a-z0-9\s]")
_SPACE_PATTERN = re.compile(r"\s+")


def preprocess_test_text(raw_text: str) -> str:
    """Normalize raw test labels for deterministic matching."""
    if not raw_text:
        return ""
    text = raw_text.lower()
    text = _UNIT_PATTERN.sub(" ", text)
    text = text.replace("µ", "u")
    text = _PUNCT_PATTERN.sub(" ", text)
    text = _SPACE_PATTERN.sub(" ", text).strip()
    return text


def _compact(text: str) -> str:
    return text.replace(" ", "")


def _abbreviation_variants(alias: str) -> set[str]:
    tokens = re.findall(r"[a-z0-9]+", alias.lower())
    joined = "".join(tokens)
    if not joined or len(joined) > 8:
        return set()
    if not any(char.isalpha() for char in joined):
        return set()

    chars = list(joined)
    variants = {
        joined,
        " ".join(chars),
        ".".join(chars),
        ". ".join(chars),
        "-".join(chars),
        f"{joined}.",
        f"{joined}:",
    }
    return variants


def _ocr_variants(alias: str) -> set[str]:
    alias_lower = alias.lower()
    variants = {
        alias_lower,
        alias_lower.replace("-", " "),
        alias_lower.replace("/", " "),
        alias_lower.replace("(", " ").replace(")", " "),
        alias_lower.replace("%", " percent "),
    }
    if "a1c" in alias_lower:
        variants.add(alias_lower.replace("a1c", "aic"))
    if "haemoglobin" in alias_lower:
        variants.add(alias_lower.replace("haemoglobin", "hemoglobin"))
    if "hemoglobin" in alias_lower:
        variants.add(alias_lower.replace("hemoglobin", "haemoglobin"))
    return variants


def _expanded_aliases(code: str, canonical_name: str, aliases: Iterable[str]) -> set[str]:
    seed_aliases = {code, canonical_name, *aliases}
    expanded: set[str] = set()
    for alias in seed_aliases:
        if not alias:
            continue
        expanded.add(alias)
        expanded.update(_ocr_variants(alias))
        expanded.update(_abbreviation_variants(alias))
    return expanded


def _load_dictionary() -> list[dict]:
    with _DATA_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_dictionary(tests: list[dict]) -> None:
    """Persist the lab dictionary and clear cached indexes."""
    _DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _DATA_PATH.open("w", encoding="utf-8") as handle:
        json.dump(tests, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    reset_catalog_cache()


def reset_catalog_cache() -> None:
    """Clear cached dictionary indexes after on-disk updates."""
    get_catalog.cache_clear()


@lru_cache(maxsize=1)
def get_catalog() -> dict:
    """Load the dictionary and build lookup indexes."""
    tests = _load_dictionary()
    by_code: dict[str, dict] = {}
    canonical_map: dict[str, dict] = {}
    alias_map: dict[str, dict] = {}
    compact_map: dict[str, dict] = {}
    fuzzy_choices: dict[str, dict] = {}

    for item in tests:
        code = item["code"].strip().upper()
        enriched = {
            **item,
            "code": code,
            "expanded_aliases": sorted(
                _expanded_aliases(code=code, canonical_name=item["canonical_name"], aliases=item["aliases"])
            ),
        }
        by_code[code] = enriched

        canonical_key = preprocess_test_text(item["canonical_name"])
        if canonical_key in canonical_map and canonical_map[canonical_key]["code"] != code:
            raise ValueError(f"Duplicate canonical key detected: {item['canonical_name']}")
        canonical_map[canonical_key] = enriched
        compact_map[_compact(canonical_key)] = enriched

        for alias in enriched["expanded_aliases"]:
            alias_key = preprocess_test_text(alias)
            if not alias_key:
                continue
            existing = alias_map.get(alias_key)
            if existing and existing["code"] != code:
                raise ValueError(
                    f"Duplicate alias '{alias}' normalizes to '{alias_key}' for "
                    f"{existing['code']} and {code}"
                )
            alias_map[alias_key] = enriched
            compact_key = _compact(alias_key)
            compact_existing = compact_map.get(compact_key)
            if compact_existing and compact_existing["code"] != code:
                raise ValueError(
                    f"Duplicate compact alias '{alias}' maps to both "
                    f"{compact_existing['code']} and {code}"
                )
            compact_map[compact_key] = enriched
            fuzzy_choices.setdefault(alias_key, enriched)

    return {
        "tests": tests,
        "by_code": by_code,
        "canonical_map": canonical_map,
        "alias_map": alias_map,
        "compact_map": compact_map,
        "fuzzy_choices": fuzzy_choices,
    }


def get_matchable_labels() -> list[str]:
    """Return the labels that should be recognized in OCR extraction."""
    catalog = get_catalog()
    labels = []
    for item in catalog["by_code"].values():
        labels.append(item["canonical_name"])
        labels.extend(item["aliases"])
    return sorted(set(labels), key=len, reverse=True)


def normalize_test_name(raw_text: str) -> dict:
    """Normalize a raw lab-test label to the master dictionary."""
    preprocessed = preprocess_test_text(raw_text)
    if not preprocessed:
        return {
            "test_code": None,
            "canonical_name": None,
            "confidence": 0.0,
        }

    catalog = get_catalog()

    exact = catalog["canonical_map"].get(preprocessed)
    if exact:
        return {
            "test_code": exact["code"],
            "canonical_name": exact["canonical_name"],
            "confidence": 1.0,
        }

    alias = catalog["alias_map"].get(preprocessed)
    if alias:
        return {
            "test_code": alias["code"],
            "canonical_name": alias["canonical_name"],
            "confidence": 0.96,
        }

    compact = catalog["compact_map"].get(_compact(preprocessed))
    if compact:
        return {
            "test_code": compact["code"],
            "canonical_name": compact["canonical_name"],
            "confidence": 0.93,
        }

    if process is not None and fuzz is not None:
        best = process.extractOne(
            preprocessed,
            list(catalog["fuzzy_choices"].keys()),
            scorer=fuzz.WRatio,
            score_cutoff=int(CONFIDENCE_THRESHOLD * 100),
        )
        if best:
            matched_key, score, _ = best
            item = catalog["fuzzy_choices"][matched_key]
            return {
                "test_code": item["code"],
                "canonical_name": item["canonical_name"],
                "confidence": round(score / 100.0, 3),
            }
    else:
        best_key = None
        best_score = 0.0
        for key in catalog["fuzzy_choices"]:
            score = SequenceMatcher(None, preprocessed, key).ratio() * 100
            if score > best_score:
                best_score = score
                best_key = key
        if best_key and best_score >= CONFIDENCE_THRESHOLD * 100:
            item = catalog["fuzzy_choices"][best_key]
            return {
                "test_code": item["code"],
                "canonical_name": item["canonical_name"],
                "confidence": round(best_score / 100.0, 3),
            }

    return {
        "test_code": None,
        "canonical_name": None,
        "confidence": 0.0,
    }


def seed_reference_tables(client: Client) -> None:
    """Populate tests_master, test_aliases, and test_units from the JSON dictionary."""
    catalog = get_catalog()
    tests_payload = [
        {
            "code": item["code"],
            "canonical_name": item["canonical_name"],
            "category": item["category"],
        }
        for item in catalog["by_code"].values()
    ]
    alias_payload = []
    unit_payload = []
    for item in catalog["by_code"].values():
        alias_payload.extend(
            {"alias": alias, "code": item["code"]}
            for alias in item["expanded_aliases"]
        )
        unit_payload.extend(
            {"code": item["code"], "unit": unit}
            for unit in item["units"]
        )

    client.table("tests_master").upsert(tests_payload).execute()
    client.table("test_aliases").upsert(alias_payload).execute()
    client.table("test_units").upsert(unit_payload).execute()


def ensure_reference_tables_seeded(client: Client) -> None:
    """Best-effort one-time seeding so ingestion works on fresh deployments."""
    global _REFERENCE_TABLES_SEEDED
    if _REFERENCE_TABLES_SEEDED:
        return
    with _REFERENCE_TABLES_LOCK:
        if _REFERENCE_TABLES_SEEDED:
            return
        seed_reference_tables(client)
        _REFERENCE_TABLES_SEEDED = True


def add_aliases_by_code(alias_map: dict[str, list[str]]) -> dict[str, int]:
    """Append aliases to existing tests, validating collisions before saving."""
    tests = _load_dictionary()
    by_code = {item["code"].strip().upper(): item for item in tests}
    added_counts: dict[str, int] = {}

    for code, aliases in alias_map.items():
        normalized_code = code.strip().upper()
        if normalized_code not in by_code:
            raise ValueError(f"Unknown test code: {normalized_code}")
        existing_aliases = set(by_code[normalized_code]["aliases"])
        additions = []
        for alias in aliases:
            cleaned = alias.strip()
            if cleaned and cleaned not in existing_aliases:
                existing_aliases.add(cleaned)
                additions.append(cleaned)
        if additions:
            by_code[normalized_code]["aliases"] = sorted(existing_aliases, key=str.lower)
            added_counts[normalized_code] = len(additions)

    original_content = json.dumps(tests, ensure_ascii=False, indent=2) + "\n"
    try:
        save_dictionary(tests)
        get_catalog()
    except Exception:
        _DATA_PATH.write_text(original_content, encoding="utf-8")
        reset_catalog_cache()
        raise

    return added_counts
