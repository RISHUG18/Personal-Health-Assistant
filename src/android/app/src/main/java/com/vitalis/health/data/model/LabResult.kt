package com.vitalis.health.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

// ─────────────────────────────────────────────
// Lab Results Models
// ─────────────────────────────────────────────

/**
 * Response from GET /reports/{report_id}/lab-results.
 */
@Serializable
data class LabResultsResponse(
    @SerialName("report_id")
    val reportId: String,
    val count: Int,
    @SerialName("lab_results")
    val labResults: List<LabResult>
)

/**
 * Individual lab result extracted from a medical report.
 */
@Serializable
data class LabResult(
    val id: String,
    @SerialName("test_name")
    val testName: String,
    val value: String? = null,
    val unit: String? = null,
    @SerialName("reference_range")
    val referenceRange: String? = null,
    @SerialName("abnormal_flag")
    val abnormalFlag: String? = null,
    @SerialName("extracted_from_page")
    val extractedFromPage: Int? = null
)
