package com.vitalis.health.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

// ─────────────────────────────────────────────
// Alert Models (matching backend /alerts/{user_id} response)
// ─────────────────────────────────────────────

/**
 * Evidence attached to an alert, linking it to the source report/lab result.
 */
@Serializable
data class AlertEvidence(
    val id: String? = null,
    @SerialName("report_id")
    val reportId: String? = null,
    @SerialName("lab_result_id")
    val labResultId: String? = null,
    @SerialName("ocr_text_snippet")
    val ocrTextSnippet: String? = null
)

/**
 * Alert from the backend /alerts/{user_id} endpoint.
 */
@Serializable
data class Alert(
    val id: String,
    val severity: String,
    val reason: String,
    @SerialName("created_at")
    val createdAt: String,
    val evidence: List<AlertEvidence> = emptyList()
) {
    /** Title derived from the reason for UI display. */
    val title: String
        get() = reason.take(50).let { if (reason.length > 50) "$it…" else it }

    /** Full message is the reason itself. */
    val message: String
        get() = reason
}

/**
 * Response wrapper from GET /alerts/{user_id}.
 */
@Serializable
data class AlertsApiResponse(
    @SerialName("user_id")
    val userId: String,
    val count: Int,
    val alerts: List<Alert>
)
