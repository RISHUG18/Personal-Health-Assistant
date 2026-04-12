package com.vitalis.health.data.model

import com.google.gson.annotations.SerializedName
import com.squareup.moshi.Json
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

// ─────────────────────────────────────────────
// Vitals Models (matching backend /api/v1/vitals endpoints)
// ─────────────────────────────────────────────

/**
 * Supported metric types for wearable vitals.
 * Must match backend enum: heart_rate, steps, sleep_minutes, etc.
 */
object VitalsMetricType {
    const val HEART_RATE = "heart_rate"
    const val RESTING_HEART_RATE = "resting_heart_rate"
    const val STEPS = "steps"
    const val SLEEP_MINUTES = "sleep_minutes"
    const val DEEP_SLEEP_MINUTES = "deep_sleep_minutes"
    const val SLEEP_SCORE = "sleep_score"
    const val CALORIES_BURNED = "calories_burned"
    const val ACTIVE_MINUTES = "active_minutes"
    const val HRV_MS = "hrv_ms"
    const val SPO2 = "spo2"
}

/**
 * A single vital reading to be sent to the backend.
 * Used for POST /api/v1/ingest/vitals
 */
@Serializable
data class VitalReading(
    @SerialName("recorded_at")
    @SerializedName("recorded_at")
    @Json(name = "recorded_at")
    val recordedAt: String,  // ISO-8601 timestamp

    @SerialName("metric_type")
    @SerializedName("metric_type")
    @Json(name = "metric_type")
    val metricType: String,  // e.g., "heart_rate", "steps"

    @SerialName("value")
    @SerializedName("value")
    @Json(name = "value")
    val value: Double,

    @SerialName("unit")
    @SerializedName("unit")
    @Json(name = "unit")
    val unit: String? = null,  // e.g., "bpm", "steps", "min", "%"

    @SerialName("device_id")
    @SerializedName("device_id")
    @Json(name = "device_id")
    val deviceId: String? = null
)

/**
 * Request body for POST /api/v1/ingest/vitals
 */
@Serializable
data class IngestVitalsRequest(
    @SerialName("user_id")
    @SerializedName("user_id")
    @Json(name = "user_id")
    val userId: String,

    @SerialName("readings")
    @SerializedName("readings")
    @Json(name = "readings")
    val readings: List<VitalReading>
)

/**
 * Response from POST /api/v1/ingest/vitals
 */
@Serializable
data class IngestVitalsResponse(
    @SerialName("user_id")
    val userId: String,

    val inserted: Int,
    val skipped: Int,
    val total: Int,
    val errors: List<String> = emptyList()
)

// ─────────────────────────────────────────────
// Vitals Summary Models (GET /api/v1/vitals/{user_id}/summary)
// ─────────────────────────────────────────────

/**
 * Aggregated stats for a single metric type over the summary period.
 */
@Serializable
data class MetricSummary(
    val avg: Double? = null,
    val min: Double? = null,
    val max: Double? = null,
    val latest: Double? = null,
    val samples: Int = 0,
    val unit: String? = null,
    // TODO: Wire backend 7-day chronological samples into this field for dashboard sparklines.
    @SerialName("trend_points")
    val trendPoints: List<Double>? = null
)

/**
 * Activity summary from wearable context.
 */
@Serializable
data class ActivitySummary(
    @SerialName("steps_today")
    val stepsToday: Int? = null,

    @SerialName("calories_burned")
    val caloriesBurned: Int? = null,

    @SerialName("active_minutes")
    val activeMinutes: Int? = null
)

/**
 * Sleep metrics from wearable context.
 */
@Serializable
data class SleepMetrics(
    @SerialName("total_sleep_hours")
    val totalSleepHours: Double? = null,

    @SerialName("sleep_score")
    val sleepScore: Int? = null,

    @SerialName("deep_sleep_minutes")
    val deepSleepMinutes: Int? = null
)

/**
 * Heart health metrics from wearable context.
 */
@Serializable
data class HeartHealth(
    @SerialName("resting_heart_rate")
    val restingHeartRate: Int? = null,

    @SerialName("hrv_score")
    val hrvScore: Int? = null
)

/**
 * Fully assembled wearable context ready for the context builder.
 */
@Serializable
data class WearableContext(
    @SerialName("device_synced_at")
    val deviceSyncedAt: String? = null,

    @SerialName("activity_summary")
    val activitySummary: ActivitySummary = ActivitySummary(),

    @SerialName("sleep_metrics")
    val sleepMetrics: SleepMetrics = SleepMetrics(),

    @SerialName("heart_health")
    val heartHealth: HeartHealth = HeartHealth(),

    @SerialName("vitals_7day_summary")
    val vitals7daySummary: Map<String, MetricSummary>? = null
)

/**
 * Response from GET /api/v1/vitals/{user_id}/summary
 */
@Serializable
data class VitalsSummaryResponse(
    @SerialName("user_id")
    val userId: String,

    @SerialName("period_days")
    val periodDays: Int,

    @SerialName("metric_count")
    val metricCount: Int,

    val summary: Map<String, MetricSummary>,

    @SerialName("wearable_context")
    val wearableContext: WearableContext
)

// ─────────────────────────────────────────────
// Raw Readings Models (GET /api/v1/vitals/{user_id}/readings)
// ─────────────────────────────────────────────

/**
 * A raw vital reading from the backend.
 */
@Serializable
data class VitalReadingRecord(
    val id: String,

    @SerialName("recorded_at")
    val recordedAt: String,

    @SerialName("metric_type")
    val metricType: String,

    val value: Double,

    val unit: String? = null,

    @SerialName("device_id")
    val deviceId: String? = null
)

/**
 * Response from GET /api/v1/vitals/{user_id}/readings
 */
@Serializable
data class VitalsReadingsResponse(
    @SerialName("user_id")
    val userId: String,

    @SerialName("metric_type")
    val metricType: String? = null,

    val days: Int,
    val count: Int,
    val readings: List<VitalReadingRecord>
)
