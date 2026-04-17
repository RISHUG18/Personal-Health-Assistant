package com.vitalis.health.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.vitalis.health.data.model.VitalReading
import com.vitalis.health.data.model.VitalsSummaryResponse
import com.vitalis.health.data.model.MetricSummary
import com.vitalis.health.data.local.VitalsSyncPreferences
import com.vitalis.health.data.network.ApiResult
import com.vitalis.health.data.repository.HealthRepository
import com.vitalis.health.healthconnect.HealthConnectAvailability
import com.vitalis.health.healthconnect.HealthConnectManager
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.util.TimeZone

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
    private val vitalsSyncPreferences: VitalsSyncPreferences,
    val healthConnectManager: HealthConnectManager  // Exposed for permission contract
) : ViewModel() {

    // ── UI State ────────────────────────────────────────────────────

    sealed class HealthConnectState {
        data object Checking : HealthConnectState()
        data object Available : HealthConnectState()
        data object NotInstalled : HealthConnectState()
        /** FIX H2: Installed but outdated — user needs to update, not install. */
        data object UpdateRequired : HealthConnectState()
        data object NotSupported : HealthConnectState()
    }

    sealed class PermissionState {
        data object Checking : PermissionState()
        data object Granted : PermissionState()
        data object NotGranted : PermissionState()
        /** User has denied permissions multiple times - must go to Settings to grant */
        data object PermanentlyDenied : PermissionState()
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

    private val _lastSyncedAtMillis = MutableStateFlow<Long?>(null)
    val lastSyncedAtMillis: StateFlow<Long?> = _lastSyncedAtMillis.asStateFlow()


    private var currentUserId: String? = null

    // Track if permission request has been attempted (to detect permanent denial)
    // FIX M2: Track denial count — only flag "permanently denied" after 2+ attempts
    private var permissionDenialCount = 0

    // FIX H3: Guard against re-initialization
    private var isInitialized = false

    // FIX H4: Track running sync job to prevent concurrent execution
    private var syncJob: Job? = null

    // ── Initialization ──────────────────────────────────────────────

    /**
     * Initialize the ViewModel for a specific user.
     * Checks Health Connect availability and permissions.
     */
    fun initialize(userId: String) {
        // FIX H3: Only initialize once per userId. If userId changes, allow re-init.
        if (isInitialized && currentUserId == userId) return
        currentUserId = userId
        isInitialized = true

        viewModelScope.launch {
            _lastSyncedAtMillis.value = vitalsSyncPreferences.getLastSyncTimestampMillis(userId)
        }

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
            // FIX H2: Handle update-required separately from not-installed
            is HealthConnectAvailability.UpdateRequired -> {
                _healthConnectState.value = HealthConnectState.UpdateRequired
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
     * If permissions are still not granted after the user interacted with the dialog,
     * we assume they've permanently denied and need to go to Settings.
     */
    @Suppress("UNUSED_PARAMETER")
    fun onPermissionsResult(granted: Set<String>) {
        viewModelScope.launch {
            if (healthConnectManager.hasAllPermissions()) {
                _permissionState.value = PermissionState.Granted
                permissionDenialCount = 0  // Reset counter on success
                loadVitalsSummary()
            } else {
                permissionDenialCount++
                // FIX M2: Only mark permanently denied after 2+ denial attempts.
                // Health Connect doesn't support shouldShowRequestPermissionRationale(),
                // so we use a heuristic: first denial lets user retry normally.
                _permissionState.value = if (permissionDenialCount >= 2) {
                    PermissionState.PermanentlyDenied
                } else {
                    PermissionState.NotGranted
                }
            }
        }
    }

    /**
     * Called when user returns from Health Connect Settings.
     * Re-check permissions to see if they were granted.
     */
    fun onReturnFromSettings() {
        viewModelScope.launch {
            _permissionState.value = PermissionState.Checking
            if (healthConnectManager.hasAllPermissions()) {
                _permissionState.value = PermissionState.Granted
                loadVitalsSummary()
            } else {
                // Still not granted - show settings prompt again
                _permissionState.value = PermissionState.PermanentlyDenied
            }
        }
    }

    /**
     * Get intent to open Health Connect settings for manual permission grant.
     */
    fun getHealthConnectSettingsIntent() = healthConnectManager.createHealthConnectSettingsIntent()

    // ── Sync Flow: Read → Upload ────────────────────────────────────

    /**
     * Sync vitals from Health Connect to the backend.
     * Reads the last 7 days of data and uploads to the server.
     */
    fun syncVitals() {
        val userId = currentUserId ?: return

        // FIX H4: Prevent concurrent syncs — if already syncing, ignore
        if (syncJob?.isActive == true) return

        syncJob = viewModelScope.launch {
            // Step 1: Read from Health Connect
            _syncState.value = SyncState.Reading

            val readResult = healthConnectManager.readVitalsForDays(days = 7)

            if (readResult.readings.isEmpty()) {
                _syncState.value = SyncState.Error(
                    readResult.errors.firstOrNull() ?: "No vitals data found in Health Connect"
                )
                return@launch
            }

            // FIX H4: Use local variable instead of mutable field to avoid races
            val readings = readResult.readings

            // Step 2: Upload to backend
            _syncState.value = SyncState.Uploading

            when (val result = repository.ingestVitals(userId, readings)) {
                is ApiResult.Success -> {
                    val syncedAtMillis = System.currentTimeMillis()
                    _syncState.value = SyncState.Success(
                        inserted = result.data.inserted,
                        skipped = result.data.skipped
                    )
                    _lastSyncedAtMillis.value = syncedAtMillis
                    vitalsSyncPreferences.setLastSyncTimestampMillis(userId, syncedAtMillis)
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
        // Read the device's IANA timezone ID (e.g. "Asia/Kolkata") at call-time
        // so the backend RPC buckets daily trend points by the user's local calendar,
        // not UTC. This fixes the off-by-one-day issue for users east of UTC.
        val deviceTimezone = TimeZone.getDefault().id

        viewModelScope.launch {
            _summaryState.value = SummaryState.Loading

            when (val result = repository.getVitalsSummary(userId, days = 7, timezone = deviceTimezone)) {
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
