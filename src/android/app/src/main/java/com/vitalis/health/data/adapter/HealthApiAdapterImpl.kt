package com.vitalis.health.data.adapter

import com.vitalis.health.data.model.*
import com.vitalis.health.data.network.ApiResult
import com.vitalis.health.data.network.HealthApiService
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.toRequestBody
import retrofit2.Response
import java.io.IOException
import java.net.SocketTimeoutException

/**
 * Production implementation of [HealthApiAdapter].
 *
 * All network I/O is shifted to [ioDispatcher] so callers never need to worry
 * about threading.  Every public method returns [ApiResult] — no exceptions
 * escape this layer.
 */
class HealthApiAdapterImpl(
    private val api: HealthApiService,
    private val ioDispatcher: CoroutineDispatcher = Dispatchers.IO
) : HealthApiAdapter {

    // ── Dashboard ─────────────────────────────────────────

    override suspend fun fetchDashboard(userId: String): ApiResult<DashboardData> =
        safeApiCall {
            val response = api.getDashboard(userId)
            response.unwrap(
                extractData = { body ->
                    if (body.status == "success" && body.data != null) body.data
                    else throw ApiException(body.message ?: "Dashboard unavailable")
                }
            )
        }

    // ── Alerts ────────────────────────────────────────────

    override suspend fun fetchAlerts(userId: String): ApiResult<List<Alert>> =
        safeApiCall {
            val response = api.getAlerts(userId)
            response.unwrap { body -> body.data.alerts }
        }

    // ── RAG / AI Health Assistant ─────────────────────────

    override suspend fun queryHealthAssistant(
        userId: String,
        query: String
    ): ApiResult<RagData> = safeApiCall {
        val response = api.postRagQuery(RagQueryRequest(userId = userId, query = query))
        response.unwrap { body -> body.data }
    }

    // ── Report Upload ─────────────────────────────────────

    override suspend fun uploadReport(
        userId: String,
        fileName: String,
        fileBytes: ByteArray
    ): ApiResult<ReportUploadResponse> = safeApiCall {
        val userIdPart = userId.toRequestBody("text/plain".toMediaType())
        val filePart = MultipartBody.Part.createFormData(
            "file",
            fileName,
            fileBytes.toRequestBody("application/pdf".toMediaType())
        )
        val response = api.uploadReport(userIdPart, filePart)
        response.unwrap { body -> body }
    }

    // ── Doctor — Patient List ─────────────────────────────

    override suspend fun fetchPatients(doctorId: String): ApiResult<List<Patient>> =
        safeApiCall {
            val response = api.getPatients(doctorId)
            response.unwrap { body -> body.patients }
        }

    // ── Reports — OCR ─────────────────────────────────────

    override suspend fun ocrReport(userId: String, storagePath: String): ApiResult<OcrReportResponse> =
        safeApiCall {
            val response = api.ocrReport(userId, storagePath)
            response.unwrap { body -> body }
        }

    // ── Reports — Extract Labs (Regex) ─────────────────────

    override suspend fun extractLabs(reportId: String): ApiResult<ExtractLabsResponse> =
        safeApiCall {
            val response = api.extractLabs(reportId)
            response.unwrap { body -> body }
        }

    // ── Reports — Extract Labs (Gemini) ────────────────────

    override suspend fun extractLabsGemini(reportId: String): ApiResult<GeminiExtractionLog> =
        safeApiCall {
            val response = api.extractLabsGemini(reportId)
            response.unwrap { body -> body }
        }

    // ── Reports — Full Pipeline ────────────────────────────

    override suspend fun processReport(
        userId: String,
        fileName: String,
        fileBytes: ByteArray,
        useGemini: Boolean
    ): ApiResult<ProcessReportResponse> = safeApiCall {
        val userIdPart = userId.toRequestBody("text/plain".toMediaType())
        val useGeminiPart = useGemini.toString().toRequestBody("text/plain".toMediaType())
        val filePart = MultipartBody.Part.createFormData(
            "file",
            fileName,
            fileBytes.toRequestBody("application/pdf".toMediaType())
        )
        val response = api.processReport(userIdPart, filePart, useGeminiPart)
        response.unwrap { body -> body }
    }

    // ── Internal helpers ──────────────────────────────────

    /**
     * Wraps any suspend [block] so that network/timeout/parsing exceptions
     * are caught and converted to [ApiResult.Error].
     */
    private suspend fun <T> safeApiCall(
        block: suspend () -> ApiResult<T>
    ): ApiResult<T> = withContext(ioDispatcher) {
        try {
            block()
        } catch (e: SocketTimeoutException) {
            ApiResult.Error(
                message = "Request timed out. Please check your connection.",
                throwable = e
            )
        } catch (e: IOException) {
            ApiResult.Error(
                message = "Network error. Please check your connection.",
                throwable = e
            )
        } catch (e: ApiException) {
            ApiResult.Error(message = e.message ?: "Unknown API error", throwable = e)
        } catch (e: Exception) {
            ApiResult.Error(
                message = e.message ?: "Unexpected error occurred.",
                throwable = e
            )
        }
    }

    /**
     * Converts a Retrofit [Response] into [ApiResult].
     * [extractData] pulls the domain object from the response body.
     */
    private fun <B, T> Response<B>.unwrap(
        extractData: (B) -> T
    ): ApiResult<T> {
        if (isSuccessful) {
            val body = body()
                ?: return ApiResult.Error("Empty response from server", code = code())
            return try {
                ApiResult.Success(extractData(body))
            } catch (e: ApiException) {
                ApiResult.Error(e.message ?: "Bad response data", code = code())
            }
        }
        return ApiResult.Error(
            message = httpErrorMessage(code()),
            code = code()
        )
    }

    private fun httpErrorMessage(code: Int): String = when (code) {
        400 -> "Bad request. Please check input."
        401 -> "Unauthorized. Please sign in again."
        403 -> "Access denied."
        404 -> "Requested resource not found."
        408 -> "Request timed out."
        429 -> "Too many requests. Please wait."
        in 500..599 -> "Server error. Please try again later."
        else -> "HTTP error $code."
    }
}

/** Internal exception used to short-circuit inside [unwrap]. */
private class ApiException(message: String) : Exception(message)
