package com.vitalis.health.ui

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.vitalis.health.data.model.DashboardData
import com.vitalis.health.data.network.ApiResult
import com.vitalis.health.data.repository.HealthRepository
import kotlinx.coroutines.launch

/**
 * ViewModel for the Dashboard screen.
 *
 * Exposes [dashboardState] as observable [LiveData] that drives the UI.
 */
class DashboardViewModel(
    private val repository: HealthRepository
) : ViewModel() {

    /** Represents the possible states of the dashboard screen. */
    sealed class UiState {
        data object Loading : UiState()
        data class Success(val data: DashboardData) : UiState()
        data class Error(val message: String) : UiState()
    }

    private val _dashboardState = MutableLiveData<UiState>()
    val dashboardState: LiveData<UiState> = _dashboardState

    /**
     * Load dashboard data for the given [userId].
     */
    fun loadDashboard(userId: String) {
        _dashboardState.value = UiState.Loading

        viewModelScope.launch {
            when (val result = repository.getDashboard(userId)) {
                is ApiResult.Success -> _dashboardState.postValue(UiState.Success(result.data))
                is ApiResult.Error   -> _dashboardState.postValue(UiState.Error(result.message))
            }
        }
    }
}
