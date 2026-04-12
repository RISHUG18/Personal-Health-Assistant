package com.vitalis.health.data.network

import com.vitalis.health.data.model.*
import okhttp3.MultipartBody
import okhttp3.RequestBody
import okhttp3.ResponseBody
import retrofit2.Response
import retrofit2.http.*

/**
 * Retrofit service interface — the raw HTTP contract.
 *
 * Every method returns [Response<T>] so the adapter can inspect HTTP status
 * codes and headers before converting to [ApiResult].
 */
interface HealthApiService {

    // ── Authentication ────────────────────────────────────
    @POST("/auth/login")
    suspend fun login(
        @Body body: UserLoginRequest
    ): Response<AuthResponse>

    @POST("/auth/register")
    suspend fun register(
        @Body body: UserRegisterRequest
    ): Response<AuthResponse>

    // ── User Profile ───────────────────────────────────────
    @GET("/api/v1/users/me")
    suspend fun getMyProfile(): Response<UserProfile>

    @PATCH("/api/v1/users/me")
    suspend fun updateMyProfile(
        @Body body: UserUpdateRequest
    ): Response<UserProfile>

    @GET("/api/v1/users/me/export")
    suspend fun exportMyData(): Response<ResponseBody>

    @DELETE("/api/v1/users/me")
    suspend fun deleteMyUser(): Response<Unit>

    // ── Alerts ─────────────────────────────────────────────
    @GET("/alerts/{user_id}")
    suspend fun getAlerts(
        @Path("user_id") userId: String,
        @Query("include_evidence") includeEvidence: Boolean = true
    ): Response<AlertsApiResponse>

    // ── Environment (AQI/Weather) ──────────────────────────
    @GET("/api/v1/environment")
    suspend fun getEnvironment(
        @Query("user_id") userId: String,
        @Query("latitude") latitude: Double,
        @Query("longitude") longitude: Double,
        @Query("city") city: String? = null
    ): Response<EnvironmentData>

    // ── Lab Results ────────────────────────────────────────
    @GET("/reports/{report_id}/lab-results")
    suspend fun getLabResults(
        @Path("report_id") reportId: String
    ): Response<LabResultsResponse>

    @GET("/reports/{report_id}/download_url")
    suspend fun getReportDownloadUrl(
        @Path("report_id") reportId: String
    ): Response<ReportDownloadUrlResponse>

    // ── User Reports (Report History) ───────────────────────
    @GET("/reports")
    suspend fun getUserReports(
        @Query("limit") limit: Int = 20,
        @Query("offset") offset: Int = 0
    ): Response<ReportsListResponse>

    @DELETE("/api/reports/{report_id}")
    suspend fun deleteReport(
        @Path("report_id") reportId: String
    ): Response<DeleteReportResponse>

    // ── RAG / AI Health Assistant ──────────────────────────
    @POST("/api/v1/rag_query")
    suspend fun postRagQuery(
        @Body body: RagQueryRequest
    ): Response<RagResponse>

    // ── Voice Interaction ────────────────────────────────────
    @POST("/voice/voice_chat")
    suspend fun postVoiceChat(
        @Body body: VoiceChatRequest
    ): Response<VoiceChatResponse>

    // ── Report Upload ──────────────────────────────────────
    @Multipart
    @POST("/upload/report")
    suspend fun uploadReport(
        @Part file: MultipartBody.Part
    ): Response<ReportUploadResponse>

    // ── Doctor — Patient List ──────────────────────────────
    @GET("/api/v1/doctor/patients")
    suspend fun getPatients(): Response<PatientsResponse>

    // ── Reports — Async Ingest (Recommended) ───────────────
    @Multipart
    @POST("/reports/ingest")
    suspend fun ingestReport(
        @Part("user_id") userId: RequestBody,
        @Part("user_name") userName: RequestBody?,
        @Part file: MultipartBody.Part
    ): Response<IngestReportResponse>

    // ── Reports — Status Polling ───────────────────────────
    @GET("/reports/status/{report_id}")
    suspend fun getReportStatus(
        @Path("report_id") reportId: String
    ): Response<ReportStatusResponse>

    // ── Wearable Vitals ─────────────────────────────────────

    /** Batch ingest vital readings from wearable devices. */
    @POST("/api/v1/ingest/vitals")
    suspend fun ingestVitals(
        @Body body: IngestVitalsRequest
    ): Response<IngestVitalsResponse>

    /** Get aggregated 7-day vitals summary for the context builder. */
    @GET("/api/v1/vitals/{user_id}/summary")
    suspend fun getVitalsSummary(
        @Path("user_id") userId: String,
        @Query("days") days: Int = 7
    ): Response<VitalsSummaryResponse>

    /** Fetch the latest weekly AI summary for a user-facing dashboard brief. */
    @GET("/api/v1/summaries/{user_id}")
    suspend fun getLatestSummary(
        @Path("user_id") userId: String,
        @Query("role") role: String = "user",
        @Query("limit") limit: Int = 1
    ): Response<SummaryResponse>

    /** Trigger fresh weekly summary generation for the authenticated user. */
    @POST("/api/v1/summaries/generate/{user_id}")
    suspend fun generateSummary(
        @Path("user_id") userId: String
    ): Response<GenerateSummaryResponse>

    /** Get raw vital readings (not aggregated) for detailed analysis. */
    @GET("/api/v1/vitals/{user_id}/readings")
    suspend fun getVitalsReadings(
        @Path("user_id") userId: String,
        @Query("metric_type") metricType: String? = null,
        @Query("days") days: Int = 7,
        @Query("limit") limit: Int = 100
    ): Response<VitalsReadingsResponse>
}
