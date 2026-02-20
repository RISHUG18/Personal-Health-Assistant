package com.vitalis.health.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

// ─────────────────────────────────────────────
// RAG Query Models (AI Health Assistant)
// ─────────────────────────────────────────────

@Serializable
data class RagQueryRequest(
    @SerialName("user_id")
    val userId: String,
    val query: String
)

@Serializable
data class Citation(
    @SerialName("source_file")
    val sourceFile: String,
    val page: Int,
    val snippet: String
)

@Serializable
data class RagData(
    val answer: String,
    val citations: List<Citation> = emptyList()
)

@Serializable
data class RagResponse(
    val status: String,
    val data: RagData
)
