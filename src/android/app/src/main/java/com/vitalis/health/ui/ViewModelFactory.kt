package com.vitalis.health.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import com.vitalis.health.data.local.TokenManager
import com.vitalis.health.data.repository.HealthRepository
import com.vitalis.health.location.LocationTracker

/**
 * Generic [ViewModelProvider.Factory] used to inject [HealthRepository],
 * [TokenManager], and [LocationTracker] into ViewModels that require them.
 *
 * Replace with Hilt @HiltViewModel in a DI-enabled project.
 */
class ViewModelFactory(
    private val repository: HealthRepository,
    private val tokenManager: TokenManager,
    private val locationTracker: LocationTracker
) : ViewModelProvider.Factory {

    @Suppress("UNCHECKED_CAST")
    override fun <T : ViewModel> create(modelClass: Class<T>): T = when {
        modelClass.isAssignableFrom(AuthViewModel::class.java) ->
            AuthViewModel(repository, tokenManager) as T

        modelClass.isAssignableFrom(DashboardViewModel::class.java) ->
            DashboardViewModel(repository) as T

        modelClass.isAssignableFrom(AlertsViewModel::class.java) ->
            AlertsViewModel(repository) as T

        modelClass.isAssignableFrom(AssistantViewModel::class.java) ->
            AssistantViewModel(repository, locationTracker) as T

        modelClass.isAssignableFrom(ReportUploadViewModel::class.java) ->
            ReportUploadViewModel(repository) as T

        modelClass.isAssignableFrom(ReportDetailViewModel::class.java) ->
            ReportDetailViewModel(repository) as T

        else -> throw IllegalArgumentException("Unknown ViewModel: ${modelClass.name}")
    }
}
