package com.vitalis.health.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

// ─────────────────────────────────────────────
// Alert Models
// ─────────────────────────────────────────────

@Serializable
data class AlertEvidence(
    val source: String? = null,
    val metric: String? = null,
    val value: String? = null,
    val threshold: String? = null,
    // Report chunk citation fields added with DB migration 002
    @SerialName("source_filename")
    val sourceFilename: String? = null,
    @SerialName("source_url")
    val sourceUrl: String? = null,
    @SerialName("page_number")
    val pageNumber: Int? = null
)

@Serializable
data class Alert(
    val id: String,
    val title: String,
    val message: String,
    val severity: String,
    val timestamp: String,
    val evidence: AlertEvidence? = null
)

@Serializable
data class AlertsData(
    val alerts: List<Alert>
)

@Serializable
data class AlertsResponse(
    val status: String,
    val data: AlertsData
)
