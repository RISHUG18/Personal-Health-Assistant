package com.vitalis.health.healthconnect

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.provider.Settings
import androidx.health.connect.client.HealthConnectClient
import androidx.health.connect.client.PermissionController
import androidx.health.connect.client.permission.HealthPermission
import androidx.health.connect.client.records.*
import androidx.health.connect.client.request.ReadRecordsRequest
import androidx.health.connect.client.time.TimeRangeFilter
import com.vitalis.health.data.model.VitalReading
import com.vitalis.health.data.model.VitalsMetricType
import java.time.Instant
import java.time.format.DateTimeFormatter
import java.time.temporal.ChronoUnit
import kotlin.reflect.KClass

/**
 * Health Connect availability status.
 */
sealed class HealthConnectAvailability {
    data object Available : HealthConnectAvailability()
    data object NotInstalled : HealthConnectAvailability()
    /** FIX H2: Installed but needs a newer version to work with this app. */
    data object UpdateRequired : HealthConnectAvailability()
    data object NotSupported : HealthConnectAvailability()
}

/**
 * Result of a permission check with detailed status.
 */
sealed class PermissionCheckResult {
    data object AllGranted : PermissionCheckResult()
    data class PartiallyGranted(val granted: Set<String>, val missing: Set<String>) : PermissionCheckResult()
    data object NoneGranted : PermissionCheckResult()
    data object ClientNotInitialized : PermissionCheckResult()
}

/**
 * Result of reading vitals from Health Connect.
 */
data class HealthConnectReadResult(
    val readings: List<VitalReading>,
    val errors: List<String> = emptyList()
)

/**
 * Manager class for interacting with Android Health Connect API.
 *
 * Responsibilities:
 * - Check Health Connect availability
 * - Request and check permissions
 * - Read health metrics (heart rate, steps, sleep, etc.)
 * - Convert Health Connect records to [VitalReading] models
 */
class HealthConnectManager(private val context: Context) {

    private var healthConnectClient: HealthConnectClient? = null

    companion object {
        /** All permissions required by the Vitalis app. */
        val REQUIRED_PERMISSIONS = setOf(
            HealthPermission.getReadPermission(StepsRecord::class),
            HealthPermission.getReadPermission(HeartRateRecord::class),
            HealthPermission.getReadPermission(RestingHeartRateRecord::class),
            HealthPermission.getReadPermission(HeartRateVariabilityRmssdRecord::class),
            HealthPermission.getReadPermission(OxygenSaturationRecord::class),
            HealthPermission.getReadPermission(SleepSessionRecord::class),
            HealthPermission.getReadPermission(ActiveCaloriesBurnedRecord::class),
            HealthPermission.getReadPermission(TotalCaloriesBurnedRecord::class),
        )

        private const val HEALTH_CONNECT_PACKAGE = "com.google.android.apps.healthdata"
        private const val ACTION_HEALTH_CONNECT_SETTINGS = "androidx.health.ACTION_HEALTH_CONNECT_SETTINGS"
        private val ISO_FORMATTER = DateTimeFormatter.ISO_INSTANT
    }

    // ── Availability & Installation ─────────────────────────────────

    /**
     * Check if Health Connect is available on this device.
     */
    fun checkAvailability(): HealthConnectAvailability {
        // Health Connect requires API 26+ but is only bundled on API 34+
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) {
            return HealthConnectAvailability.NotSupported
        }

