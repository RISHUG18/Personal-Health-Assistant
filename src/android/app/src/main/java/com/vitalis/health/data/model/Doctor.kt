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
    val name: String,
    val age: Int,
    @SerialName("risk_level")
    val riskLevel: String,
    @SerialName("last_updated")
    val lastUpdated: String
)

@Serializable
data class PatientsResponse(
    val patients: List<Patient>
)
