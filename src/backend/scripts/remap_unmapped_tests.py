"""Promote reviewed unmapped test names into the dictionary and reprocess them."""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Any

_SRC_DIR = Path(__file__).resolve().parents[2]
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from backend.config.supabase_client import get_supabase_client
from backend.extraction.normalizer import normalize_unit, parse_numeric_range
from backend.labs import CONFIDENCE_THRESHOLD, normalize_test_name, seed_reference_tables
from backend.labs.normalization import add_aliases_by_code


def _fetch_unmapped_tests() -> list[dict[str, Any]]:
    client = get_supabase_client()
    response = (
        client.table("unmapped_tests")
        .select(
            "id, report_id, source_lab_result_id, raw_test_name, normalized_input, "
            "suggested_code, suggested_name, confidence, value, text_value, unit, "
            "reference_range, extracted_from_page, notes, created_at"
        )
        .order("created_at")
        .execute()
    )
    return response.data or []


def _compute_abnormal_flag(value: Any, reference_range: str | None) -> bool | None:
    if value is None or not reference_range:
        return None
    low, high = parse_numeric_range(reference_range)
    if low is None or high is None:
        return None
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return None
    return numeric_value < low or numeric_value > high


def _load_mapping_file(path: Path) -> dict[str, str]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("Mapping file must be a JSON object of raw_test_name -> code")
    return {str(key): str(value).upper() for key, value in payload.items()}


def _build_alias_plan(
    rows: list[dict[str, Any]],
    *,
    mapping_file: Path | None,
    apply_suggested: bool,
    min_suggested_confidence: float,
) -> dict[str, list[str]]:
    alias_plan: dict[str, list[str]] = defaultdict(list)

    if mapping_file:
        explicit_map = _load_mapping_file(mapping_file)
        for row in rows:
            raw_name = (row.get("raw_test_name") or "").strip()
            if raw_name and raw_name in explicit_map:
                alias_plan[explicit_map[raw_name]].append(raw_name)

    if apply_suggested:
        for row in rows:
            raw_name = (row.get("raw_test_name") or "").strip()
            suggested_code = (row.get("suggested_code") or "").strip().upper()
            confidence = float(row.get("confidence") or 0.0)
            if raw_name and suggested_code and confidence >= min_suggested_confidence:
                alias_plan[suggested_code].append(raw_name)

    return {code: sorted(set(aliases), key=str.lower) for code, aliases in alias_plan.items()}


def _reprocess_unmapped_rows(rows: list[dict[str, Any]]) -> tuple[int, int]:
    client = get_supabase_client()
    inserted = 0
    still_unmapped = 0

    for row in rows:
        raw_name = (row.get("raw_test_name") or "").strip()
        normalized = normalize_test_name(raw_name)
        if not normalized["test_code"] or normalized["confidence"] < CONFIDENCE_THRESHOLD:
            still_unmapped += 1
            continue

        payload = {
            "id": row.get("source_lab_result_id") or str(uuid.uuid4()),
            "report_id": row["report_id"],
            "test_name": normalized["canonical_name"],
            "normalization_confidence": normalized["confidence"],
            "value": row.get("value"),
            "text_value": row.get("text_value"),
            "unit": normalize_unit(row.get("unit")),
            "reference_range": row.get("reference_range"),
            "abnormal_flag": _compute_abnormal_flag(row.get("value"), row.get("reference_range")),
            "extracted_from_page": row.get("extracted_from_page"),
        }
        client.table("lab_results").upsert(payload).execute()
        client.table("unmapped_tests").delete().eq("id", row["id"]).execute()
        inserted += 1

    return inserted, still_unmapped


def _export_review_template(rows: list[dict[str, Any]], destination: Path) -> None:
    review_payload = {}
    for row in rows:
        raw_name = (row.get("raw_test_name") or "").strip()
        if not raw_name:
            continue
        review_payload.setdefault(
            raw_name,
            {
                "suggested_code": row.get("suggested_code"),
                "suggested_name": row.get("suggested_name"),
                "confidence": row.get("confidence"),
            },
        )
    with destination.open("w", encoding="utf-8") as handle:
        json.dump(review_payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Update lab dictionary from unmapped_tests and reprocess rows"
    )
    parser.add_argument(
        "--mapping-file",
        type=Path,
        default=None,
        help="JSON object of raw_test_name -> test_code for reviewed mappings",
    )
    parser.add_argument(
        "--apply-suggested",
        action="store_true",
        help="Also add aliases from unmapped rows that already have suggested_code",
    )
    parser.add_argument(
        "--min-suggested-confidence",
        type=float,
        default=0.85,
        help="Minimum unmapped_tests.confidence required when using --apply-suggested",
    )
    parser.add_argument(
        "--export-review-template",
        type=Path,
        default=None,
        help="Write a review JSON template from current unmapped rows",
    )
    args = parser.parse_args()

    rows = _fetch_unmapped_tests()
    if not rows:
        print("No rows found in unmapped_tests.")
        return

    if args.export_review_template:
        _export_review_template(rows, args.export_review_template)
        print(f"Exported review template to {args.export_review_template}")

    alias_plan = _build_alias_plan(
        rows,
        mapping_file=args.mapping_file,
        apply_suggested=args.apply_suggested,
        min_suggested_confidence=args.min_suggested_confidence,
    )

    if not alias_plan:
        print("No alias updates selected. Provide --mapping-file or --apply-suggested.")
        return

    added_counts = add_aliases_by_code(alias_plan)
    client = get_supabase_client()
    seed_reference_tables(client)

    refreshed_rows = _fetch_unmapped_tests()
    inserted, still_unmapped = _reprocess_unmapped_rows(refreshed_rows)

    print(
        "Dictionary updated. "
        f"codes_changed={len(added_counts)} "
        f"aliases_added={sum(added_counts.values())} "
        f"reinserted={inserted} "
        f"still_unmapped={still_unmapped}"
    )


if __name__ == "__main__":
    main()
