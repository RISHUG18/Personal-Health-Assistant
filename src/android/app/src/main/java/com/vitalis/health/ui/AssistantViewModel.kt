package com.vitalis.health.ui

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.vitalis.health.data.model.RagData
import com.vitalis.health.data.network.ApiResult
import com.vitalis.health.data.repository.HealthRepository
import com.vitalis.health.location.LocationTracker
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Job
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/**
 * ViewModel for the AI Health Assistant (RAG) chat screen.
 */
class AssistantViewModel(
    private val repository: HealthRepository,
    private val locationTracker: LocationTracker
) : ViewModel() {

    sealed class UiState {
        data object Idle : UiState()
        data object Loading : UiState()
        data class Success(val data: RagData) : UiState()
        data class Error(val message: String) : UiState()
    }

    /** Tracks the entire conversation history for display in the chat UI. */
    data class ChatMessage(
        val isUser: Boolean,
        val text: String,
        val citations: List<com.vitalis.health.data.model.Citation> = emptyList()
    )

    private val _uiState = MutableLiveData<UiState>(UiState.Idle)
    val uiState: LiveData<UiState> = _uiState

    private val _chatHistory = MutableLiveData<List<ChatMessage>>(emptyList())
    val chatHistory: LiveData<List<ChatMessage>> = _chatHistory

    private val _partialTranscript = MutableStateFlow("")
    val partialTranscript: StateFlow<String> = _partialTranscript.asStateFlow()

    private val _voiceDraft = MutableStateFlow("")
    val voiceDraft: StateFlow<String> = _voiceDraft.asStateFlow()

    private val _voiceCaptureError = MutableStateFlow<String?>(null)
    val voiceCaptureError: StateFlow<String?> = _voiceCaptureError.asStateFlow()

    private val _isGenerating = MutableStateFlow(false)
    val isGenerating: StateFlow<Boolean> = _isGenerating.asStateFlow()

    private var generationJob: Job? = null

    /**
     * Send a natural-language [query] on behalf of [userId].
     * The result is appended to [chatHistory] automatically.
     * Location data is automatically fetched and included in the query if available.
     */
    fun sendQuery(userId: String, query: String) {
        if (_isGenerating.value) return

        // Append user message immediately
        appendMessage(ChatMessage(isUser = true, text = query))
        _uiState.value = UiState.Loading

        generationJob = viewModelScope.launch {
            _isGenerating.value = true
            try {
                // Try to fetch user's current location
                val location = try {
                    locationTracker.getCurrentLocation()
                } catch (_: Exception) {
                    null // Gracefully handle any location fetch errors
                }

                // Call the repository with location parameters (null if location unavailable)
                when (
                    val result = repository.queryAssistant(
                        userId = userId,
                        query = query,
                        userLat = location?.latitude,
                        userLon = location?.longitude,
                        userLocation = null // Could add reverse geocoding here if needed
                    )
                ) {
                    is ApiResult.Success -> {
                        val ragData = result.data
                        appendMessage(
                            ChatMessage(
                                isUser = false,
                                text = ragData.answer,
                                citations = ragData.citations
                            )
                        )
                        _uiState.postValue(UiState.Success(ragData))
                    }

                    is ApiResult.Error -> {
                        appendMessage(
                            ChatMessage(isUser = false, text = "Sorry, I couldn't process that: ${result.message}")
                        )
                        _uiState.postValue(UiState.Error(result.message))
                    }
                }
            } catch (_: CancellationException) {
                _uiState.postValue(UiState.Idle)
            } finally {
                _isGenerating.value = false
                val currentJob = currentCoroutineContext()[Job]
                if (generationJob == currentJob) {
                    generationJob = null
                }
            }
        }
    }

    private val _voiceResponse = MutableLiveData<String?>(null)
    val voiceResponse: LiveData<String?> = _voiceResponse

    fun updatePartialTranscript(text: String) {
        val normalized = text.trim()
        if (normalized.isNotEmpty()) {
            _partialTranscript.value = normalized
            _voiceDraft.value = normalized
            _voiceCaptureError.value = null
        }
    }

    fun setVoiceDraft(text: String) {
        _voiceDraft.value = text
        _voiceCaptureError.value = null
    }

    fun setVoiceCaptureError(message: String?) {
        _voiceCaptureError.value = message
    }

    fun resetVoiceComposer() {
        _partialTranscript.value = ""
        _voiceDraft.value = ""
        _voiceCaptureError.value = null
    }

    fun clearVoiceResponse() {
        _voiceResponse.value = null
    }

    fun sendVoiceQuery(userId: String, query: String) {
        val cleanedQuery = query.trim()
        if (cleanedQuery.isEmpty()) {
            return
        }
        if (_isGenerating.value) {
            return
        }

        _partialTranscript.value = cleanedQuery
        _voiceDraft.value = cleanedQuery
        _voiceCaptureError.value = null
        appendMessage(ChatMessage(isUser = true, text = cleanedQuery))
        _uiState.value = UiState.Loading

        generationJob = viewModelScope.launch {
            _isGenerating.value = true
            try {
                when (val result = repository.postVoiceChat(userId, cleanedQuery)) {
                    is ApiResult.Success -> {
                        val responseText = result.data.responseText
                        appendMessage(ChatMessage(isUser = false, text = responseText))
                        _voiceResponse.postValue(responseText)
                        _uiState.postValue(UiState.Success(RagData(answer = responseText)))
                    }

                    is ApiResult.Error -> {
                        appendMessage(ChatMessage(isUser = false, text = "Voice error: ${result.message}"))
                        _voiceCaptureError.value = result.message
                        _uiState.postValue(UiState.Error(result.message))
                    }
                }
            } catch (_: CancellationException) {
                _uiState.postValue(UiState.Idle)
            } finally {
                _isGenerating.value = false
                val currentJob = currentCoroutineContext()[Job]
                if (generationJob == currentJob) {
                    generationJob = null
                }
            }
        }
    }

    fun stopGeneration() {
        generationJob?.cancel()
        generationJob = null
        _isGenerating.value = false
        if (_uiState.value is UiState.Loading) {
            _uiState.value = UiState.Idle
        }
    }

    private fun appendMessage(message: ChatMessage) {
        val current = _chatHistory.value.orEmpty().toMutableList()
        current.add(message)
        _chatHistory.postValue(current)
    }

    fun clearConversation() {
        stopGeneration()
        _chatHistory.value = emptyList()
        _uiState.value = UiState.Idle
        _voiceResponse.value = null
        _partialTranscript.value = ""
        _voiceDraft.value = ""
        _voiceCaptureError.value = null
    }
}
