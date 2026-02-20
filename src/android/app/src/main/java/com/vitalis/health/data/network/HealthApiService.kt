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

    // ── Dashboard ─────────────────────────────────────────
    @GET("/api/v1/dashboard/{user_id}")
    suspend fun getDashboard(
        @Path("user_id") userId: String
    ): Response<DashboardResponse>

    // ── Alerts ────────────────────────────────────────────
    @GET("/api/v1/alerts")
    suspend fun getAlerts(
        @Query("user_id") userId: String
    ): Response<AlertsResponse>

    // ── RAG / AI Health Assistant ─────────────────────────
    @POST("/api/v1/rag_query")
    suspend fun postRagQuery(
        @Body body: RagQueryRequest
    ): Response<RagResponse>

    // ── Report Upload ─────────────────────────────────────
    @Multipart
    @POST("/api/v1/reports/upload")
    suspend fun uploadReport(
        @Part("user_id") userId: RequestBody,
        @Part file: MultipartBody.Part
    ): Response<ReportUploadResponse>

    // ── Doctor — Patient List ─────────────────────────────
    @GET("/api/v1/doctor/patients")
    suspend fun getPatients(
        @Query("doctor_id") doctorId: String
    ): Response<PatientsResponse>
}
