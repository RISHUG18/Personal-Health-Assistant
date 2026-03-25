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

    // ── Authentication ────────────────────────────────────

    /** Login with email and password. */
    suspend fun login(email: String, password: String): ApiResult<AuthResponse>

    /** Register a new user account. */
    suspend fun register(
        email: String,
        password: String,
        fullName: String,
        role: String = "patient"
    ): ApiResult<AuthResponse>

    // ── User Profile ──────────────────────────────────────

    /** Fetch the user profile for [userId]. */
    suspend fun fetchUserProfile(userId: String): ApiResult<UserProfile>

    /** Fetch all health alerts for [userId] with evidence. */
    suspend fun fetchAlerts(userId: String): ApiResult<List<Alert>>

    /** Fetch environment data (AQI/weather) for given coordinates. */
    suspend fun fetchEnvironment(
        userId: String,
        latitude: Double,
        longitude: Double,
        city: String? = null
    ): ApiResult<EnvironmentData>

    /** Fetch lab results for a specific report. */
    suspend fun fetchLabResults(reportId: String): ApiResult<LabResultsResponse>

    /** Fetch report history for the authenticated user. */
    suspend fun fetchUserReports(limit: Int = 20, offset: Int = 0): ApiResult<List<ReportSummary>>

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

    /** Async upload → queue background processing (recommended). Returns immediately. */
    suspend fun ingestReport(
        userId: String,
        userName: String?,
        fileName: String,
        fileBytes: ByteArray
    ): ApiResult<IngestReportResponse>

    /** Poll the processing status of an async report upload. */
    suspend fun getReportStatus(reportId: String): ApiResult<ReportStatusResponse>
}
