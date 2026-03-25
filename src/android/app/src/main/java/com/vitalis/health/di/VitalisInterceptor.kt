package com.vitalis.health.di

import android.util.Log
import com.vitalis.health.data.local.TokenManager
import okhttp3.Interceptor
import okhttp3.Response
import okhttp3.internal.http.promisesBody
import okio.Buffer
import java.io.IOException
import java.nio.charset.Charset

/**
 * OkHttp interceptor that provides developer observability:
 * - Adds Authorization header if access token is available
 * - Logs every request (method, URL, truncated body)
 * - Logs every response (status code, URL, truncated body)
 * - Logs non-2xx responses as warnings
 * - Flags slow responses exceeding [SLOW_THRESHOLD_MS] milliseconds
 * - Logs IOExceptions as errors
 */
class VitalisInterceptor(
    private val tokenManager: TokenManager? = null
) : Interceptor {

    companion object {
        private const val TAG = "VitalisInterceptor"
        private const val SLOW_THRESHOLD_MS = 2_000L
        private const val BODY_TRUNCATE_CHARS = 500
        private const val HEADER_AUTHORIZATION = "Authorization"
    }

    override fun intercept(chain: Interceptor.Chain): Response {
        var request = chain.request()
        val url = request.url.toString()
        val method = request.method

        // Add Authorization header if token is available and not an auth endpoint
        val isAuthEndpoint = url.contains("/auth/login") || url.contains("/auth/register")
        if (!isAuthEndpoint) {
            tokenManager?.accessToken?.let { token ->
                request = request.newBuilder()
                    .addHeader(HEADER_AUTHORIZATION, "Bearer $token")
                    .build()
            }
        }

        // Log outgoing request
        val requestBody = request.body
        val requestBodySnippet = if (requestBody != null) {
            try {
                val buffer = Buffer()
                requestBody.writeTo(buffer)
                buffer.readString(Charset.forName("UTF-8")).take(BODY_TRUNCATE_CHARS)
            } catch (e: Exception) {
                "<unreadable body>"
            }
        } else {
            "<no body>"
        }
        Log.d(TAG, "--> $method $url | body: $requestBodySnippet")

        val startMs = System.currentTimeMillis()

        val response: Response
        try {
            response = chain.proceed(request)
        } catch (e: IOException) {
            Log.e(TAG, "<-- $method $url FAILED: ${e.message}", e)
            throw e
        }

        val elapsedMs = System.currentTimeMillis() - startMs

        // Flag slow responses
        if (elapsedMs > SLOW_THRESHOLD_MS) {
            Log.w(TAG, "SLOW REQUEST [${elapsedMs}ms]: $method $url")
        }

        // Log response
        val statusCode = response.code
        val responseBodySnippet = if (response.promisesBody()) {
            try {
                val source = response.body?.source()
                source?.request(Long.MAX_VALUE)
                val buffer = source?.buffer?.clone()
                buffer?.readString(Charset.forName("UTF-8"))?.take(BODY_TRUNCATE_CHARS)
                    ?: "<empty body>"
            } catch (e: Exception) {
                "<unreadable body>"
            }
        } else {
            "<no body>"
        }

        if (statusCode in 200..299) {
            Log.d(TAG, "<-- $statusCode $method $url [${elapsedMs}ms] | body: $responseBodySnippet")
        } else {
            Log.w(
                TAG,
                "<-- ERROR $statusCode $method $url [${elapsedMs}ms] | body: $responseBodySnippet"
            )
        }

        return response
    }
}
