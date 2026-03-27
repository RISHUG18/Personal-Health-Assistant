package com.vitalis.health.ui

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.vitalis.health.data.model.RagData
import com.vitalis.health.data.network.ApiResult
import com.vitalis.health.data.repository.HealthRepository
import com.vitalis.health.location.LocationTracker
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

    /**
     * Send a natural-language [query] on behalf of [userId].
     * The result is appended to [chatHistory] automatically.
     * Location data is automatically fetched and included in the query if available.
     */
    fun sendQuery(userId: String, query: String) {
        // Append user message immediately
        appendMessage(ChatMessage(isUser = true, text = query))
        _uiState.value = UiState.Loading

        viewModelScope.launch {
            // Try to fetch user's current location
            val location = try {
                locationTracker.getCurrentLocation()
            } catch (e: Exception) {
                null // Gracefully handle any location fetch errors
            }

            // Call the repository with location parameters (null if location unavailable)
            when (val result = repository.queryAssistant(
                userId = userId,
                query = query,
                userLat = location?.latitude,
                userLon = location?.longitude,
                userLocation = null // Could add reverse geocoding here if needed
            )) {
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
        }
    }

    private fun appendMessage(message: ChatMessage) {
        val current = _chatHistory.value.orEmpty().toMutableList()
        current.add(message)
        _chatHistory.postValue(current)
    }
}
