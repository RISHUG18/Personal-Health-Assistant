"""Backfill normalized lab identifiers into existing lab_results rows."""

from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path
from typing import Any

_SRC_DIR = Path(__file__).resolve().parents[2]
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from backend.config.supabase_client import get_supabase_client
from backend.extraction.normalizer import normalize_unit
from backend.labs import CONFIDENCE_THRESHOLD, normalize_test_name, seed_reference_tables


def _fetch_lab_rows(limit: int) -> list[dict[str, Any]]:
    client = get_supabase_client()
    response = (
        client.table("lab_results")
        .select(
            "id, report_id, test_name, value, text_value, unit, reference_range, "
            "abnormal_flag, extracted_from_page, normalization_confidence"
        )
        .is_("normalization_confidence", "null")
        .order("id")
        .limit(limit)
        .execute()
    )
    return response.data or []


def migrate(batch_size: int = 500) -> None:
    client = get_supabase_client()
    seed_reference_tables(client)

    migrated = 0
    unmapped = 0

    while True:
        rows = _fetch_lab_rows(limit=batch_size)
        if not rows:
            break

        for row in rows:
            raw_name = (row.get("test_name") or "").strip()

            normalized = normalize_test_name(raw_name)
            normalized_unit = normalize_unit(row.get("unit"))

            if normalized["test_code"] and normalized["confidence"] >= CONFIDENCE_THRESHOLD:
                client.table("lab_results").update(
                    {
                        "test_name": normalized["canonical_name"],
                        "normalization_confidence": normalized["confidence"],
                        "unit": normalized_unit,
                    }
                ).eq("id", row["id"]).execute()
                migrated += 1
                continue

            payload = {
                "id": str(uuid.uuid4()),
                "report_id": row["report_id"],
                "source_lab_result_id": row["id"],
                "raw_test_name": raw_name or "<missing>",
                "normalized_input": raw_name,
                "suggested_code": normalized["test_code"],
                "suggested_name": normalized["canonical_name"],
                "confidence": normalized["confidence"],
                "value": row.get("value"),
                "text_value": row.get("text_value"),
                "unit": normalized_unit,
                "reference_range": row.get("reference_range"),
                "extracted_from_page": row.get("extracted_from_page"),
                "notes": "Moved during lab name normalization migration",
            }
            client.table("unmapped_tests").insert(payload).execute()
            client.table("lab_results").delete().eq("id", row["id"]).execute()
            unmapped += 1

    print(
        f"Migration complete. migrated={migrated} unmapped={unmapped} "
        f"threshold={CONFIDENCE_THRESHOLD:.2f}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize existing lab_results rows")
    parser.add_argument("--batch-size", type=int, default=500)
    args = parser.parse_args()
    migrate(batch_size=args.batch_size)


if __name__ == "__main__":
    main()
