package com.vitalis.health.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.vitalis.health.data.model.VitalReading
import com.vitalis.health.data.model.VitalsSummaryResponse
import com.vitalis.health.data.model.MetricSummary
import com.vitalis.health.data.network.ApiResult
import com.vitalis.health.data.repository.HealthRepository
import com.vitalis.health.healthconnect.HealthConnectAvailability
import com.vitalis.health.healthconnect.HealthConnectManager
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/**
 * ViewModel for the Vitals Dashboard screen.
 *
 * Manages:
 * - Health Connect availability and permissions
 * - Reading vitals from Health Connect
 * - Syncing data to the backend
 * - Displaying 7-day vitals summary from the backend
 */
class VitalsViewModel(
    private val repository: HealthRepository,
    val healthConnectManager: HealthConnectManager  // Exposed for permission contract
) : ViewModel() {

    // ── UI State ────────────────────────────────────────────────────

    sealed class HealthConnectState {
        data object Checking : HealthConnectState()
        data object Available : HealthConnectState()
        data object NotInstalled : HealthConnectState()
        data object NotSupported : HealthConnectState()
    }

    sealed class PermissionState {
        data object Checking : PermissionState()
        data object Granted : PermissionState()
        data object NotGranted : PermissionState()
    }

    sealed class SyncState {
        data object Idle : SyncState()
        data object Reading : SyncState()
        data object Uploading : SyncState()
        data class Success(val inserted: Int, val skipped: Int) : SyncState()
        data class Error(val message: String) : SyncState()
    }

    sealed class SummaryState {
        data object Loading : SummaryState()
        data class Success(val summary: VitalsSummaryResponse) : SummaryState()
        data class Error(val message: String) : SummaryState()
        data object Empty : SummaryState()
    }

    // ── State Flows ─────────────────────────────────────────────────

    private val _healthConnectState = MutableStateFlow<HealthConnectState>(HealthConnectState.Checking)
    val healthConnectState: StateFlow<HealthConnectState> = _healthConnectState.asStateFlow()

    private val _permissionState = MutableStateFlow<PermissionState>(PermissionState.Checking)
    val permissionState: StateFlow<PermissionState> = _permissionState.asStateFlow()

    private val _syncState = MutableStateFlow<SyncState>(SyncState.Idle)
    val syncState: StateFlow<SyncState> = _syncState.asStateFlow()

    private val _summaryState = MutableStateFlow<SummaryState>(SummaryState.Loading)
    val summaryState: StateFlow<SummaryState> = _summaryState.asStateFlow()

    // Store readings temporarily between read and upload
    private var pendingReadings: List<VitalReading> = emptyList()

    private var currentUserId: String? = null

    // ── Initialization ──────────────────────────────────────────────

    /**
     * Initialize the ViewModel for a specific user.
     * Checks Health Connect availability and permissions.
     */
    fun initialize(userId: String) {
        currentUserId = userId
        checkHealthConnectAvailability()
    }

    // ── Health Connect Availability ─────────────────────────────────

    fun checkHealthConnectAvailability() {
        _healthConnectState.value = HealthConnectState.Checking

        when (healthConnectManager.checkAvailability()) {
            is HealthConnectAvailability.Available -> {
                _healthConnectState.value = HealthConnectState.Available
                checkPermissions()
            }
            is HealthConnectAvailability.NotInstalled -> {
                _healthConnectState.value = HealthConnectState.NotInstalled
            }
            is HealthConnectAvailability.NotSupported -> {
                _healthConnectState.value = HealthConnectState.NotSupported
            }
        }
    }

    /**
     * Get the intent to install Health Connect from Play Store.
     */
    fun getInstallIntent() = healthConnectManager.createInstallIntent()

    // ── Permissions ─────────────────────────────────────────────────

    fun checkPermissions() {
        viewModelScope.launch {
            _permissionState.value = PermissionState.Checking
            val hasPermissions = healthConnectManager.hasAllPermissions()
            _permissionState.value = if (hasPermissions) {
                // Permissions granted, load summary
                loadVitalsSummary()
                PermissionState.Granted
            } else {
                PermissionState.NotGranted
            }
        }
    }

    /**
     * Get the required Health Connect permissions for the permission request.
     */
    fun getRequiredPermissions() = HealthConnectManager.REQUIRED_PERMISSIONS

    /**
     * Called after permission request result is received.
     */
    fun onPermissionsResult(granted: Set<String>) {
        viewModelScope.launch {
            if (healthConnectManager.hasAllPermissions()) {
                _permissionState.value = PermissionState.Granted
                loadVitalsSummary()
            } else {
                _permissionState.value = PermissionState.NotGranted
            }
        }
    }

    // ── Sync Flow: Read → Upload ────────────────────────────────────

    /**
     * Sync vitals from Health Connect to the backend.
     * Reads the last 7 days of data and uploads to the server.
     */
    fun syncVitals() {
        val userId = currentUserId ?: return

        viewModelScope.launch {
            // Step 1: Read from Health Connect
            _syncState.value = SyncState.Reading

            val readResult = healthConnectManager.readVitalsForDays(days = 7)

            if (readResult.readings.isEmpty()) {
                _syncState.value = SyncState.Error(
                    readResult.errors.firstOrNull() ?: "No vitals data found in Health Connect"
                )
                return@launch
            }

            pendingReadings = readResult.readings

            // Step 2: Upload to backend
            _syncState.value = SyncState.Uploading

            when (val result = repository.ingestVitals(userId, pendingReadings)) {
                is ApiResult.Success -> {
                    _syncState.value = SyncState.Success(
                        inserted = result.data.inserted,
                        skipped = result.data.skipped
                    )
                    // Refresh summary after successful sync
                    loadVitalsSummary()
                }
                is ApiResult.Error -> {
                    _syncState.value = SyncState.Error(result.message)
                }
            }
        }
    }

    /**
     * Reset sync state to idle (e.g., after showing success/error message).
     */
    fun resetSyncState() {
        _syncState.value = SyncState.Idle
    }

    // ── Load Summary from Backend ───────────────────────────────────

    /**
     * Load the 7-day vitals summary from the backend.
     */
    fun loadVitalsSummary() {
        val userId = currentUserId ?: return

        viewModelScope.launch {
            _summaryState.value = SummaryState.Loading

            when (val result = repository.getVitalsSummary(userId, days = 7)) {
                is ApiResult.Success -> {
                    if (result.data.metricCount > 0) {
                        _summaryState.value = SummaryState.Success(result.data)
                    } else {
                        _summaryState.value = SummaryState.Empty
                    }
                }
                is ApiResult.Error -> {
                    _summaryState.value = SummaryState.Error(result.message)
                }
            }
        }
    }

    // ── Convenience Getters for UI ──────────────────────────────────

    /**
     * Get a specific metric summary from the current state.
     */
    fun getMetricSummary(metricType: String): MetricSummary? {
        val state = _summaryState.value
        return if (state is SummaryState.Success) {
            state.summary.summary[metricType]
        } else null
    }

    /**
     * Get the total steps from today (latest reading).
     */
    fun getTodaySteps(): Int? = getMetricSummary("steps")?.latest?.toInt()

    /**
     * Get the average heart rate over the summary period.
     */
    fun getAverageHeartRate(): Int? = getMetricSummary("heart_rate")?.avg?.toInt()

    /**
     * Get the total sleep hours (latest reading converted to hours).
     */
    fun getTotalSleepHours(): Double? {
        val sleepMinutes = getMetricSummary("sleep_minutes")?.latest
        return sleepMinutes?.let { it / 60.0 }
    }

    /**
     * Get the latest SpO2 percentage.
     */
    fun getLatestSpO2(): Int? = getMetricSummary("spo2")?.latest?.toInt()

    /**
     * Get the resting heart rate.
     */
    fun getRestingHeartRate(): Int? = getMetricSummary("resting_heart_rate")?.latest?.toInt()

    /**
     * Get the HRV (Heart Rate Variability) in milliseconds.
     */
    fun getHrvMs(): Int? = getMetricSummary("hrv_ms")?.latest?.toInt()
}
