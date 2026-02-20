package com.vitalis.health.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

// ─────────────────────────────────────────────
// Dashboard Models
// ─────────────────────────────────────────────

@Serializable
data class Environment(
    val aqi: Int? = null,
    val weather: String? = null
)

@Serializable
data class DashboardData(
    @SerialName("user_id")
    val userId: String,
    val greeting: String,
    @SerialName("wellbeing_score")
    val wellbeingScore: Int,
    @SerialName("wellbeing_trend")
    val wellbeingTrend: String,
    @SerialName("active_alerts_count")
    val activeAlertsCount: Int,
    val environment: Environment? = null
)

@Serializable
data class DashboardResponse(
    val status: String,
    val data: DashboardData? = null,
    val message: String? = null
)