        return try {
            val status = HealthConnectClient.getSdkStatus(context, HEALTH_CONNECT_PACKAGE)
            when (status) {
                HealthConnectClient.SDK_AVAILABLE -> {
                    healthConnectClient = HealthConnectClient.getOrCreate(context)
                    HealthConnectAvailability.Available
                }
                HealthConnectClient.SDK_UNAVAILABLE_PROVIDER_UPDATE_REQUIRED -> {
                    // FIX H2: Correctly distinguish "needs update" from "not installed"
                    HealthConnectAvailability.UpdateRequired
                }
                else -> HealthConnectAvailability.NotSupported
            }
        } catch (e: Exception) {
            // Handle any unexpected errors during Health Connect initialization
            HealthConnectAvailability.NotSupported
        }
    }

    /**
     * Create an intent to open the Play Store for Health Connect installation.
     */
    fun createInstallIntent(): Intent {
        val uri = Uri.parse("market://details?id=$HEALTH_CONNECT_PACKAGE")
        return Intent(Intent.ACTION_VIEW, uri).apply {
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        }
    }

    /**
     * Create an intent to open Health Connect app settings for permission management.
     * Users can manually grant permissions here if they previously denied them.
     */
    fun createHealthConnectSettingsIntent(): Intent {
        return Intent(ACTION_HEALTH_CONNECT_SETTINGS).apply {
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        }
    }

    // ── Permissions ─────────────────────────────────────────────────

    /**
     * Create a permission request contract for use with ActivityResultLauncher.
     */
    fun createPermissionRequestContract() = PermissionController.createRequestPermissionResultContract()

    /**
     * Check if all required permissions are granted.
     */
    suspend fun hasAllPermissions(): Boolean {
        val client = healthConnectClient ?: return false
        val granted = client.permissionController.getGrantedPermissions()
        return REQUIRED_PERMISSIONS.all { it in granted }
    }

    /**
     * Get detailed permission check result.
     * Returns whether permissions are all granted, partially granted, or none granted.
     */
    suspend fun checkPermissionsDetailed(): PermissionCheckResult {
        val client = healthConnectClient ?: return PermissionCheckResult.ClientNotInitialized
        val granted = client.permissionController.getGrantedPermissions()
        val missing = REQUIRED_PERMISSIONS - granted
        val grantedRequired = REQUIRED_PERMISSIONS.intersect(granted)

        return when {
            missing.isEmpty() -> PermissionCheckResult.AllGranted
            grantedRequired.isEmpty() -> PermissionCheckResult.NoneGranted
            else -> PermissionCheckResult.PartiallyGranted(grantedRequired, missing)
        }
    }

    /**
     * Get the set of permissions that are not yet granted.
     */
    suspend fun getMissingPermissions(): Set<String> {
        val client = healthConnectClient ?: return  REQUIRED_PERMISSIONS
        val granted = client.permissionController.getGrantedPermissions()
        return REQUIRED_PERMISSIONS - granted
    }

    // ── Reading Health Data ─────────────────────────────────────────

    /**
     * Read all supported vitals for the specified time range.
     *
     * @param startTime Start of the time range (default: 24 hours ago)
     * @param endTime End of the time range (default: now)
     * @param deviceId Optional device identifier to tag readings
     * @return [HealthConnectReadResult] with readings and any errors
     */
    suspend fun readVitals(
        startTime: Instant = Instant.now().minus(24, ChronoUnit.HOURS),
        endTime: Instant = Instant.now(),
        deviceId: String? = "health_connect"
    ): HealthConnectReadResult {
        val client = healthConnectClient
            ?: return HealthConnectReadResult(emptyList(), listOf("Health Connect not initialized"))

        val timeRange = TimeRangeFilter.between(startTime, endTime)
        val readings = mutableListOf<VitalReading>()
        val errors = mutableListOf<String>()

        // Read each metric type
        readSteps(client, timeRange, deviceId, readings, errors)
        readHeartRate(client, timeRange, deviceId, readings, errors)
        readRestingHeartRate(client, timeRange, deviceId, readings, errors)
        readHrv(client, timeRange, deviceId, readings, errors)
        readSpO2(client, timeRange, deviceId, readings, errors)
        readSleep(client, timeRange, deviceId, readings, errors)
        readActiveCalories(client, timeRange, deviceId, readings, errors)
        // NOTE: readTotalCalories removed — TotalCaloriesBurnedRecord includes BMR
        // and would double-count with ActiveCaloriesBurnedRecord under the same
        // CALORIES_BURNED metric type. Active calories is the correct fitness metric.

        return HealthConnectReadResult(readings, errors)
    }

    /**
     * Read vitals for the last N days (aggregated daily).
     */
    suspend fun readVitalsForDays(
        days: Int = 7,
        deviceId: String? = "health_connect"
    ): HealthConnectReadResult {
        val endTime = Instant.now()
        val startTime = endTime.minus(days.toLong(), ChronoUnit.DAYS)
        return readVitals(startTime, endTime, deviceId)
    }

    // ── Private Read Methods ────────────────────────────────────────

    /**
     * FIX H1: Generic paginated read helper. Health Connect caps responses
        * at ~1000 records per page. This follows the pageToken chain to collect
     * ALL records in the requested time range.
     */
    private suspend fun <T : Record> readAllRecords(
        client: HealthConnectClient,
        recordType: KClass<T>,
        timeRange: TimeRangeFilter
    ): List<T> {
        val allRecords = mutableListOf<T>()
        var pageToken: String? = null

        do {
            val request = ReadRecordsRequest(
                recordType = recordType,
                timeRangeFilter = timeRange,
                pageToken = pageToken
            )
            val response = client.readRecords(request)
            allRecords.addAll(response.records)
            // FIX: AndroidX ReadRecordsResponse exposes `pageToken`.
            // Using the wrong property name would silently break pagination.
            pageToken = response.pageToken  // null when no more pages
        } while (pageToken != null)

        return allRecords
    }

    private suspend fun readSteps(
        client: HealthConnectClient,
        timeRange: TimeRangeFilter,
        deviceId: String?,
        readings: MutableList<VitalReading>,
        errors: MutableList<String>
    ) {
        try {
            // FIX H1: Use paginated read to capture ALL step records
            val records = readAllRecords(client, StepsRecord::class, timeRange)
            records.forEach { record ->
                readings.add(
                    VitalReading(
                        recordedAt = formatInstant(record.endTime),
                        metricType = VitalsMetricType.STEPS,
                        value = record.count.toDouble(),
                        unit = "steps",
                        deviceId = deviceId
                    )
                )
            }
        } catch (e: Exception) {
            errors.add("Failed to read steps: ${e.message}")
        }
    }

    private suspend fun readHeartRate(
        client: HealthConnectClient,
        timeRange: TimeRangeFilter,
        deviceId: String?,
        readings: MutableList<VitalReading>,
        errors: MutableList<String>
    ) {
        try {
            // FIX H1: Use paginated read — heart rate can have thousands of samples over 7 days
            val records = readAllRecords(client, HeartRateRecord::class, timeRange)
            records.forEach { record ->
                record.samples.forEach { sample ->
                    readings.add(
                        VitalReading(
                            recordedAt = formatInstant(sample.time),
                            metricType = VitalsMetricType.HEART_RATE,
                            value = sample.beatsPerMinute.toDouble(),
                            unit = "bpm",
                            deviceId = deviceId
                        )
                    )
                }
            }
        } catch (e: Exception) {
            errors.add("Failed to read heart rate: ${e.message}")
        }
    }

    private suspend fun readRestingHeartRate(
        client: HealthConnectClient,
        timeRange: TimeRangeFilter,
        deviceId: String?,
        readings: MutableList<VitalReading>,
        errors: MutableList<String>
    ) {
        try {
            // FIX H1: Paginated read
            val records = readAllRecords(client, RestingHeartRateRecord::class, timeRange)
            records.forEach { record ->
                readings.add(
                    VitalReading(
                        recordedAt = formatInstant(record.time),
                        metricType = VitalsMetricType.RESTING_HEART_RATE,
                        value = record.beatsPerMinute.toDouble(),
                        unit = "bpm",
                        deviceId = deviceId
                    )
                )
            }
        } catch (e: Exception) {
            errors.add("Failed to read resting heart rate: ${e.message}")
        }
    }

    private suspend fun readHrv(
        client: HealthConnectClient,
        timeRange: TimeRangeFilter,
        deviceId: String?,
        readings: MutableList<VitalReading>,
        errors: MutableList<String>
    ) {
        try {
            // FIX H1: Paginated read
            val records = readAllRecords(client, HeartRateVariabilityRmssdRecord::class, timeRange)
            records.forEach { record ->
                readings.add(
                    VitalReading(
                        recordedAt = formatInstant(record.time),
                        metricType = VitalsMetricType.HRV_MS,
                        value = record.heartRateVariabilityMillis,
                        unit = "ms",
                        deviceId = deviceId
                    )
                )
            }
        } catch (e: Exception) {
            errors.add("Failed to read HRV: ${e.message}")
        }
    }

    private suspend fun readSpO2(
        client: HealthConnectClient,
        timeRange: TimeRangeFilter,
        deviceId: String?,
        readings: MutableList<VitalReading>,
        errors: MutableList<String>
    ) {
        try {
            // FIX H1: Paginated read
            val records = readAllRecords(client, OxygenSaturationRecord::class, timeRange)
            records.forEach { record ->
                readings.add(
                    VitalReading(
                        recordedAt = formatInstant(record.time),
                        metricType = VitalsMetricType.SPO2,
                        value = record.percentage.value,
                        unit = "%",
                        deviceId = deviceId
                    )
                )
            }
        } catch (e: Exception) {
            errors.add("Failed to read SpO2: ${e.message}")
        }
    }

    private suspend fun readSleep(
        client: HealthConnectClient,
        timeRange: TimeRangeFilter,
        deviceId: String?,
        readings: MutableList<VitalReading>,
        errors: MutableList<String>
    ) {
        try {
            // FIX H1: Paginated read
            val records = readAllRecords(client, SleepSessionRecord::class, timeRange)
            records.forEach { record ->
                // Calculate total sleep duration
                val durationMinutes = ChronoUnit.MINUTES.between(record.startTime, record.endTime)
                readings.add(
                    VitalReading(
                        recordedAt = formatInstant(record.endTime),
                        metricType = VitalsMetricType.SLEEP_MINUTES,
                        value = durationMinutes.toDouble(),
                        unit = "min",
                        deviceId = deviceId
                    )
                )

                // Calculate deep sleep from stages if available
                var deepSleepMinutes = 0L
                record.stages.forEach { stage ->
                    if (stage.stage == SleepSessionRecord.STAGE_TYPE_DEEP) {
                        deepSleepMinutes += ChronoUnit.MINUTES.between(stage.startTime, stage.endTime)
                    }
                }
                if (deepSleepMinutes > 0) {
                    readings.add(
                        VitalReading(
                            recordedAt = formatInstant(record.endTime),
                            metricType = VitalsMetricType.DEEP_SLEEP_MINUTES,
                            value = deepSleepMinutes.toDouble(),
                            unit = "min",
                            deviceId = deviceId
                        )
                    )
                }
            }
        } catch (e: Exception) {
            errors.add("Failed to read sleep: ${e.message}")
        }
    }

    private suspend fun readActiveCalories(
        client: HealthConnectClient,
        timeRange: TimeRangeFilter,
        deviceId: String?,
        readings: MutableList<VitalReading>,
        errors: MutableList<String>
    ) {
        try {
            // FIX H1: Paginated read
            val records = readAllRecords(client, ActiveCaloriesBurnedRecord::class, timeRange)
            records.forEach { record ->
                readings.add(
                    VitalReading(
                        recordedAt = formatInstant(record.endTime),
                        metricType = VitalsMetricType.CALORIES_BURNED,
                        value = record.energy.inKilocalories,
                        unit = "kcal",
                        deviceId = deviceId
                    )
                )
            }
        } catch (e: Exception) {
            errors.add("Failed to read active calories: ${e.message}")
        }
    }



    // ── Utilities ───────────────────────────────────────────────────

    private fun formatInstant(instant: Instant): String {
        return ISO_FORMATTER.format(instant)
    }
}
