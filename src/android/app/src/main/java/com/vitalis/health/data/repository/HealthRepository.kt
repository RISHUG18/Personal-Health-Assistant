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

    // ── Authentication ────────────────────────────────────

    /** Login with email and password, returns auth tokens on success. */
    suspend fun login(email: String, password: String): ApiResult<AuthResponse> =
        apiAdapter.login(email, password)

    /** Register a new user account, returns auth tokens on success. */
    suspend fun register(
        email: String,
        password: String,
        fullName: String,
        dateOfBirth: String,
        gender: String? = null,
        heightCm: Double? = null,
        weightKg: Double? = null,
        role: String = "patient"
    ): ApiResult<AuthResponse> =
        apiAdapter.register(
            email = email,
            password = password,
            fullName = fullName,
            dateOfBirth = dateOfBirth,
            gender = gender,
            heightCm = heightCm,
            weightKg = weightKg,
            role = role,
        )

    // ── User Profile ─────────────────────────────────────────

    /** Fetch the user profile for [userId]. */
    suspend fun getUserProfile(userId: String): ApiResult<UserProfile> =
        apiAdapter.fetchUserProfile(userId)

    /** Update the user profile for [userId]. */
    suspend fun updateUser(userId: String, request: UserUpdateRequest): ApiResult<UserProfile> =
        apiAdapter.updateUserProfile(userId, request)

    /** Delete the user account for [userId]. Cascade deletes all associated data. */
    suspend fun deleteUser(userId: String): ApiResult<Unit> =
        apiAdapter.deleteUser(userId)

    /** Fetch a user profile by email address. */
    suspend fun getUserByEmail(email: String): ApiResult<UserProfile> =
        apiAdapter.getUserByEmail(email)

    // ── Alerts ────────────────────────────────────────────

    /**
     * Fetch all alerts for [userId], sorted with highest severity first.
     */
    suspend fun getAlerts(userId: String): ApiResult<List<Alert>> =
        apiAdapter.fetchAlerts(userId).map { alerts ->
            val order = mapOf("high" to 0, "medium" to 1, "low" to 2)
            alerts.sortedBy { order[it.severity] ?: 3 }
        }

    // ── Environment (AQI/Weather) ─────────────────────────

    /** Fetch environment data (AQI, weather) for the given coordinates. */
    suspend fun getEnvironment(
        userId: String,
        latitude: Double,
        longitude: Double,
        city: String? = null
    ): ApiResult<EnvironmentData> =
        apiAdapter.fetchEnvironment(userId, latitude, longitude, city)

    // ── Lab Results ───────────────────────────────────────

    /** Fetch lab results for a specific report. */
    suspend fun getLabResults(reportId: String): ApiResult<LabResultsResponse> =
        apiAdapter.fetchLabResults(reportId)

    /** Fetch a short-lived signed URL for secure report PDF download. */
    suspend fun getReportDownloadUrl(reportId: String): ApiResult<String> =
        apiAdapter.fetchReportDownloadUrl(reportId)

    // ── User Reports (Report History) ────────────────────

    /** Fetch all reports for a user, sorted by most recent. */
    suspend fun getUserReports(
        limit: Int = 20,
        offset: Int = 0
    ): ApiResult<List<ReportSummary>> =
        apiAdapter.fetchUserReports(limit, offset)

    // ── RAG / AI Health Assistant ─────────────────────────

    /** Send a user query to the AI health assistant with optional location context. */
    suspend fun postVoiceChat(userId: String, text: String): ApiResult<VoiceChatResponse> =
        apiAdapter.postVoiceChat(VoiceChatRequest(text = text, userId = userId))

    suspend fun queryAssistant(
        userId: String,
        query: String,
        userLat: Double? = null,
        userLon: Double? = null,
        userLocation: String? = null
    ): ApiResult<RagData> =
        apiAdapter.queryHealthAssistant(userId, query, userLat, userLon, userLocation)

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

    // ── Reports — Async Ingest (Recommended) ───────────────

    /**
     * Upload and queue background processing (async, returns immediately).
     * Poll [getReportStatus] to track progress.
     */
    suspend fun ingestReport(
        userId: String,
        userName: String?,
        fileName: String,
        fileBytes: ByteArray
    ): ApiResult<IngestReportResponse> =
        apiAdapter.ingestReport(userId, userName, fileName, fileBytes)

    /** Poll the processing status of an async report upload. */
    suspend fun getReportStatus(reportId: String): ApiResult<ReportStatusResponse> =
        apiAdapter.getReportStatus(reportId)

    // ── Wearable Vitals ─────────────────────────────────────

    /**
     * Batch ingest vital readings from wearable device.
     * [readings] should contain all metric types collected from Health Connect.
     */
    suspend fun ingestVitals(
        userId: String,
        readings: List<VitalReading>
    ): ApiResult<IngestVitalsResponse> =
        apiAdapter.ingestVitals(userId, readings)

    /**
     * Fetch aggregated vitals summary for the context builder.
     * Returns 7-day stats (avg, min, max, latest) per metric type.
     */
    suspend fun getVitalsSummary(userId: String, days: Int = 7): ApiResult<VitalsSummaryResponse> =
        apiAdapter.getVitalsSummary(userId, days)

    /** Fetch the latest weekly AI summary for the dashboard brief card. */
    suspend fun getLatestSummary(userId: String): ApiResult<SummaryResponse> =
        apiAdapter.getLatestSummary(userId)

    /** Trigger backend generation of a new weekly AI summary for this user. */
    suspend fun generateSummary(userId: String): ApiResult<GenerateSummaryResponse> =
        apiAdapter.generateSummary(userId)

    /**
     * Fetch raw vital readings (not aggregated) for detailed analysis.
     * Optionally filter by [metricType] (e.g., "heart_rate").
     */
    suspend fun getVitalsReadings(
        userId: String,
        metricType: String? = null,
        days: Int = 7,
        limit: Int = 100
    ): ApiResult<VitalsReadingsResponse> =
        apiAdapter.getVitalsReadings(userId, metricType, days, limit)
}
