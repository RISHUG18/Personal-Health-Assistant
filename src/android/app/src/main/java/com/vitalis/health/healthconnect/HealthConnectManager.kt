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
import androidx.health.connect.client.request.AggregateGroupByPeriodRequest
import androidx.health.connect.client.request.ReadRecordsRequest
import androidx.health.connect.client.time.TimeRangeFilter
import com.vitalis.health.data.model.VitalReading
import com.vitalis.health.data.model.VitalsMetricType
import java.time.Instant
import java.time.LocalDateTime
import java.time.Period
import java.time.ZoneId
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
            // Mi Band 6 (Zepp Life) writes TotalCaloriesBurnedRecord, not Active.
            // Both permissions are requested so the app works across device brands.
            HealthPermission.getReadPermission(ActiveCaloriesBurnedRecord::class),
            HealthPermission.getReadPermission(TotalCaloriesBurnedRecord::class),
        )

        private const val HEALTH_CONNECT_PACKAGE = "com.google.android.apps.healthdata"
        private const val ACTION_HEALTH_CONNECT_SETTINGS = "androidx.health.ACTION_HEALTH_CONNECT_SETTINGS"
        private val ISO_FORMATTER = DateTimeFormatter.ISO_INSTANT
        // ISO_OFFSET_DATE_TIME emits e.g. '2026-04-14T00:00:00+05:30' — the zone
        // offset is critical so the backend stores the correct UTC instant instead
        // of treating a naive local midnight as UTC midnight.
        private val ISO_OFFSET_DATE_TIME_FORMATTER = DateTimeFormatter.ISO_OFFSET_DATE_TIME
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
     * @return [HealthConnectReadResult] with readings and any errors
     */
    suspend fun readVitals(
        startTime: Instant = Instant.now().minus(24, ChronoUnit.HOURS),
        endTime: Instant = Instant.now()
    ): HealthConnectReadResult {
        val client = healthConnectClient
            ?: return HealthConnectReadResult(emptyList(), listOf("Health Connect not initialized"))

        // Raw-record readers (HRV, SpO2, Sleep) use Instant-based TimeRangeFilter.
        val instantTimeRange = TimeRangeFilter.between(startTime, endTime)

        // Period-aggregation readers (Steps, HR, RHR, Calories) need LocalDateTime
        // boundaries so that Health Connect can align buckets to calendar-day midnight
        // instead of creating 24-hour rolling windows that bleed across days.
        val localEndTime = LocalDateTime.now()
        // FIX A: Add +1 so a fractional-day range (e.g. 24h) still covers the full
        // start calendar day.  ChronoUnit.DAYS.between() truncates; without +1 a
        // 24 h window returns 0 days → coerceAtLeast(1) → only today fetched.
        val daysDiff = ChronoUnit.DAYS.between(startTime, endTime) + 1
        val localStartTime = localEndTime.minusDays(daysDiff).truncatedTo(ChronoUnit.DAYS)

        val readings = mutableListOf<VitalReading>()
        val errors = mutableListOf<String>()

        // Period-aggregated metrics (midnight-aligned calendar days)
        readSteps(client, localStartTime, localEndTime, readings, errors)
        readHeartRate(client, localStartTime, localEndTime, readings, errors)
        readRestingHeartRate(client, localStartTime, localEndTime, readings, errors)
        // Read total calories (active + BMR). Zepp Life (Mi Band 6) writes
        // TotalCaloriesBurnedRecord exclusively; devices that write both types
        // are handled by preferring total calories to match Google Fit's display.
        readTotalCalories(client, localStartTime, localEndTime, readings, errors)

        // Raw-record metrics
        readHrv(client, instantTimeRange, readings, errors)
        readSpO2(client, instantTimeRange, readings, errors)
        readSleep(client, instantTimeRange, readings, errors)

        return HealthConnectReadResult(readings, errors)
    }

    /**
     * Read vitals for the last N days (aggregated daily).
     *
     * Uses midnight-snapped LocalDateTime boundaries for period aggregation so
     * that each bucket corresponds to a real calendar day.
     */
    suspend fun readVitalsForDays(
        days: Int = 7
    ): HealthConnectReadResult {
        val client = healthConnectClient
            ?: return HealthConnectReadResult(emptyList(), listOf("Health Connect not initialized"))

        // Snap to midnight so period-aggregation buckets align with calendar days.
        val localEndTime = LocalDateTime.now()
        val localStartTime = localEndTime.minusDays(days.toLong()).truncatedTo(ChronoUnit.DAYS)

        // For raw-record readers we still need Instant boundaries.
        val zone = ZoneId.systemDefault()
        val instantStart = localStartTime.atZone(zone).toInstant()
        val instantEnd = localEndTime.atZone(zone).toInstant()
        val instantTimeRange = TimeRangeFilter.between(instantStart, instantEnd)

        val readings = mutableListOf<VitalReading>()
        val errors = mutableListOf<String>()

        // Period-aggregated metrics (midnight-aligned calendar days)
        readSteps(client, localStartTime, localEndTime, readings, errors)
        readHeartRate(client, localStartTime, localEndTime, readings, errors)
        readRestingHeartRate(client, localStartTime, localEndTime, readings, errors)
        readTotalCalories(client, localStartTime, localEndTime, readings, errors)

        // Raw-record metrics
        readHrv(client, instantTimeRange, readings, errors)
        readSpO2(client, instantTimeRange, readings, errors)
        readSleep(client, instantTimeRange, readings, errors)

        return HealthConnectReadResult(readings, errors)
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

    /**
     * Read steps using daily aggregation via [AggregateGroupByPeriodRequest].
     *
     * Health Connect stores steps as tiny sub-minute segments. Fetching them
     * raw produces thousands of rows that corrupt backend aggregation and
     * create massive payloads. Daily bucketing yields one reading per day.
     *
     * By accepting [LocalDateTime] boundaries and slicing by [Period.ofDays(1)],
     * Health Connect aligns each bucket to calendar-day midnight in the device's
     * local timezone, eliminating the "phantom 8th day" that appeared when 24-hour
     * [Duration] buckets were used with [Instant] boundaries.
     */
    private suspend fun readSteps(
        client: HealthConnectClient,
        localStartTime: LocalDateTime,
        localEndTime: LocalDateTime,
        readings: MutableList<VitalReading>,
        errors: MutableList<String>
    ) {
        try {
            val result = client.aggregateGroupByPeriod(
                AggregateGroupByPeriodRequest(
                    metrics = setOf(StepsRecord.COUNT_TOTAL),
                    timeRangeFilter = TimeRangeFilter.between(localStartTime, localEndTime),
                    timeRangeSlicer = Period.ofDays(1)
                )
            )
            result.forEach { bucket ->
                val steps = bucket.result[StepsRecord.COUNT_TOTAL]
                if (steps != null) {
                    readings.add(
                        VitalReading(
                            // Use bucket.startTime (local midnight) as the canonical
                            // timestamp for each day. The backend upserts with overwrite=true
                            // so a re-sync always writes the latest cumulative total over
                            // any earlier partial count stored from a previous sync.
                            recordedAt = formatLocalDateTime(bucket.startTime),
                            metricType = VitalsMetricType.STEPS,
                            value = steps.toDouble(),
                            unit = "steps",
                            deviceId = getDeviceName(null),
                            overwrite = true  // overwrite stale daily total on re-sync
                        )
                    )
                }
            }
        } catch (e: Exception) {
            errors.add("Failed to read steps: ${e.message}")
        }
    }

    private suspend fun readHeartRate(
        client: HealthConnectClient,
        localStartTime: LocalDateTime,
        localEndTime: LocalDateTime,
        readings: MutableList<VitalReading>,
        errors: MutableList<String>
    ) {
        try {
            // FIX HR-MINMAX: Request BPM_AVG, BPM_MIN, and BPM_MAX in a single
            // aggregation call so the backend receives true per-day min/max rather
            // than computing min/max from daily averages (which underestimates range).
            val result = client.aggregateGroupByPeriod(
                AggregateGroupByPeriodRequest(
                    metrics = setOf(
                        HeartRateRecord.BPM_AVG,
                        HeartRateRecord.BPM_MIN,
                        HeartRateRecord.BPM_MAX
                    ),
                    timeRangeFilter = TimeRangeFilter.between(localStartTime, localEndTime),
                    timeRangeSlicer = Period.ofDays(1)
                )
            )
            result.forEach { bucket ->
                val ts = formatLocalDateTime(bucket.startTime)
                val device = getDeviceName(null)

                // Average BPM for this calendar day (weighted by Health Connect)
                bucket.result[HeartRateRecord.BPM_AVG]?.let { bpm ->
                    readings.add(
                        VitalReading(
                            recordedAt = ts,
                            metricType = VitalsMetricType.HEART_RATE,
                            value = bpm.toDouble(),
                            unit = "bpm",
                            deviceId = device,
                            overwrite = true
                        )
                    )
                }

                // True minimum BPM sample in this calendar day
                bucket.result[HeartRateRecord.BPM_MIN]?.let { bpmMin ->
                    readings.add(
                        VitalReading(
                            recordedAt = ts,
                            metricType = VitalsMetricType.HEART_RATE_MIN,
                            value = bpmMin.toDouble(),
                            unit = "bpm",
                            deviceId = device,
                            overwrite = true
                        )
                    )
                }

                // True maximum BPM sample in this calendar day
                bucket.result[HeartRateRecord.BPM_MAX]?.let { bpmMax ->
                    readings.add(
                        VitalReading(
                            recordedAt = ts,
                            metricType = VitalsMetricType.HEART_RATE_MAX,
                            value = bpmMax.toDouble(),
                            unit = "bpm",
                            deviceId = device,
                            overwrite = true
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
        localStartTime: LocalDateTime,
        localEndTime: LocalDateTime,
        readings: MutableList<VitalReading>,
        errors: MutableList<String>
    ) {
        try {
            val result = client.aggregateGroupByPeriod(
                AggregateGroupByPeriodRequest(
                    metrics = setOf(RestingHeartRateRecord.BPM_AVG),
                    timeRangeFilter = TimeRangeFilter.between(localStartTime, localEndTime),
                    timeRangeSlicer = Period.ofDays(1)
                )
            )
            result.forEach { bucket ->
                val bpm = bucket.result[RestingHeartRateRecord.BPM_AVG]
                if (bpm != null) {
                    readings.add(
                        VitalReading(
                            recordedAt = formatLocalDateTime(bucket.startTime),
                            metricType = VitalsMetricType.RESTING_HEART_RATE,
                            value = bpm.toDouble(),
                            unit = "bpm",
                            deviceId = getDeviceName(null),
                            overwrite = true
                        )
                    )
                }
            }
        } catch (e: Exception) {
            errors.add("Failed to read resting heart rate: ${e.message}")
        }
    }


    private suspend fun readHrv(
        client: HealthConnectClient,
        timeRange: TimeRangeFilter,
        readings: MutableList<VitalReading>,
        errors: MutableList<String>
    ) {
        try {
            // connect-client alpha08 does not expose aggregate metrics for HRV,
            // so we fold raw points to one daily average per day client-side.
            val records = readAllRecords(client, HeartRateVariabilityRmssdRecord::class, timeRange)
            records
                .groupBy { it.time.atZone(ZoneId.systemDefault()).toLocalDate() }
                .entries
                .sortedBy { it.key }
                .forEach { entry ->
                    val dayRecords = entry.value
                    val average = dayRecords.map { it.heartRateVariabilityMillis }.average()
                    val latestRecord = dayRecords.maxByOrNull { it.time } ?: return@forEach

                    readings.add(
                        VitalReading(
                            recordedAt = formatInstant(latestRecord.time),
                            metricType = VitalsMetricType.HRV_MS,
                            value = average,
                            unit = "ms",
                            deviceId = getDeviceName(latestRecord.metadata.device?.model)
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
        readings: MutableList<VitalReading>,
        errors: MutableList<String>
    ) {
        try {
            // connect-client alpha08 does not expose aggregate metrics for SpO2,
            // so we fold raw points to one daily average per day client-side.
            val records = readAllRecords(client, OxygenSaturationRecord::class, timeRange)
            records
                .groupBy { it.time.atZone(ZoneId.systemDefault()).toLocalDate() }
                .entries
                .sortedBy { it.key }
                .forEach { entry ->
                    val dayRecords = entry.value
                    val average = dayRecords.map { it.percentage.value }.average()
                    val latestRecord = dayRecords.maxByOrNull { it.time } ?: return@forEach

                    readings.add(
                        VitalReading(
                            recordedAt = formatInstant(latestRecord.time),
                            metricType = VitalsMetricType.SPO2,
                            value = average,
                            unit = "%",
                            deviceId = getDeviceName(latestRecord.metadata.device?.model)
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
        readings: MutableList<VitalReading>,
        errors: MutableList<String>
    ) {
        try {
            val records = readAllRecords(client, SleepSessionRecord::class, timeRange)
            val zone = ZoneId.systemDefault()

            // Group sessions by the LOCAL DATE of their end-time (wakeup).
            // This handles multi-session nights (naps + main sleep) and sessions
            // that span midnight, attributing them all to the day the person woke up.
            val byDate = records.groupBy { it.endTime.atZone(zone).toLocalDate() }

            byDate.entries.sortedBy { it.key }.forEach { (_, sessions) ->
                val device = getDeviceName(sessions.first().metadata.device?.model)

                // Pick the latest wake-up time in this day's sessions as the
                // canonical recorded_at — provides a unique, real event timestamp.
                val latestEndTime = sessions.maxOf { it.endTime }

                // ── Total sleep ──────────────────────────────────────────────
                val totalMinutes = sessions.sumOf { session ->
                    ChronoUnit.MINUTES.between(session.startTime, session.endTime)
                }
                if (totalMinutes > 0) {
                    readings.add(
                        VitalReading(
                            recordedAt = formatInstant(latestEndTime),
                            metricType = VitalsMetricType.SLEEP_MINUTES,
                            value = totalMinutes.toDouble(),
                            unit = "min",
                            deviceId = device
                        )
                    )
                }

                // ── Deep sleep ───────────────────────────────────────────────
                // Zepp Life (Mi Band 6) may write deep sleep in two ways:
                //  Pattern A — single session with embedded stages list
                //    record.stages contains Stage(type=STAGE_TYPE_DEEP, start, end)
                //  Pattern B — separate SleepSessionRecord per stage
                //    entire record has no sub-stages; its session-level type is
                //    surfaced via the first (and only) stage, or the record itself
                //    is tagged as a deep-sleep segment via a stage with type DEEP.
                //
                // We handle both by summing STAGE_TYPE_DEEP sub-stages first, then
                // falling back to the session duration when the session's own sole
                // stage IS STAGE_TYPE_DEEP.
                var deepSleepMinutes = 0L
                sessions.forEach { session ->
                    if (session.stages.isEmpty()) {
                        // Pattern B: no sub-stages — skip; we cannot determine type
                    } else {
                        // Pattern A: sum from sub-stages tagged as DEEP
                        val deepFromStages = session.stages
                            .filter { it.stage == SleepSessionRecord.STAGE_TYPE_DEEP }
                            .sumOf { ChronoUnit.MINUTES.between(it.startTime, it.endTime) }

                        if (deepFromStages > 0) {
                            deepSleepMinutes += deepFromStages
                        } else if (
                            session.stages.size == 1 &&
                            session.stages[0].stage == SleepSessionRecord.STAGE_TYPE_DEEP
                        ) {
                            // Pattern B variant: session has exactly one stage and it is DEEP
                            deepSleepMinutes += ChronoUnit.MINUTES.between(
                                session.startTime, session.endTime
                            )
                        }
                    }
                }

                // Only emit a row when real deep-stage time was found.
                // Emitting 0s pollutes the DB average and causes the card to show 0.
                if (deepSleepMinutes > 0) {
                    readings.add(
                        VitalReading(
                            recordedAt = formatInstant(latestEndTime),
                            metricType = VitalsMetricType.DEEP_SLEEP_MINUTES,
                            value = deepSleepMinutes.toDouble(),
                            unit = "min",
                            deviceId = device
                        )
                    )
                }
            }
        } catch (e: Exception) {
            errors.add("Failed to read sleep: ${e.message}")
        }
    }


    /**
     * Read active calories using daily aggregation via [AggregateGroupByPeriodRequest].
     *
     * Like steps, Health Connect stores calories as many tiny sub-minute
     * segments. Daily bucketing yields one reading per day. LocalDateTime
     * boundaries ensure buckets align to calendar-day midnight.
     */
    /**
     * Read total calories burned (active + BMR) using daily aggregation.
     *
     * Zepp Life (Mi Band 6 companion) writes [TotalCaloriesBurnedRecord] to
     * Health Connect — it never writes [ActiveCaloriesBurnedRecord]. Reading
     * only active calories therefore produces ZERO readings for Mi Band 6 users,
     * causing the calories card to show "--" even though data is available.
     *
     * Total calories also matches Google Fit's default "Calories" display, which
     * shows active + BMR (resting metabolic rate).
     */
    private suspend fun readTotalCalories(
        client: HealthConnectClient,
        localStartTime: LocalDateTime,
        localEndTime: LocalDateTime,
        readings: MutableList<VitalReading>,
        errors: MutableList<String>
    ) {
        try {
            val result = client.aggregateGroupByPeriod(
                AggregateGroupByPeriodRequest(
                    metrics = setOf(TotalCaloriesBurnedRecord.ENERGY_TOTAL),
                    timeRangeFilter = TimeRangeFilter.between(localStartTime, localEndTime),
                    timeRangeSlicer = Period.ofDays(1)
                )
            )
            result.forEach { bucket ->
                val energy = bucket.result[TotalCaloriesBurnedRecord.ENERGY_TOTAL]
                if (energy != null) {
                    readings.add(
                        VitalReading(
                            recordedAt = formatLocalDateTime(bucket.startTime),
                            metricType = VitalsMetricType.CALORIES_BURNED,
                            value = energy.inKilocalories,
                            unit = "kcal",
                            deviceId = getDeviceName(null),
                            overwrite = true
                        )
                    )
                }
            }
        } catch (e: Exception) {
            errors.add("Failed to read total calories: ${e.message}")
        }
    }



    // ── Utilities ───────────────────────────────────────────────────

    /**
     * Return the actual device identifier from Health Connect record metadata,
     * falling back to the Android device model when the record doesn't carry one.
     */
    private fun getDeviceName(recordDeviceId: String?): String {
        return recordDeviceId ?: Build.MODEL
    }

    private fun formatInstant(instant: Instant): String {
        return ISO_FORMATTER.format(instant)
    }

    /**
     * Format a [LocalDateTime] as a timezone-aware ISO-8601 string.
     *
     * FIX B: We must attach the device's zone offset before serialising.  Without
     * the offset the string looks like "2026-04-14T00:00:00" — a *naive* datetime
     * that the backend Pydantic model stores as UTC midnight.  For a UTC+5:30 user
     * that shifts every reading 5 h 30 m into the future, causing daily bucketing
     * in the DB to disagree with Google Fit which tracks local-midnight boundaries.
     *
     * With the offset the string becomes "2026-04-14T00:00:00+05:30" and the
     * backend correctly converts it to "2026-04-13T18:30:00Z" before storage.
     */
    private fun formatLocalDateTime(localDateTime: LocalDateTime): String {
        val zoneOffset = ZoneId.systemDefault().rules.getOffset(localDateTime)
        return ISO_OFFSET_DATE_TIME_FORMATTER.format(localDateTime.atOffset(zoneOffset))
    }
}
