package com.vitalis.health.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.vitalis.health.data.model.Alert
import com.vitalis.health.data.model.DashboardData
import com.vitalis.health.data.model.EnvironmentData
import com.vitalis.health.data.model.HealthSummary
import com.vitalis.health.data.model.ReportSummary
import com.vitalis.health.data.model.UserProfile
import com.vitalis.health.data.network.ApiResult
import com.vitalis.health.data.repository.HealthRepository
import kotlinx.coroutines.async
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/**
 * ViewModel for the Dashboard screen.
 *
 * Aggregates data from multiple backend endpoints (user profile, alerts, environment, reports)
 * into a unified [DashboardData] object using concurrent network calls.
 *
 * Handles location permission states and provides fallback UI states when location
 * is unavailable or permissions are denied.
 *
 * Exposes [dashboardState] as observable [StateFlow] that drives the UI.
 */
class DashboardViewModel(
    private val repository: HealthRepository
) : ViewModel() {

    /**
     * Location data for environment API calls.
     */
    data class LocationData(
        val latitude: Double,
        val longitude: Double,
        val city: String? = null
    )

    /**
     * Represents the possible states of the dashboard screen.
     */
    sealed class UiState {
        data object Loading : UiState()
        data class Success(
            val data: DashboardData,
            val locationAvailable: Boolean = true
        ) : UiState()
        data class Error(val message: String) : UiState()
        data class LocationPermissionRequired(
            val data: DashboardData? = null
        ) : UiState()
    }

    private val _dashboardState = MutableStateFlow<UiState>(UiState.Loading)
    val dashboardState: StateFlow<UiState> = _dashboardState.asStateFlow()

    private val _latestSummary = MutableStateFlow<HealthSummary?>(null)
    val latestSummary: StateFlow<HealthSummary?> = _latestSummary.asStateFlow()

    private val _isGeneratingSummary = MutableStateFlow(false)
    val isGeneratingSummary: StateFlow<Boolean> = _isGeneratingSummary.asStateFlow()

    private var currentUserId: String? = null
    private var currentLocation: LocationData? = null
    private var hasLoadedInitialData: Boolean = false

    /**
     * Load dashboard data for the given [userId].
     *
     * Makes concurrent API calls to fetch:
     * - User profile (for greeting)
     * - Alerts (for alert count and list)
     * - Environment data (AQI/weather, if location is provided)
     * - Report history (for timeline)
     *
     * @param userId The user ID to load dashboard data for.
     * @param location Optional location data for environment API call.
     */
    fun loadDashboard(
        userId: String,
        location: LocationData? = null,
        forceRefresh: Boolean = false
    ) {
        val sameUser = currentUserId == userId
        val hasUsableCache = _dashboardState.value is UiState.Success ||
            _dashboardState.value is UiState.LocationPermissionRequired
        if (!forceRefresh && sameUser && hasLoadedInitialData && hasUsableCache) {
            // Keep cached StateFlow data when revisiting Home and only refresh environment if location changed.
            if (location != null && location != currentLocation) {
                updateLocation(location)
            }
            return
        }

        currentUserId = userId
        currentLocation = location

        _dashboardState.value = UiState.Loading

        viewModelScope.launch {
            // Make concurrent network calls using async
            val userProfileDeferred = async { repository.getUserProfile(userId) }
            val alertsDeferred = async { repository.getAlerts(userId) }
            val reportsDeferred = async { repository.getUserReports() }
            val environmentDeferred = if (location != null) {
                async {
                    repository.getEnvironment(
                        userId,
                        location.latitude,
                        location.longitude,
                        location.city
                    )
                }
            } else null

            // Await all results
            val userProfileResult = userProfileDeferred.await()
            val alertsResult = alertsDeferred.await()
            val reportsResult = reportsDeferred.await()
            val environmentResult = environmentDeferred?.await()

            // Handle results and build dashboard data
            when {
                userProfileResult is ApiResult.Error -> {
                    _dashboardState.value = UiState.Error(
                        userProfileResult.message
                    )
                }
                alertsResult is ApiResult.Error -> {
                    _dashboardState.value = UiState.Error(
                        alertsResult.message
                    )
                }
                else -> {
                    val userProfile = (userProfileResult as ApiResult.Success<UserProfile>).data
                    val alerts = (alertsResult as ApiResult.Success<List<Alert>>).data

                    // Environment is optional - null if location not provided or if API fails
                    val environment = when (environmentResult) {
                        is ApiResult.Success -> environmentResult.data
                        else -> null
                    }

                    // Reports are optional - empty list if API fails
                    val reports = when (reportsResult) {
                        is ApiResult.Success -> reportsResult.data
                        else -> emptyList()
                    }

                    val dashboardData = DashboardData(
                        userId = userId,
                        greeting = buildGreeting(userProfile.fullName),
                        activeAlertsCount = alerts.size,
                        alerts = alerts.map { alert ->
                            com.vitalis.health.data.model.DashboardAlert(
                                id = alert.id,
                                severity = alert.severity,
                                reason = alert.reason,
                                createdAt = alert.createdAt
                            )
                        },
                        environment = environment,
                        reports = reports
                    )

                    _dashboardState.value = UiState.Success(
                        data = dashboardData,
                        locationAvailable = environment != null
                    )
                    hasLoadedInitialData = true
                    fetchLatestSummary()
                }
            }
        }
    }

    /**
     * Update location and refresh environment data.
     * Does not reload user profile, alerts, or reports.
     */
    fun updateLocation(location: LocationData) {
        currentLocation = location
        val userId = currentUserId ?: return

        viewModelScope.launch {
            val currentState = _dashboardState.value
            if (currentState is UiState.Success) {
                // Keep existing data, just update environment
                when (val result = repository.getEnvironment(
                    userId,
                    location.latitude,
                    location.longitude,
                    location.city
                )) {
                    is ApiResult.Success -> {
                        _dashboardState.value = UiState.Success(
                            data = currentState.data.copy(environment = result.data),
                            locationAvailable = true
                        )
                    }
                    is ApiResult.Error -> {
                        // Keep existing data, mark location as unavailable
                        _dashboardState.value = UiState.Success(
                            data = currentState.data.copy(environment = null),
                            locationAvailable = false
                        )
                    }
                }
            }
        }
    }

    /**
     * Called when location permission is denied.
     * Loads dashboard without environment data.
     */
    fun onLocationPermissionDenied(userId: String) {
        loadDashboard(userId, location = null)
    }

    /**
     * Returns true when this ViewModel already has dashboard data cached for [userId].
     */
    fun hasCachedDashboard(userId: String): Boolean {
        if (!hasLoadedInitialData || currentUserId != userId) return false
        return _dashboardState.value is UiState.Success ||
            _dashboardState.value is UiState.LocationPermissionRequired
    }

    /**
     * Manually refresh dashboard data using the last known user and location.
     */
    fun refreshDashboard() {
        val userId = currentUserId ?: return
        loadDashboard(userId, currentLocation, forceRefresh = true)
    }

    /** Fetch the latest weekly summary for the current dashboard user. */
    fun fetchLatestSummary() {
        val userId = currentUserId ?: return

        viewModelScope.launch {
            when (val result = repository.getLatestSummary(userId)) {
                is ApiResult.Success -> {
                    _latestSummary.value = result.data.summaries.firstOrNull()
                }
                is ApiResult.Error -> {
                    _latestSummary.value = null
                }
            }
        }
    }

    /** Trigger summary generation and refresh the latest summary on success. */
    fun generateNewSummary() {
        val userId = currentUserId ?: return
        if (_isGeneratingSummary.value) return

        viewModelScope.launch {
            _isGeneratingSummary.value = true
            try {
                when (repository.generateSummary(userId)) {
                    is ApiResult.Success -> fetchLatestSummary()
                    is ApiResult.Error -> {
                        // Keep existing summary content on generation failure.
                    }
                }
            } finally {
                _isGeneratingSummary.value = false
            }
        }
    }

    /**
     * Clears cached dashboard/session context so next load performs a fresh network fetch.
     */
    fun clearCachedDashboard() {
        currentUserId = null
        currentLocation = null
        hasLoadedInitialData = false
        _latestSummary.value = null
        _isGeneratingSummary.value = false
        _dashboardState.value = UiState.Loading
    }

    /**
     * Retry loading dashboard with current parameters.
     */
    fun retry() {
        val userId = currentUserId ?: return
        loadDashboard(userId, currentLocation, forceRefresh = true)
    }

    private fun buildGreeting(fullName: String): String {
        val firstName = fullName.split(" ").firstOrNull() ?: fullName
        val hour = java.util.Calendar.getInstance().get(java.util.Calendar.HOUR_OF_DAY)
        val timeOfDay = when {
            hour < 12 -> "Good morning"
            hour < 17 -> "Good afternoon"
            else -> "Good evening"
        }
        return "$timeOfDay, $firstName"
    }
}
