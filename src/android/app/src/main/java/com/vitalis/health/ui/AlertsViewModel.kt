package com.vitalis.health.ui

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.vitalis.health.data.model.Alert
import com.vitalis.health.data.network.ApiResult
import com.vitalis.health.data.repository.HealthRepository
import kotlinx.coroutines.launch

/**
 * ViewModel for the Alerts screen.
 *
 * Exposes [alertsState] as observable [LiveData].
 */
class AlertsViewModel(
    private val repository: HealthRepository
) : ViewModel() {

    sealed class UiState {
        data object Loading : UiState()
        data class Success(val alerts: List<Alert>) : UiState()
        data class Error(val message: String) : UiState()
    }

    private val _alertsState = MutableLiveData<UiState>()
    val alertsState: LiveData<UiState> = _alertsState

    /**
     * Fetch all alerts for [userId].
     */
    fun loadAlerts(userId: String) {
        _alertsState.value = UiState.Loading

        viewModelScope.launch {
            when (val result = repository.getAlerts(userId)) {
                is ApiResult.Success -> _alertsState.postValue(UiState.Success(result.data))
                is ApiResult.Error   -> _alertsState.postValue(UiState.Error(result.message))
            }
        }
    }
}
