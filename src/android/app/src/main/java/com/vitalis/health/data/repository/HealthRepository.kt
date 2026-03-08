package com.vitalis.health.data.repository

import com.vitalis.health.data.adapter.HealthApiAdapter
import com.vitalis.health.data.model.*
import com.vitalis.health.data.network.ApiResult

/**
 * Repository that mediates between ViewModels and the [HealthApiAdapter].
 *
 * Responsibilities:
 *  - Call the adapter
 *  - Apply any business / domain logic (caching, dedup, sorting)
 *  - Return clean [ApiResult] to ViewModels
 *
 * The UI layer MUST NOT call [HealthApiAdapter] directly.
 */
class HealthRepository(
    private val apiAdapter: HealthApiAdapter
) {

    // ── Dashboard ─────────────────────────────────────────

    /** Fetch the main dashboard summary for [userId]. */
    suspend fun getDashboard(userId: String): ApiResult<DashboardData> =
        apiAdapter.fetchDashboard(userId)

    // ── Alerts ────────────────────────────────────────────

    /**
     * Fetch all alerts for [userId], sorted with highest severity first.
     */
    suspend fun getAlerts(userId: String): ApiResult<List<Alert>> =
        apiAdapter.fetchAlerts(userId).map { alerts ->
            val order = mapOf("high" to 0, "medium" to 1, "low" to 2)
            alerts.sortedBy { order[it.severity] ?: 3 }
        }

    // ── RAG / AI Health Assistant ─────────────────────────

    /** Send a user query to the AI health assistant. */
    suspend fun queryAssistant(userId: String, query: String): ApiResult<RagData> =
        apiAdapter.queryHealthAssistant(userId, query)

    // ── Report Upload ─────────────────────────────────────

    /** Upload a medical report PDF on behalf of [userId]. */
    suspend fun uploadReport(
        userId: String,
        fileName: String,
        fileBytes: ByteArray
    ): ApiResult<ReportUploadResponse> =
        apiAdapter.uploadReport(userId, fileName, fileBytes)

    // ── Doctor — Patient List ─────────────────────────────

    /** Fetch the patient list for the given [doctorId]. */
    suspend fun getPatients(doctorId: String): ApiResult<List<Patient>> =
        apiAdapter.fetchPatients(doctorId)

    // ── Reports — OCR ─────────────────────────────────────

    /** Run OCR on a previously uploaded report at [storagePath]. */
    suspend fun ocrReport(userId: String, storagePath: String): ApiResult<OcrReportResponse> =
        apiAdapter.ocrReport(userId, storagePath)

    // ── Reports — Extract Labs (Regex) ─────────────────────

    /** Extract lab results using deterministic regex for [reportId]. */
    suspend fun extractLabs(reportId: String): ApiResult<ExtractLabsResponse> =
        apiAdapter.extractLabs(reportId)

    // ── Reports — Extract Labs (Gemini) ────────────────────

    /** Extract lab results using Gemini AI for [reportId] (idempotent). */
    suspend fun extractLabsGemini(reportId: String): ApiResult<GeminiExtractionLog> =
        apiAdapter.extractLabsGemini(reportId)

    // ── Reports — Full Pipeline ────────────────────────────

    /** Run the full pipeline (upload → OCR → extraction) for a report file. */
    suspend fun processReport(
        userId: String,
        fileName: String,
        fileBytes: ByteArray,
        useGemini: Boolean = false
    ): ApiResult<ProcessReportResponse> =
        apiAdapter.processReport(userId, fileName, fileBytes, useGemini)
}
