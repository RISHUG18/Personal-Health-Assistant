package com.vitalis.health.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

// ─────────────────────────────────────────────
// Report Upload Models
// ─────────────────────────────────────────────

@Serializable
data class ReportUploadResponse(
    val status: String,
    @SerialName("report_id")
    val reportId: String,
    val message: String
)
