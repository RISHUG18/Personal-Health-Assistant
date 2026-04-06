package com.vitalis.health.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class VoiceChatRequest(
    val text: String,
    @SerialName("user_id")
    val userId: String
)

@Serializable
data class VoiceChatResponse(
    val transcript: String,
    @SerialName("response_text")
    val responseText: String,
    @SerialName("audio_base64")
    val audioBase64: String? = null,
    @SerialName("audio_format")
    val audioFormat: String? = null
)
