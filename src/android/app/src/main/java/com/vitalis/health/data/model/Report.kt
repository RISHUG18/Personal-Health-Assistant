package com.vitalis.health.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

// ─────────────────────────────────────────────
// Report Upload Models
// POST /upload/report
// Backend returns: { message, structured_report_id, report_id, storage_path, file_url }
// ─────────────────────────────────────────────

@Serializable
data class ReportUploadResponse(
    val message: String = "",
    @SerialName("structured_report_id")
    val structuredReportId: String? = null,
    @SerialName("report_id")
    val reportId: String? = null,
    @SerialName("storage_path")
    val storagePath: String? = null,
    @SerialName("file_url")
    val fileUrl: String? = null,
    // Backward-compat fields for older payload variants.
    val path: String? = null,
    @SerialName("public_url")
    val publicUrl: String? = null,
)

@Serializable
data class ReportDownloadUrlResponse(
    @SerialName("signed_url")
    val signedUrl: String
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

// ─────────────────────────────────────────────
// Async Ingest Response
// POST /reports/ingest
// ─────────────────────────────────────────────

/** Response from async ingest endpoint (HTTP 202). */
@Serializable
data class IngestReportResponse(
    @SerialName("report_id")
    val reportId: String,
    @SerialName("storage_path")
    val storagePath: String = "",
    @SerialName("public_url")
    val publicUrl: String = "",
    @SerialName("processing_status")
    val processingStatus: String,  // "pending"
    val message: String
)

// ─────────────────────────────────────────────
// Report Status Response
// GET /reports/status/{report_id}
// ─────────────────────────────────────────────

/** Status tracking for async report processing. */
@Serializable
data class ReportStatusResponse(
    @SerialName("report_id")
    val reportId: String,
    @SerialName("source_file_name")
    val sourceFileName: String?,
    @SerialName("processing_status")
    val processingStatus: String,  // "pending" | "ocr_complete" | "done" | "failed" | "processing" | "validating" | "completed"
    @SerialName("processing_error")
    val processingError: String? = null,
    @SerialName("ocr_confidence")
    val ocrConfidence: Double? = null,
    @SerialName("lab_results_count")
    val labResultsCount: Int? = null
)

// ─────────────────────────────────────────────
// WebSocket Report Status Protocol
// WS /ws/report-status/{report_id}
// ─────────────────────────────────────────────

@Serializable
data class ReportRealtimeData(
    @SerialName("report_id")
    val reportId: String? = null,
    @SerialName("tests_detected")
    val testsDetected: Int? = null,
    @SerialName("alerts_triggered")
    val alertsTriggered: Int? = null,
    @SerialName("ocr_confidence")
    val ocrConfidence: Double? = null,
    @SerialName("cleanup_started")
    val cleanupStarted: Boolean? = null,
    @SerialName("cleanup_completed")
    val cleanupCompleted: Boolean? = null,
    @SerialName("report_deleted")
    val reportDeleted: Boolean? = null,
)

@Serializable
data class ReportRealtimeError(
    val reason: String? = null,
    val confidence: Double? = null,
)

@Serializable
data class ReportRealtimeStatusMessage(
    @SerialName("report_id")
    val reportId: String,
    val status: String, // "processing" | "validating" | "completed" | "failed"
    val data: ReportRealtimeData = ReportRealtimeData(),
    val error: ReportRealtimeError = ReportRealtimeError(),
)

// ─────────────────────────────────────────────
// Delete Report Response
// DELETE /api/reports/{report_id}
// ─────────────────────────────────────────────

@Serializable
data class DeleteReportResponse(
    @SerialName("report_id")
    val reportId: String,
    @SerialName("alerts_deleted")
    val alertsDeleted: Int = 0,
    @SerialName("deleted_at")
    val deletedAt: String? = null,
    val message: String = ""
)
