package com.vitalis.health.data.adapter

import com.vitalis.health.data.model.*
import com.vitalis.health.data.network.ApiResult
import com.vitalis.health.data.network.HealthApiService
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Response as OkHttpResponse
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import org.json.JSONArray
import org.json.JSONObject
import retrofit2.Response
import java.io.IOException
import java.net.SocketTimeoutException
import java.util.Locale

/**
 * Production implementation of [HealthApiAdapter].
 *
 * All network I/O is shifted to [ioDispatcher] so callers never need to worry
 * about threading.  Every public method returns [ApiResult] — no exceptions
 * escape this layer.
 */
class HealthApiAdapterImpl(
    private val api: HealthApiService,
    private val okHttpClient: OkHttpClient,
    private val baseUrl: String,
    private val ioDispatcher: CoroutineDispatcher = Dispatchers.IO
) : HealthApiAdapter {

    // ── Authentication ────────────────────────────────────

    override suspend fun login(email: String, password: String): ApiResult<AuthResponse> =
        safeApiCall {
            val response = api.login(UserLoginRequest(email = email, password = password))
            response.unwrap { body -> body }
        }

    override suspend fun register(
        email: String,
        password: String,
        fullName: String,
        dateOfBirth: String,
        gender: String?,
        heightCm: Double?,
        weightKg: Double?,
        role: String
    ): ApiResult<AuthResponse> = safeApiCall {
        val response = api.register(
            UserRegisterRequest(
                email = email,
                password = password,
                fullName = fullName,
                dateOfBirth = dateOfBirth,
                gender = gender,
                heightCm = heightCm,
                weightKg = weightKg,
                role = role
            )
        )
        response.unwrap { body -> body }
    }

    // ── User Profile ─────────────────────────────────────────

    override suspend fun fetchUserProfile(userId: String): ApiResult<UserProfile> =
        safeApiCall {
            val response = api.getMyProfile()
            response.unwrap { body -> body }
        }

    override suspend fun updateUserProfile(
        userId: String,
        request: UserUpdateRequest
    ): ApiResult<UserProfile> = safeApiCall {
        val response = api.updateMyProfile(request)
        response.unwrap { body -> body }
    }

    override suspend fun exportMyData(): ApiResult<ByteArray> = safeApiCall {
        val response = api.exportMyData()
        if (response.isSuccessful) {
            val bytes = response.body()?.bytes()
                ?: return@safeApiCall ApiResult.Error("Empty export from server", code = response.code())
            ApiResult.Success(bytes)
        } else {
            ApiResult.Error(
                message = extractErrorMessage(
                    code = response.code(),
                    rawErrorBody = response.errorBody()?.string(),
                ),
                code = response.code()
            )
        }
    }

    override suspend fun deleteUser(userId: String): ApiResult<Unit> = safeApiCall {
        val response = api.deleteMyUser()
        response.unwrap { Unit }
    }

    override suspend fun getUserByEmail(email: String): ApiResult<UserProfile> = safeApiCall {
        // Current backend build does not expose a /api/v1/users/email/{email} route.
        ApiResult.Error("User lookup by email is not available on this backend.")
    }

    // ── Alerts ────────────────────────────────────────────

    override suspend fun fetchAlerts(userId: String): ApiResult<List<Alert>> =
        safeApiCall {
            val response = api.getAlerts(userId, includeEvidence = true)
            response.unwrap { body -> body.alerts }
        }

    // ── Environment (AQI/Weather) ─────────────────────────

    override suspend fun fetchEnvironment(
        userId: String,
        latitude: Double,
        longitude: Double,
        city: String?
    ): ApiResult<EnvironmentData> = safeApiCall {
        val response = api.getEnvironment(userId, latitude, longitude, city)
        response.unwrap { body -> body }
    }

    // ── Lab Results ───────────────────────────────────────

    override suspend fun fetchLabResults(reportId: String): ApiResult<LabResultsResponse> =
        safeApiCall {
            val response = api.getLabResults(reportId)
            response.unwrap { body -> body }
        }

    override suspend fun fetchReportDownloadUrl(reportId: String): ApiResult<String> =
        safeApiCall {
            val response = api.getReportDownloadUrl(reportId)
            response.unwrap { body -> body.signedUrl }
        }

    // ── User Reports (Report History) ────────────────────────

    override suspend fun fetchUserReports(
        limit: Int,
        offset: Int
    ): ApiResult<List<ReportSummary>> = safeApiCall {
        val response = api.getUserReports(limit, offset)
        response.unwrap { body ->
            body.items.map { item ->
                val normalizedStatus = item.processingStatus?.lowercase(Locale.US)
                val (riskLabel, riskLevel) = when (normalizedStatus) {
                    "failed" -> "Failed" to "high"
                    "processing" -> "Processing" to "mild"
                    "validating" -> "Processing" to "mild"
                    "pending" -> "Processing" to "mild"
                    "ocr_complete" -> "Processing" to "mild"
                    "completed" -> "Complete" to "normal"
                    "done" -> "Complete" to "normal"
                    else -> "Complete" to "normal"
                }

                val fallbackId = buildString {
                    append("report-")
                    append((item.createdAt ?: item.reportDate ?: System.currentTimeMillis().toString()).replace(":", "-"))
                }

                ReportSummary(
                    reportId = item.id.takeIf { it.isNotBlank() } ?: fallbackId,
                    reportName = item.sourceFileName?.takeIf { it.isNotBlank() } ?: "Medical Report",
                    uploadDate = item.createdAt ?: item.reportDate ?: "Unknown date",
                    reportType = item.reportType ?: "lab",
                    riskLabel = riskLabel,
                    riskLevel = riskLevel,
                    processingStatus = normalizedStatus,
                    ocrConfidence = null,
                    labResultsCount = 0,
                    publicUrl = null,
                    storagePath = null
                )
            }
        }
    }

    override suspend fun deleteReport(reportId: String): ApiResult<DeleteReportResponse> = safeApiCall {
        val response = api.deleteReport(reportId)
        response.unwrap { body -> body }
    }

    // ── RAG / AI Health Assistant ─────────────────────────

    override suspend fun postVoiceChat(request: VoiceChatRequest): ApiResult<VoiceChatResponse> =
        safeApiCall {
            val response = api.postVoiceChat(request)
            response.unwrap { body -> body }
        }

    override suspend fun queryHealthAssistant(
        userId: String,
        query: String,
        userLat: Double?,
        userLon: Double?,
        userLocation: String?
    ): ApiResult<RagData> = safeApiCall {
        val response = api.postRagQuery(
            RagQueryRequest(
                userId = userId,
                query = query,
                userLat = userLat,
                userLon = userLon,
                userLocation = userLocation
            )
        )
        response.unwrap { body ->
            RagData(answer = body.answer)
        }
    }

    // ── Report Upload ─────────────────────────────────────

    override suspend fun uploadReport(
        userId: String,
        fileName: String,
        fileBytes: ByteArray
    ): ApiResult<ReportUploadResponse> = safeApiCall {
        val mimeType = detectUploadMimeType(fileName)
        val filePart = MultipartBody.Part.createFormData(
            "file",
            fileName,
            fileBytes.toRequestBody(mimeType.toMediaType())
        )
        val response = api.uploadReport(filePart)
        response.unwrap { body -> body }
    }

    // ── Doctor — Patient List ─────────────────────────────

    override suspend fun fetchPatients(doctorId: String): ApiResult<List<Patient>> =
        safeApiCall {
            val response = api.getPatients()
            response.unwrap { body -> body.patients }
        }

    // ── Reports — OCR ─────────────────────────────────────

    override suspend fun ocrReport(userId: String, storagePath: String): ApiResult<OcrReportResponse> =
        safeApiCall {
            ApiResult.Error(
                "OCR endpoint is unavailable on this backend. Use async ingest processing instead."
            )
        }

    // ── Reports — Extract Labs (Regex) ─────────────────────

    override suspend fun extractLabs(reportId: String): ApiResult<ExtractLabsResponse> =
        safeApiCall {
            ApiResult.Error(
                "Lab extraction endpoint is unavailable on this backend. Use async ingest processing instead."
            )
        }

    // ── Reports — Extract Labs (Gemini) ────────────────────

    override suspend fun extractLabsGemini(reportId: String): ApiResult<GeminiExtractionLog> =
        safeApiCall {
            ApiResult.Error(
                "Gemini extraction endpoint is unavailable on this backend. Use async ingest processing instead."
            )
        }

    // ── Reports — Full Pipeline ────────────────────────────

    override suspend fun processReport(
        userId: String,
        fileName: String,
        fileBytes: ByteArray,
        useGemini: Boolean
    ): ApiResult<ProcessReportResponse> = safeApiCall {
        ApiResult.Error(
            "Synchronous report processing is unavailable on this backend. Use ingestReport() and poll getReportStatus()."
        )
    }

    override suspend fun ingestReport(
        userId: String,
        userName: String?,
        fileName: String,
        fileBytes: ByteArray
    ): ApiResult<IngestReportResponse> = safeApiCall {
        val userIdPart = userId.toRequestBody("text/plain".toMediaType())
        val userNamePart = userName?.toRequestBody("text/plain".toMediaType())
        val mimeType = detectUploadMimeType(fileName)
        val filePart = MultipartBody.Part.createFormData(
            "file",
            fileName,
            fileBytes.toRequestBody(mimeType.toMediaType())
        )
        val response = api.ingestReport(userIdPart, userNamePart, filePart)
        response.unwrap { body -> body }
    }

    override suspend fun getReportStatus(reportId: String): ApiResult<ReportStatusResponse> = safeApiCall {
        val response = api.getReportStatus(reportId)
        response.unwrap { body -> body }
    }

    override fun observeReportStatus(reportId: String): Flow<ApiResult<ReportRealtimeStatusMessage>> = callbackFlow {
        val request = Request.Builder()
            .url(buildReportStatusWebSocketUrl(reportId))
            .build()

        val webSocket = okHttpClient.newWebSocket(
            request,
            object : WebSocketListener() {
                override fun onOpen(webSocket: WebSocket, response: OkHttpResponse) {
                    // No-op: server pushes report status updates.
                }

                override fun onMessage(webSocket: WebSocket, text: String) {
                    val parsed = try {
                        parseRealtimeStatusMessage(text)
                    } catch (_: Exception) {
                        null
                    }

                    if (parsed == null) {
                        trySend(ApiResult.Error("Invalid realtime status payload from server."))
                        return
                    }

                    trySend(ApiResult.Success(parsed))
                }

                override fun onFailure(webSocket: WebSocket, t: Throwable, response: OkHttpResponse?) {
                    trySend(
                        ApiResult.Error(
                            message = t.message ?: "Realtime status connection failed.",
                            throwable = t
                        )
                    )
                    close(t)
                }

                override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
                    webSocket.close(code, reason)
                }

                override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                    close()
                }
            }
        )

        awaitClose {
            webSocket.close(1000, "Client closed")
        }
    }

    // ── Wearable Vitals ─────────────────────────────────────

    override suspend fun ingestVitals(
        userId: String,
        readings: List<VitalReading>
    ): ApiResult<IngestVitalsResponse> {
        if (readings.isEmpty()) {
            return ApiResult.Success(
                IngestVitalsResponse(
                    userId = userId,
                    inserted = 0,
                    skipped = 0,
                    total = 0
                )
            )
        }

        var totalInserted = 0
        var totalSkipped = 0
        var totalReadings = 0
        val allErrors = mutableListOf<String>()

        for (chunk in readings.chunked(1000)) {
            when (
                val chunkResult = safeApiCall {
                    val response = api.ingestVitals(
                        IngestVitalsRequest(userId = userId, readings = chunk)
                    )
                    response.unwrap { body -> body }
                }
            ) {
                is ApiResult.Success -> {
                    val chunkData = chunkResult.data
                    totalInserted += chunkData.inserted
                    totalSkipped += chunkData.skipped
                    totalReadings += chunkData.total
                    allErrors += chunkData.errors
                }

                is ApiResult.Error -> return chunkResult
            }
        }

        return ApiResult.Success(
            IngestVitalsResponse(
                userId = userId,
                inserted = totalInserted,
                skipped = totalSkipped,
                total = totalReadings,
                errors = allErrors
            )
        )
    }

    override suspend fun getVitalsSummary(userId: String, days: Int): ApiResult<VitalsSummaryResponse> =
        safeApiCall {
            val response = api.getVitalsSummary(userId, days)
            response.unwrap { body -> body }
        }

    override suspend fun getLatestSummary(userId: String): ApiResult<SummaryResponse> =
        safeApiCall {
            val response = api.getLatestSummary(userId = userId, role = "user", limit = 1)
            response.unwrap { body -> body }
        }

    override suspend fun generateSummary(userId: String): ApiResult<GenerateSummaryResponse> =
        safeApiCall {
            val response = api.generateSummary(userId)
            response.unwrap { body -> body }
        }

    override suspend fun getVitalsReadings(
        userId: String,
        metricType: String?,
        days: Int,
        limit: Int
    ): ApiResult<VitalsReadingsResponse> = safeApiCall {
        val response = api.getVitalsReadings(userId, metricType, days, limit)
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

        val rawErrorBody = errorBody()?.string()
        return ApiResult.Error(
            message = extractErrorMessage(code = code(), rawErrorBody = rawErrorBody),
            code = code()
        )
    }

    private fun extractErrorMessage(code: Int, rawErrorBody: String?): String {
        val bodyMessage = parseErrorBodyMessage(rawErrorBody)
        return bodyMessage ?: httpErrorMessage(code)
    }

    private fun parseErrorBodyMessage(rawErrorBody: String?): String? {
        val trimmed = rawErrorBody?.trim().orEmpty()
        if (trimmed.isEmpty()) return null

        return try {
            when {
                trimmed.startsWith("{") -> parseJsonObjectMessage(JSONObject(trimmed))
                trimmed.startsWith("[") -> parseJsonArrayMessage(JSONArray(trimmed))
                else -> trimmed
            }?.takeIf { it.isNotBlank() }
        } catch (_: Exception) {
            trimmed.takeIf { it.isNotBlank() }
        }
    }

    private fun parseJsonObjectMessage(json: JSONObject): String? {
        val detail = json.opt("detail")
        when (detail) {
            is String -> return detail
            is JSONObject -> {
                val nested = detail.optString("message", "")
                if (nested.isNotBlank()) return nested
                val nestedDetail = detail.optString("detail", "")
                if (nestedDetail.isNotBlank()) return nestedDetail
            }
            is JSONArray -> return parseJsonArrayMessage(detail)
        }

        val message = json.optString("message", "")
        if (message.isNotBlank()) return message

        val error = json.optString("error", "")
        if (error.isNotBlank()) return error

        return null
    }

    private fun parseJsonArrayMessage(array: JSONArray): String? {
        val messages = mutableListOf<String>()
        for (i in 0 until array.length()) {
            when (val item = array.opt(i)) {
                is String -> if (item.isNotBlank()) messages.add(item)
                is JSONObject -> {
                    val msg = item.optString("msg", "")
                    if (msg.isNotBlank()) {
                        messages.add(msg)
                    } else {
                        val detail = item.optString("detail", "")
                        if (detail.isNotBlank()) messages.add(detail)
                    }
                }
            }
        }

        return messages.joinToString(separator = "\n").takeIf { it.isNotBlank() }
    }

    private fun detectUploadMimeType(fileName: String): String {
        val lower = fileName.lowercase(Locale.US)
        return when {
            lower.endsWith(".png") -> "image/png"
            lower.endsWith(".jpg") || lower.endsWith(".jpeg") -> "image/jpeg"
            lower.endsWith(".webp") -> "image/webp"
            lower.endsWith(".pdf") -> "application/pdf"
            else -> "application/octet-stream"
        }
    }

    private fun buildReportStatusWebSocketUrl(reportId: String): String {
        val normalizedBase = baseUrl.trim().trimEnd('/')
        val wsBase = when {
            normalizedBase.startsWith("https://") -> "wss://${normalizedBase.removePrefix("https://")}"
            normalizedBase.startsWith("http://") -> "ws://${normalizedBase.removePrefix("http://")}"
            normalizedBase.startsWith("wss://") || normalizedBase.startsWith("ws://") -> normalizedBase
            else -> "ws://$normalizedBase"
        }
        return "$wsBase/ws/report-status/$reportId"
    }

    private fun parseRealtimeStatusMessage(raw: String): ReportRealtimeStatusMessage {
        val json = JSONObject(raw)
        val dataObj = json.optJSONObject("data")
        val errorObj = json.optJSONObject("error")

        val data = ReportRealtimeData(
            reportId = dataObj?.optString("report_id")?.takeIf { it.isNotBlank() },
            testsDetected = dataObj
                ?.takeIf { it.has("tests_detected") && !it.isNull("tests_detected") }
                ?.optInt("tests_detected"),
            alertsTriggered = dataObj
                ?.takeIf { it.has("alerts_triggered") && !it.isNull("alerts_triggered") }
                ?.optInt("alerts_triggered"),
            ocrConfidence = dataObj
                ?.takeIf { it.has("ocr_confidence") && !it.isNull("ocr_confidence") }
                ?.optDouble("ocr_confidence"),
            cleanupStarted = dataObj
                ?.takeIf { it.has("cleanup_started") && !it.isNull("cleanup_started") }
                ?.optBoolean("cleanup_started"),
            cleanupCompleted = dataObj
                ?.takeIf { it.has("cleanup_completed") && !it.isNull("cleanup_completed") }
                ?.optBoolean("cleanup_completed"),
            reportDeleted = dataObj
                ?.takeIf { it.has("report_deleted") && !it.isNull("report_deleted") }
                ?.optBoolean("report_deleted"),
        )

        val error = ReportRealtimeError(
            reason = errorObj?.optString("reason")?.takeIf { it.isNotBlank() },
            confidence = errorObj
                ?.takeIf { it.has("confidence") && !it.isNull("confidence") }
                ?.optDouble("confidence")
        )

        val reportId = json.optString("report_id")
        val status = json.optString("status")
        if (reportId.isBlank() || status.isBlank()) {
            throw IllegalArgumentException("Missing required realtime fields")
        }

        return ReportRealtimeStatusMessage(
            reportId = reportId,
            status = status,
            data = data,
            error = error,
        )
    }

    private fun httpErrorMessage(code: Int): String = when (code) {
        400 -> "Bad request. Please check input."
        401 -> "Unauthorized. Please sign in again."
        403 -> "Access denied."
        404 -> "Requested resource not found."
        409 -> "Conflict. The request could not be completed."
        408 -> "Request timed out."
        422 -> "Invalid request data."
        429 -> "Too many requests. Please wait."
        in 500..599 -> "Server error. Please try again later."
        else -> "HTTP error $code."
    }
}

/** Internal exception used to short-circuit inside [unwrap]. */
private class ApiException(message: String) : Exception(message)
