package com.vitalis.health.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

// ─────────────────────────────────────────────
// Doctor / Patient List Models
// ─────────────────────────────────────────────

@Serializable
data class Patient(
    @SerialName("user_id")
    val userId: String,
    val name: String = "",
    val age: Int? = null,
    @SerialName("risk_level")
    val riskLevel: String = "low",
    @SerialName("last_report_at")
    val lastReportAt: String? = null,
    @SerialName("last_updated")
    val lastUpdated: String? = null,
)

@Serializable
data class PatientsResponse(
    val patients: List<Patient>
)
