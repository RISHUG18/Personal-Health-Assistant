package com.vitalis.health.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

// ─────────────────────────────────────────────
// Dashboard Models (refactored to remove mock features)
// ─────────────────────────────────────────────

/**
 * Aggregated dashboard data built from multiple backend endpoints.
 *
 * Note: The backend does NOT calculate `wellbeingScore` or `wellbeingTrend`.
 * These mock fields have been removed. The dashboard now displays:
 * - User greeting (from /api/v1/users/{user_id})
 * - Active alerts count and list (from /alerts/{user_id})
 * - Environment data (from /api/v1/environment)
 * - Report history (from /reports)
 */
@Serializable
data class DashboardData(
    @SerialName("user_id")
    val userId: String,
    val greeting: String,
    @SerialName("active_alerts_count")
    val activeAlertsCount: Int,
    val alerts: List<DashboardAlert> = emptyList(),
    val environment: EnvironmentData? = null,
    val reports: List<ReportSummary> = emptyList()
)

/**
 * Simplified alert for dashboard display.
 */
@Serializable
data class DashboardAlert(
    val id: String,
    val severity: String,
    val reason: String,
    @SerialName("created_at")
    val createdAt: String,
)

/**
 * Environment data from the backend /api/v1/environment endpoint.
 * Includes AQI, weather, and location information.
 */
@Serializable
data class EnvironmentData(
    @SerialName("location_city")
    val locationCity: String? = null,
    val latitude: Double? = null,
    val longitude: Double? = null,
    @SerialName("temperature_celsius")
    val temperatureCelsius: Double? = null,
    @SerialName("humidity_percent")
    val humidityPercent: Double? = null,
    @SerialName("aqi_level")
    val aqiLevel: Int? = null,
    @SerialName("weather_condition")
    val weatherCondition: String? = null,
    @SerialName("fetched_at")
    val fetchedAt: String? = null
)

/**
 * Report summary for dashboard timeline.
 */
@Serializable
data class ReportSummary(
    @SerialName("report_id")
    val reportId: String,
    @SerialName("report_name")
    val reportName: String,
    @SerialName("upload_date")
    val uploadDate: String,
    @SerialName("report_type")
    val reportType: String,
    @SerialName("risk_label")
    val riskLabel: String,
    @SerialName("risk_level")
    val riskLevel: String,
    @SerialName("processing_status")
    val processingStatus: String? = null,
    @SerialName("ocr_confidence")
    val ocrConfidence: Double? = null,
    @SerialName("lab_results_count")
    val labResultsCount: Int = 0,
    @SerialName("public_url")
    val publicUrl: String? = null,
    @SerialName("storage_path")
    val storagePath: String? = null
)

/**
 * Single report item from GET /reports.
 */
@Serializable
data class ReportsListItem(
    val id: String,
    @SerialName("created_at")
    val createdAt: String,
    @SerialName("source_file_name")
    val sourceFileName: String,
    @SerialName("report_date")
    val reportDate: String? = null,
    @SerialName("report_type")
    val reportType: String? = null,
    @SerialName("processing_status")
    val processingStatus: String? = null,
    @SerialName("processing_error")
    val processingError: String? = null
)

/**
 * Response from GET /reports.
 */
@Serializable
data class ReportsListResponse(
    val items: List<ReportsListItem>,
    val total: Int,
    val limit: Int,
    val offset: Int
)

/**
 * Wrapper response for backward compatibility (if needed).
 */
@Serializable
data class DashboardResponse(
    val status: String,
    val data: DashboardData? = null,
    val message: String? = null
)
