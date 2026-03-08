package com.vitalis.health.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

// ─────────────────────────────────────────────
// Report Upload Models
// ─────────────────────────────────────────────

@Serializable
data class ReportUploadResponse(
    val status: String,
    @SerialName("report_id")
    val reportId: String,
    val message: String
)

// ─────────────────────────────────────────────
// OCR Response
// POST /reports/ocr
// ─────────────────────────────────────────────

@Serializable
data class OcrReportResponse(
    val path: String,
    @SerialName("ocr_text")
    val ocrText: String,
    val confidence: Double,
    @SerialName("report_id")
    val reportId: String
)

// ─────────────────────────────────────────────
// Regex Extraction Response
// POST /reports/extract-labs
// ─────────────────────────────────────────────

@Serializable
data class ExtractLabsResponse(
    @SerialName("report_id")
    val reportId: String,
    val inserted: Int
)

// ─────────────────────────────────────────────
// Gemini Extraction Models
// POST /reports/extract-labs-gemini
// ─────────────────────────────────────────────

/** Mirrors the backend ExtractionLogEntry Pydantic model. */
@Serializable
data class GeminiExtractionLog(
    @SerialName("report_id")
    val reportId: String = "",
    @SerialName("total_tests_found")
    val totalTestsFound: Int = 0,
    @SerialName("tests_inserted")
    val testsInserted: Int = 0,
    @SerialName("tests_skipped")
    val testsSkipped: Int = 0,
    @SerialName("skipped_details")
    val skippedDetails: List<String> = emptyList(),
    val errors: List<String> = emptyList(),
    val warnings: List<String> = emptyList()
)

// ─────────────────────────────────────────────
// Full Pipeline Response
// POST /reports/process
// ─────────────────────────────────────────────

/** Regex extraction sub-result inside ProcessReportResponse. */
@Serializable
data class RegexExtractionResult(
    val inserted: Int = 0,
    val error: String? = null
)

/** Combined result of the full upload → OCR → extraction pipeline. */
@Serializable
data class ProcessReportResponse(
    @SerialName("report_id")
    val reportId: String,
    @SerialName("storage_path")
    val storagePath: String,
    @SerialName("public_url")
    val publicUrl: String,
    @SerialName("ocr_confidence")
    val ocrConfidence: Double = 0.0,
    @SerialName("ocr_text_preview")
    val ocrTextPreview: String = "",
    @SerialName("regex_extraction")
    val regexExtraction: RegexExtractionResult = RegexExtractionResult(),
    @SerialName("gemini_extraction")
    val geminiExtraction: GeminiExtractionLog? = null,
    @SerialName("gemini_error")
    val geminiError: String? = null
)
