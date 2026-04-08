package com.vitalis.health.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/**
 * Single weekly AI health summary entry from backend.
 */
@Serializable
data class HealthSummary(
    val id: String,
    @SerialName("user_id")
    val userId: String,
    @SerialName("period_type")
    val periodType: String,
    @SerialName("target_role")
    val targetRole: String,
    @SerialName("summary_content")
    val summaryContent: String,
    @SerialName("created_at")
    val createdAt: String,
)

/**
 * Response from GET /api/v1/summaries/{user_id}.
 */
@Serializable
data class SummaryResponse(
    @SerialName("user_id")
    val userId: String,
    val role: String,
    val count: Int,
    val summaries: List<HealthSummary> = emptyList(),
)

/**
 * Response from POST /api/v1/summaries/generate/{user_id}.
 */
@Serializable
data class GenerateSummaryResponse(
    val status: String,
    @SerialName("user_id")
    val userId: String,
    @SerialName("triggered_by")
    val triggeredBy: String? = null,
    val generated: List<String> = emptyList(),
    val errors: List<String> = emptyList(),
)
