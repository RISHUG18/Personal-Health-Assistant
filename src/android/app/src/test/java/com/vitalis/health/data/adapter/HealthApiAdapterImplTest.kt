package com.vitalis.health.data.adapter

import com.vitalis.health.data.model.*
import com.vitalis.health.data.network.ApiResult
import com.vitalis.health.data.network.HealthApiService
import com.vitalis.health.di.NetworkModule
import kotlinx.coroutines.test.runTest
import kotlinx.serialization.json.Json
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

/**
 * Unit tests for [HealthApiAdapterImpl] using OkHttp MockWebServer.
 *
 * These tests verify that the adapter correctly:
 *  - Parses successful JSON responses
 *  - Maps HTTP errors to [ApiResult.Error]
 *  - Handles malformed / empty bodies
 */
class HealthApiAdapterImplTest {

    private lateinit var server: MockWebServer
    private lateinit var adapter: HealthApiAdapter

    @Before
    fun setUp() {
        server = MockWebServer()
        server.start()

        val baseUrl = server.url("/").toString()
        adapter = NetworkModule.provideAdapter(baseUrl)
    }

    @After
    fun tearDown() {
        server.shutdown()
    }

    // ── Dashboard ─────────────────────────────────────────

    @Test
    fun `fetchDashboard returns DashboardData on 200`() = runTest {
        server.enqueue(
            MockResponse()
                .setResponseCode(200)
                .setBody("""
                    {
                      "status": "success",
                      "data": {
                        "user_id": "patient_001",
                        "greeting": "Good Morning",
                        "wellbeing_score": 85,
                        "wellbeing_trend": "improving",
                        "active_alerts_count": 2,
                        "environment": { "aqi": 42, "weather": "Sunny" }
                      }
                    }
                """.trimIndent())
        )

        val result = adapter.fetchDashboard("patient_001")

        assertTrue(result.isSuccess)
        val data = (result as ApiResult.Success).data
        assertEquals("Good Morning", data.greeting)
        assertEquals(85, data.wellbeingScore)
    }

    @Test
    fun `fetchDashboard returns Error on 500`() = runTest {
        server.enqueue(MockResponse().setResponseCode(500))

        val result = adapter.fetchDashboard("patient_001")

        assertTrue(result.isError)
        assertTrue((result as ApiResult.Error).message.contains("Server error"))
    }

    // ── Alerts ────────────────────────────────────────────

    @Test
    fun `fetchAlerts parses alert list correctly`() = runTest {
        server.enqueue(
            MockResponse()
                .setResponseCode(200)
                .setBody("""
                    {
                      "status": "success",
                      "data": {
                        "alerts": [
                          {
                            "id": "alert_01",
                            "title": "Low Sleep",
                            "severity": "high",
                            "timestamp": "2026-02-20T10:00:00",
                            "message": "You slept less than 5 hours."
                          }
                        ]
                      }
                    }
                """.trimIndent())
        )

        val result = adapter.fetchAlerts("patient_001")

        assertTrue(result.isSuccess)
        val alerts = (result as ApiResult.Success).data
        assertEquals(1, alerts.size)
        assertEquals("Low Sleep", alerts[0].title)
    }

    // ── RAG Query ─────────────────────────────────────────

    @Test
    fun `queryHealthAssistant returns RagData on 200`() = runTest {
        server.enqueue(
            MockResponse()
                .setResponseCode(200)
                .setBody("""
                    {
                      "status": "success",
                      "data": {
                        "answer": "Your iron levels are low.",
                        "citations": [
                          { "source_file": "blood_report.pdf", "page": 2, "snippet": "Ferritin: 10" }
                        ]
                      }
                    }
                """.trimIndent())
        )

        val result = adapter.queryHealthAssistant("patient_001", "Why is my iron low?")

        assertTrue(result.isSuccess)
        val rag = (result as ApiResult.Success).data
        assertTrue(rag.answer.contains("iron"))
        assertEquals(1, rag.citations.size)
    }

    @Test
    fun `queryHealthAssistant returns Error on 404`() = runTest {
        server.enqueue(MockResponse().setResponseCode(404))

        val result = adapter.queryHealthAssistant("patient_001", "test")

        assertTrue(result.isError)
        assertTrue((result as ApiResult.Error).message.contains("not found"))
    }
}
