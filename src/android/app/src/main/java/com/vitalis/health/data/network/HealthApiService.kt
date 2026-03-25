package com.vitalis.health.data.network

import com.vitalis.health.data.model.*
import okhttp3.MultipartBody
import okhttp3.RequestBody
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
    @GET("/api/v1/users/{user_id}")
    suspend fun getUserProfile(
        @Path("user_id") userId: String
    ): Response<UserProfile>

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

    // ── User Reports (Report History) ───────────────────────
    @GET("/reports")
    suspend fun getUserReports(
        @Query("limit") limit: Int = 20,
        @Query("offset") offset: Int = 0
    ): Response<ReportsListResponse>

    // ── RAG / AI Health Assistant ──────────────────────────
    @POST("/api/v1/rag_query")
    suspend fun postRagQuery(
        @Body body: RagQueryRequest
    ): Response<RagResponse>

    // ── Report Upload ──────────────────────────────────────
    @Multipart
    @POST("/reports/upload")
    suspend fun uploadReport(
        @Part("user_id") userId: RequestBody,
        @Part file: MultipartBody.Part
    ): Response<ReportUploadResponse>

    // ── Doctor — Patient List ──────────────────────────────
    @GET("/api/v1/doctor/patients")
    suspend fun getPatients(
        @Query("doctor_id") doctorId: String
    ): Response<PatientsResponse>

    // ── Reports — OCR ──────────────────────────────────────
    @FormUrlEncoded
    @POST("/reports/ocr")
    suspend fun ocrReport(
        @Field("user_id") userId: String,
        @Field("storage_path") storagePath: String
    ): Response<OcrReportResponse>

    // ── Reports — Extract Labs (Regex) ─────────────────────
    @FormUrlEncoded
    @POST("/reports/extract-labs")
    suspend fun extractLabs(
        @Field("report_id") reportId: String
    ): Response<ExtractLabsResponse>

    // ── Reports — Extract Labs (Gemini) ────────────────────
    @FormUrlEncoded
    @POST("/reports/extract-labs-gemini")
    suspend fun extractLabsGemini(
        @Field("report_id") reportId: String
    ): Response<GeminiExtractionLog>

    // ── Reports — Full Pipeline ────────────────────────────
    @Multipart
    @POST("/reports/process")
    suspend fun processReport(
        @Part("user_id") userId: RequestBody,
        @Part file: MultipartBody.Part,
        @Part("use_gemini") useGemini: RequestBody
    ): Response<ProcessReportResponse>

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
}
