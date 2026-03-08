"""Pydantic models for Gemini extraction input/output."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Gemini extraction output models ──────────────────────────────────────────


class ExtractedLabResult(BaseModel):
    """A single lab test result extracted by Gemini."""

    test_name: str = Field(..., description="Full name of the lab test")
    value: Optional[float] = Field(
        None, description="Numeric value exactly as reported — never rounded"
    )
    value_string: Optional[str] = Field(
        None,
        description="Original string representation (useful for non-numeric results like Positive/Negative)",
    )
    unit: Optional[str] = Field(None, description="Measurement unit as reported")
    reference_range: Optional[str] = Field(
        None, description="Reference/normal range as printed on the report"
    )
    is_abnormal: Optional[bool] = Field(
        None,
        description="True if flagged abnormal by the report, False if normal, None if uncertain",
    )
    page_number: Optional[int] = Field(
        None, description="Page number where this result appears"
    )


class ExtractedReportMetadata(BaseModel):
    """Report-level metadata extracted by Gemini."""

    report_date: Optional[str] = Field(
        None, description="Report date in YYYY-MM-DD format"
    )
    report_type: Optional[str] = Field(
        None, description="Type of report (e.g. Complete Blood Count, Lipid Panel)"
    )
    patient_name: Optional[str] = Field(
        None, description="Patient name if visible in the report"
    )
    lab_name: Optional[str] = Field(
        None, description="Laboratory name if visible in the report"
    )


class GeminiExtractionResponse(BaseModel):
    """Complete structured extraction result from Gemini."""

    metadata: ExtractedReportMetadata = Field(
        default_factory=ExtractedReportMetadata
    )
    lab_results: List[ExtractedLabResult] = Field(default_factory=list)
    extraction_notes: Optional[str] = Field(
        None, description="Notes about extraction quality or issues encountered"
    )


# ── Extraction log model ─────────────────────────────────────────────────────


class ExtractionLogEntry(BaseModel):
    """Structured log of what happened during one extraction run."""

    report_id: str
    total_tests_found: int = 0
    tests_inserted: int = 0
    tests_skipped: int = 0
    skipped_details: List[str] = Field(default_factory=list)
    metadata_updates: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
