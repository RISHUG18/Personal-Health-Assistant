package com.vitalis.health.data.adapter

import com.vitalis.health.data.model.*
import com.vitalis.health.data.network.ApiResult

/**
 * Contract for the API adapter layer.
 *
 * Every method returns [ApiResult] — UI code never touches raw Retrofit
 * responses, HTTP codes, or exceptions.
 */
interface HealthApiAdapter {

    /** Fetch the main dashboard summary for [userId]. */
    suspend fun fetchDashboard(userId: String): ApiResult<DashboardData>

    /** Fetch all health alerts for [userId]. */
    suspend fun fetchAlerts(userId: String): ApiResult<List<Alert>>

    /** Send a natural-language query to the AI health assistant. */
    suspend fun queryHealthAssistant(userId: String, query: String): ApiResult<RagData>

    /** Upload a medical report PDF. */
    suspend fun uploadReport(userId: String, fileName: String, fileBytes: ByteArray): ApiResult<ReportUploadResponse>

    /** Fetch the doctor's patient list. */
    suspend fun fetchPatients(doctorId: String): ApiResult<List<Patient>>

    /** Run OCR on a previously uploaded report at [storagePath]. */
    suspend fun ocrReport(userId: String, storagePath: String): ApiResult<OcrReportResponse>

    /** Extract lab results from OCR text using deterministic regex. */
    suspend fun extractLabs(reportId: String): ApiResult<ExtractLabsResponse>

    /** Extract lab results from OCR text using Gemini AI (idempotent). */
    suspend fun extractLabsGemini(reportId: String): ApiResult<GeminiExtractionLog>

    /** Run the full pipeline (upload → OCR → extraction) for a report file. */
    suspend fun processReport(
        userId: String,
        fileName: String,
        fileBytes: ByteArray,
        useGemini: Boolean = false
    ): ApiResult<ProcessReportResponse>
}
