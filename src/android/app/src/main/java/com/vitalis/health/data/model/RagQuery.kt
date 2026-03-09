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
    val snippet: String,
    // Added with DB migration 002 — report chunk citation metadata
    @SerialName("source_filename")
    val sourceFilename: String? = null,
    @SerialName("source_url")
    val sourceUrl: String? = null,
    @SerialName("page_number")
    val pageNumber: Int? = null
)

@Serializable
data class RagData(
    val answer: String,
    val citations: List<Citation> = emptyList()
)

/**
 * Matches the real backend response from POST /api/v1/rag_query.
 *
 * The backend returns a flat object:
 *   { answer, context, chunks_retrieved, grounding_available, model, llm_error }
 *
 * The large `context` field is intentionally omitted — kotlinx-serialization
 * ignoreUnknownKeys skips it during deserialization.
 */
@Serializable
data class RagResponse(
    val answer: String,
    @SerialName("chunks_retrieved")
    val chunksRetrieved: Int = 0,
    @SerialName("grounding_available")
    val groundingAvailable: Boolean = false,
    val model: String = "",
    @SerialName("llm_error")
    val llmError: String? = null
)
