package com.vitalis.health.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.vitalis.health.data.model.Alert
import com.vitalis.health.data.network.ApiResult
import com.vitalis.health.data.repository.HealthRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/**
 * ViewModel for the Alerts screen.
 *
 * Fetches alerts from GET /alerts/{user_id} and exposes them as [StateFlow].
 * Alerts include severity levels (high, medium, low) and evidence linking
 * back to the source report/lab result that triggered the alert.
 */
class AlertsViewModel(
    private val repository: HealthRepository
) : ViewModel() {

    sealed class UiState {
        data object Loading : UiState()
        data class Success(val alerts: List<Alert>) : UiState()
        data class Error(val message: String) : UiState()
    }

    private val _alertsState = MutableStateFlow<UiState>(UiState.Loading)
    val alertsState: StateFlow<UiState> = _alertsState.asStateFlow()

    private var currentUserId: String? = null

    /**
     * Fetch all alerts for [userId].
     * Alerts are sorted by severity (high → medium → low) via the repository.
     */
    fun loadAlerts(userId: String) {
        currentUserId = userId
        _alertsState.value = UiState.Loading

        viewModelScope.launch {
            when (val result = repository.getAlerts(userId)) {
                is ApiResult.Success -> _alertsState.value = UiState.Success(result.data)
                is ApiResult.Error   -> _alertsState.value = UiState.Error(result.message)
            }
        }
    }

    /**
     * Retry loading alerts with the last used userId.
     */
    fun retry() {
        val userId = currentUserId ?: return
        loadAlerts(userId)
    }
}
