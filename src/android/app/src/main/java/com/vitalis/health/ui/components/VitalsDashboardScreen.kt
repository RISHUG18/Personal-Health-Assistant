package com.vitalis.health.ui.components

import android.content.Intent
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Sync
import androidx.compose.material.icons.automirrored.outlined.DirectionsRun
import androidx.compose.material.icons.outlined.Bed
import androidx.compose.material.icons.outlined.Favorite
import androidx.compose.material.icons.outlined.FavoriteBorder
import androidx.compose.material.icons.outlined.HealthAndSafety
import androidx.compose.material.icons.outlined.LocalFireDepartment
import androidx.compose.material.icons.outlined.MonitorHeart
import androidx.compose.material.icons.outlined.PlayArrow
import androidx.compose.material.icons.outlined.Refresh
import androidx.compose.material.icons.outlined.Speed
import androidx.compose.material.icons.outlined.Timeline
import androidx.compose.material.icons.outlined.Warning
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.runtime.DisposableEffect
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import com.vitalis.health.data.model.MetricSummary
import com.vitalis.health.data.model.VitalsMetricType
import com.vitalis.health.healthconnect.HealthConnectManager
import com.vitalis.health.ui.VitalsViewModel
import com.vitalis.health.ui.theme.MetricTextStyle
import com.vitalis.health.ui.theme.VitalisDanger
import com.vitalis.health.ui.theme.VitalisPrimary
import com.vitalis.health.ui.theme.VitalisPrimaryLight
import com.vitalis.health.ui.theme.VitalisSuccess
import com.vitalis.health.ui.theme.VitalisTextMuted
import com.vitalis.health.ui.theme.VitalisTextSecondary
import com.vitalis.health.ui.theme.VitalisWarning

/**
 * Vitals Dashboard screen displaying wearable health data.
 *
 * Features:
 * - Health Connect availability check
 * - Permission request flow
 * - Sync data from Health Connect to backend
 * - Display 7-day vitals summary cards
 */
@Composable
fun VitalsDashboardScreen(
    viewModel: VitalsViewModel,
    userId: String,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val healthConnectState by viewModel.healthConnectState.collectAsState()
    val permissionState by viewModel.permissionState.collectAsState()
    val syncState by viewModel.syncState.collectAsState()
    val summaryState by viewModel.summaryState.collectAsState()

    // FIX M1: Key contract on viewModel so it recreates if the VM instance changes
    val permissionContract = remember(viewModel) {
        viewModel.healthConnectManager.createPermissionRequestContract()
    }

    // Permission launcher - uses the stable contract
    val permissionLauncher = rememberLauncherForActivityResult(
        contract = permissionContract
    ) { granted ->
        viewModel.onPermissionsResult(granted)
    }

    // Initialize on first composition
    LaunchedEffect(userId) {
        viewModel.initialize(userId)
    }

    // FIX L3: Re-check permissions when the user returns from Settings via back button.
    val lifecycleOwner = LocalLifecycleOwner.current
    DisposableEffect(lifecycleOwner) {
        val observer = LifecycleEventObserver { _, event ->
            if (event == Lifecycle.Event.ON_RESUME) {
                // Only re-check if we're in a permission-pending state
                val currentPermState = viewModel.permissionState.value
                if (currentPermState is VitalsViewModel.PermissionState.PermanentlyDenied ||
                    currentPermState is VitalsViewModel.PermissionState.NotGranted
                ) {
                    viewModel.onReturnFromSettings()
                }
            }
        }
        lifecycleOwner.lifecycle.addObserver(observer)
        onDispose {
            lifecycleOwner.lifecycle.removeObserver(observer)
        }
    }

    Box(
        modifier = modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
    ) {
        when (healthConnectState) {
            is VitalsViewModel.HealthConnectState.Checking -> {
                VitalisLoadingScreen(label = "Checking Health Connect…")
            }

            is VitalsViewModel.HealthConnectState.NotSupported -> {
                HealthConnectUnavailableScreen(
                    message = "Your device does not support Health Connect",
                    subtitle = "Health Connect requires Android 8.0 or higher"
                )
            }

            is VitalsViewModel.HealthConnectState.NotInstalled -> {
                HealthConnectInstallScreen(
                    onInstallClick = {
                        context.startActivity(viewModel.getInstallIntent())
                    }
                )
            }

            // FIX H2: Show "update" messaging when HC is outdated, not "install"
            is VitalsViewModel.HealthConnectState.UpdateRequired -> {
                HealthConnectUpdateScreen(
                    onUpdateClick = {
                        context.startActivity(viewModel.getInstallIntent())
                    }
                )
            }

            is VitalsViewModel.HealthConnectState.Available -> {
                when (permissionState) {
                    is VitalsViewModel.PermissionState.Checking -> {
                        VitalisLoadingScreen(label = "Checking permissions…")
                    }

                    is VitalsViewModel.PermissionState.NotGranted -> {
                        PermissionRequestScreen(
                            onRequestPermissions = {
                                permissionLauncher.launch(viewModel.getRequiredPermissions())
                            }
                        )
                    }

                    is VitalsViewModel.PermissionState.PermanentlyDenied -> {
                        PermissionDeniedScreen(
                            onOpenSettings = {
                                context.startActivity(viewModel.getHealthConnectSettingsIntent())
                            },
                            onRetryPermissions = {
                                viewModel.onReturnFromSettings()
                            }
                        )
                    }

                    is VitalsViewModel.PermissionState.Granted -> {
                        VitalsDashboardContent(
                            summaryState = summaryState,
                            syncState = syncState,
                            onSyncClick = { viewModel.syncVitals() },
                            onRefreshClick = { viewModel.loadVitalsSummary() },
                            onSyncDismiss = { viewModel.resetSyncState() }
                        )
                    }
                }
            }
        }
    }
}

// ═══════════════════════════════════════════════════════════════════════════════
// Sub-screens
// ═══════════════════════════════════════════════════════════════════════════════

@Composable
private fun HealthConnectUnavailableScreen(
    message: String,
    subtitle: String
) {
    VitalisEmptyScreen(
        message = message,
        subtitle = subtitle,
        icon = Icons.Outlined.HealthAndSafety
    )
}

@Composable
private fun HealthConnectInstallScreen(
    onInstallClick: () -> Unit
) {
    Box(
        modifier = Modifier.fillMaxSize(),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(16.dp),
            modifier = Modifier.padding(32.dp)
        ) {
            Icon(
                imageVector = Icons.Outlined.HealthAndSafety,
                contentDescription = null,
                tint = VitalisPrimary,
                modifier = Modifier.size(72.dp)
            )

            Text(
                text = "Health Connect Required",
                style = MaterialTheme.typography.headlineSmall,
                color = MaterialTheme.colorScheme.onBackground,
                textAlign = TextAlign.Center
            )

            Text(
                text = "To sync your wearable data, please install Health Connect from the Play Store.",
                style = MaterialTheme.typography.bodyMedium,
                color = VitalisTextSecondary,
                textAlign = TextAlign.Center
            )

            Spacer(modifier = Modifier.height(8.dp))

            Button(
                onClick = onInstallClick,
                colors = ButtonDefaults.buttonColors(containerColor = VitalisPrimary),
                shape = MaterialTheme.shapes.small
            ) {
                Icon(
                    imageVector = Icons.Outlined.PlayArrow,
                    contentDescription = null,
                    modifier = Modifier.size(20.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text("Install Health Connect")
            }
        }
    }
}

/**
 * FIX H2: Separate screen for when Health Connect is installed but needs an update.
 * Shows "Update" messaging instead of misleading "Install" messaging.
 */
@Composable
private fun HealthConnectUpdateScreen(
    onUpdateClick: () -> Unit
) {
    Box(
        modifier = Modifier.fillMaxSize(),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(16.dp),
            modifier = Modifier.padding(32.dp)
        ) {
            Icon(
                imageVector = Icons.Outlined.Refresh,
                contentDescription = null,
                tint = VitalisWarning,
                modifier = Modifier.size(72.dp)
            )

            Text(
                text = "Health Connect Update Required",
                style = MaterialTheme.typography.headlineSmall,
                color = MaterialTheme.colorScheme.onBackground,
                textAlign = TextAlign.Center
            )

            Text(
                text = "Your version of Health Connect needs to be updated to sync wearable data.",
                style = MaterialTheme.typography.bodyMedium,
                color = VitalisTextSecondary,
                textAlign = TextAlign.Center
            )

            Spacer(modifier = Modifier.height(8.dp))

            Button(
                onClick = onUpdateClick,
                colors = ButtonDefaults.buttonColors(containerColor = VitalisWarning),
                shape = MaterialTheme.shapes.small
            ) {
                Icon(
                    imageVector = Icons.Outlined.Refresh,
                    contentDescription = null,
                    modifier = Modifier.size(20.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text("Update Health Connect")
            }
        }
    }
}

@Composable
private fun PermissionRequestScreen(
    onRequestPermissions: () -> Unit
) {
    Box(
        modifier = Modifier.fillMaxSize(),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(16.dp),
            modifier = Modifier.padding(32.dp)
        ) {
            Box(
                modifier = Modifier
                    .size(80.dp)
                    .clip(CircleShape)
                    .background(VitalisPrimaryLight),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Outlined.MonitorHeart,
                    contentDescription = null,
                    tint = VitalisPrimary,
                    modifier = Modifier.size(40.dp)
                )
            }

            Text(
                text = "Connect Your Health Data",
                style = MaterialTheme.typography.headlineSmall,
                color = MaterialTheme.colorScheme.onBackground,
                textAlign = TextAlign.Center
            )

            Text(
                text = "Grant access to Health Connect to sync your vitals including heart rate, steps, sleep, and more.",
                style = MaterialTheme.typography.bodyMedium,
                color = VitalisTextSecondary,
                textAlign = TextAlign.Center
            )

            // Permission list
            Column(
                verticalArrangement = Arrangement.spacedBy(8.dp),
                modifier = Modifier.padding(vertical = 8.dp)
            ) {
                PermissionItem("Heart Rate & HRV")
                PermissionItem("Steps & Activity")
                PermissionItem("Sleep Data")
                PermissionItem("Blood Oxygen (SpO2)")
                PermissionItem("Calories Burned")
            }

            Spacer(modifier = Modifier.height(8.dp))

            Button(
                onClick = onRequestPermissions,
                colors = ButtonDefaults.buttonColors(containerColor = VitalisPrimary),
                shape = MaterialTheme.shapes.small,
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Grant Permissions", modifier = Modifier.padding(vertical = 4.dp))
            }
        }
    }
}

@Composable
private fun PermissionItem(text: String) {
    Row(
        verticalAlignment = Alignment.CenterVertically,
        modifier = Modifier.fillMaxWidth()
    ) {
        Icon(
            imageVector = Icons.Filled.CheckCircle,
            contentDescription = null,
            tint = VitalisSuccess,
            modifier = Modifier.size(20.dp)
        )
        Spacer(modifier = Modifier.width(12.dp))
        Text(
            text = text,
            style = MaterialTheme.typography.bodyMedium,
            color = VitalisTextSecondary
        )
    }
}

@Composable
private fun PermissionDeniedScreen(
    onOpenSettings: () -> Unit,
    onRetryPermissions: () -> Unit
) {
    Box(
        modifier = Modifier.fillMaxSize(),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(16.dp),
            modifier = Modifier.padding(32.dp)
        ) {
            Box(
                modifier = Modifier
                    .size(80.dp)
                    .clip(CircleShape)
                    .background(VitalisWarning.copy(alpha = 0.1f)),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Outlined.Warning,
                    contentDescription = null,
                    tint = VitalisWarning,
                    modifier = Modifier.size(40.dp)
                )
            }

            Text(
                text = "Permissions Required",
                style = MaterialTheme.typography.headlineSmall,
                color = MaterialTheme.colorScheme.onBackground,
                textAlign = TextAlign.Center
            )

            Text(
                text = "Health Connect permissions were denied. To sync your wearable data, please grant permissions in Health Connect settings.",
                style = MaterialTheme.typography.bodyMedium,
                color = VitalisTextSecondary,
                textAlign = TextAlign.Center
            )

            Spacer(modifier = Modifier.height(8.dp))

            Button(
                onClick = onOpenSettings,
                colors = ButtonDefaults.buttonColors(containerColor = VitalisPrimary),
                shape = MaterialTheme.shapes.small,
                modifier = Modifier.fillMaxWidth()
            ) {
                Icon(
                    imageVector = Icons.Outlined.HealthAndSafety,
                    contentDescription = null,
                    modifier = Modifier.size(20.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text("Open Health Connect Settings")
            }

            OutlinedButton(
                onClick = onRetryPermissions,
                shape = MaterialTheme.shapes.small,
                modifier = Modifier.fillMaxWidth()
            ) {
                Icon(
                    imageVector = Icons.Outlined.Refresh,
                    contentDescription = null,
                    modifier = Modifier.size(20.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text("Check Permissions Again")
            }
        }
    }
}

// ═══════════════════════════════════════════════════════════════════════════════
// Main Dashboard Content
// ═══════════════════════════════════════════════════════════════════════════════

@Composable
private fun VitalsDashboardContent(
    summaryState: VitalsViewModel.SummaryState,
    syncState: VitalsViewModel.SyncState,
    onSyncClick: () -> Unit,
    onRefreshClick: () -> Unit,
    onSyncDismiss: () -> Unit
) {
    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        item {
            Spacer(modifier = Modifier.height(16.dp))

            // Header
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = "Health Vitals",
                        style = MaterialTheme.typography.headlineMedium,
                        color = MaterialTheme.colorScheme.onBackground
                    )
                    Text(
                        text = "7-day summary",
                        style = MaterialTheme.typography.bodyMedium,
                        color = VitalisTextSecondary
                    )
                }

                // Sync button
                SyncButton(
                    syncState = syncState,
                    onClick = onSyncClick
                )
            }
        }

        // Sync status banner
        item {
            AnimatedVisibility(
                visible = syncState !is VitalsViewModel.SyncState.Idle,
                enter = fadeIn(),
                exit = fadeOut()
            ) {
                SyncStatusBanner(
                    syncState = syncState,
                    onDismiss = onSyncDismiss
                )
            }
        }

        // Main content based on summary state
        when (summaryState) {
            is VitalsViewModel.SummaryState.Loading -> {
                item {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(200.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        CircularProgressIndicator(color = VitalisPrimary)
                    }
                }
            }

            is VitalsViewModel.SummaryState.Error -> {
                item {
                    VitalisErrorScreen(
                        message = summaryState.message,
                        title = "Failed to load vitals",
                        onRetry = onRefreshClick
                    )
                }
            }

            is VitalsViewModel.SummaryState.Empty -> {
                item {
                    EmptyVitalsCard(onSyncClick = onSyncClick)
                }
            }

            is VitalsViewModel.SummaryState.Success -> {
                // Key metrics cards row
                item {
                    KeyMetricsRow(summary = summaryState.summary.summary)
                }

                // Detailed metrics cards
                items(getMetricDisplayItems(summaryState.summary.summary)) { item ->
                    MetricDetailCard(
                        title = item.title,
                        icon = item.icon,
                        iconColor = item.color,
                        metricSummary = item.summary,
                        unit = item.unit
                    )
                }
            }
        }

        item {
            Spacer(modifier = Modifier.height(16.dp))
        }
    }
}

// ═══════════════════════════════════════════════════════════════════════════════
// Helper Components
// ═══════════════════════════════════════════════════════════════════════════════

@Composable
private fun SyncButton(
    syncState: VitalsViewModel.SyncState,
    onClick: () -> Unit
) {
    val isLoading = syncState is VitalsViewModel.SyncState.Reading ||
            syncState is VitalsViewModel.SyncState.Uploading

    OutlinedButton(
        onClick = onClick,
        enabled = !isLoading,
        shape = MaterialTheme.shapes.small
    ) {
        if (isLoading) {
            CircularProgressIndicator(
                modifier = Modifier.size(18.dp),
                color = VitalisPrimary,
                strokeWidth = 2.dp
            )
        } else {
            Icon(
                imageVector = Icons.Filled.Sync,
                contentDescription = "Sync",
                modifier = Modifier.size(18.dp)
            )
        }
        Spacer(modifier = Modifier.width(8.dp))
        Text(
            text = when (syncState) {
                is VitalsViewModel.SyncState.Reading -> "Reading…"
                is VitalsViewModel.SyncState.Uploading -> "Uploading…"
                else -> "Sync Now"
            }
        )
    }
}

@Composable
private fun SyncStatusBanner(
    syncState: VitalsViewModel.SyncState,
    onDismiss: () -> Unit
) {
    val (color, icon, message) = when (syncState) {
        is VitalsViewModel.SyncState.Reading -> Triple(
            VitalisWarning,
            Icons.Outlined.Refresh,
            "Reading from Health Connect…"
        )
        is VitalsViewModel.SyncState.Uploading -> Triple(
            VitalisPrimary,
            Icons.Filled.Sync,
            "Uploading to server…"
        )
        is VitalsViewModel.SyncState.Success -> Triple(
            VitalisSuccess,
            Icons.Filled.CheckCircle,
            "Synced ${syncState.inserted} readings (${syncState.skipped} skipped)"
        )
        is VitalsViewModel.SyncState.Error -> Triple(
            VitalisDanger,
            Icons.Outlined.Warning,
            syncState.message
        )
        else -> return
    }

    Surface(
        modifier = Modifier.fillMaxWidth(),
        shape = MaterialTheme.shapes.small,
        color = color.copy(alpha = 0.1f)
    ) {
        Row(
            modifier = Modifier.padding(12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = color,
                modifier = Modifier.size(20.dp)
            )
            Spacer(modifier = Modifier.width(12.dp))
            Text(
                text = message,
                style = MaterialTheme.typography.bodySmall,
                color = color,
                modifier = Modifier.weight(1f)
            )
            if (syncState is VitalsViewModel.SyncState.Success ||
                syncState is VitalsViewModel.SyncState.Error
            ) {
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = "Dismiss",
                    style = MaterialTheme.typography.labelSmall,
                    color = color,
                    modifier = Modifier
                        .clip(RoundedCornerShape(4.dp))
                        .background(color.copy(alpha = 0.1f))
                        .clickable { onDismiss() }
                        .padding(horizontal = 8.dp, vertical = 4.dp)
                )
            }
        }
    }
}

@Composable
private fun EmptyVitalsCard(onSyncClick: () -> Unit) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = MaterialTheme.shapes.medium,
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Icon(
                imageVector = Icons.Outlined.MonitorHeart,
                contentDescription = null,
                tint = VitalisTextMuted,
                modifier = Modifier.size(48.dp)
            )
            Spacer(modifier = Modifier.height(16.dp))
            Text(
                text = "No Vitals Data Yet",
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onSurface
            )
            Text(
                text = "Sync your wearable data to see your health metrics",
                style = MaterialTheme.typography.bodySmall,
                color = VitalisTextSecondary,
                textAlign = TextAlign.Center
            )
            Spacer(modifier = Modifier.height(16.dp))
            Button(
                onClick = onSyncClick,
                colors = ButtonDefaults.buttonColors(containerColor = VitalisPrimary),
                shape = MaterialTheme.shapes.small
            ) {
                Icon(
                    imageVector = Icons.Filled.Sync,
                    contentDescription = null,
                    modifier = Modifier.size(18.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text("Sync Now")
            }
        }
    }
}

@Composable
private fun KeyMetricsRow(summary: Map<String, MetricSummary>) {
    LazyRow(
        horizontalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        // Steps
        summary[VitalsMetricType.STEPS]?.let { metric ->
            item {
                KeyMetricCard(
                    title = "Steps",
                    value = metric.latest?.toInt()?.toString() ?: "--",
                    unit = "",
                    icon = Icons.AutoMirrored.Outlined.DirectionsRun,
                    iconColor = VitalisPrimary
                )
            }
        }

        // Heart Rate
        summary[VitalsMetricType.HEART_RATE]?.let { metric ->
            item {
                KeyMetricCard(
                    title = "Avg HR",
                    value = metric.avg?.toInt()?.toString() ?: "--",
                    unit = "bpm",
                    icon = Icons.Outlined.Favorite,
                    iconColor = VitalisDanger
                )
            }
        }

        // Sleep
        summary[VitalsMetricType.SLEEP_MINUTES]?.let { metric ->
            val hours = metric.latest?.let { it / 60.0 }
            item {
                KeyMetricCard(
                    title = "Sleep",
                    value = hours?.let { String.format("%.1f", it) } ?: "--",
                    unit = "hrs",
                    icon = Icons.Outlined.Bed,
                    iconColor = Color(0xFF6366F1) // Indigo
                )
            }
        }

        // SpO2
        summary[VitalsMetricType.SPO2]?.let { metric ->
            item {
                KeyMetricCard(
                    title = "SpO2",
                    value = metric.latest?.toInt()?.toString() ?: "--",
                    unit = "%",
                    icon = Icons.Outlined.Speed,
                    iconColor = VitalisSuccess
                )
            }
        }
    }
}

@Composable
private fun KeyMetricCard(
    title: String,
    value: String,
    unit: String,
    icon: ImageVector,
    iconColor: Color
) {
    Card(
        modifier = Modifier.width(140.dp),
        shape = MaterialTheme.shapes.medium,
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically
            ) {
                Box(
                    modifier = Modifier
                        .size(32.dp)
                        .clip(RoundedCornerShape(8.dp))
                        .background(iconColor.copy(alpha = 0.1f)),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = icon,
                        contentDescription = null,
                        tint = iconColor,
                        modifier = Modifier.size(18.dp)
                    )
                }
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = title,
                    style = MaterialTheme.typography.labelSmall,
                    color = VitalisTextSecondary
                )
            }
            Spacer(modifier = Modifier.height(12.dp))
            Row(
                verticalAlignment = Alignment.Bottom
            ) {
                Text(
                    text = value,
                    style = MetricTextStyle.copy(fontSize = 28.sp),
                    color = MaterialTheme.colorScheme.onSurface
                )
                if (unit.isNotEmpty()) {
                    Spacer(modifier = Modifier.width(4.dp))
                    Text(
                        text = unit,
                        style = MaterialTheme.typography.bodySmall,
                        color = VitalisTextMuted,
                        modifier = Modifier.padding(bottom = 4.dp)
                    )
                }
            }
        }
    }
}

@Composable
private fun MetricDetailCard(
    title: String,
    icon: ImageVector,
    iconColor: Color,
    metricSummary: MetricSummary,
    unit: String
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = MaterialTheme.shapes.medium,
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            // Header
            Row(
                verticalAlignment = Alignment.CenterVertically
            ) {
                Box(
                    modifier = Modifier
                        .size(36.dp)
                        .clip(RoundedCornerShape(8.dp))
                        .background(iconColor.copy(alpha = 0.1f)),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = icon,
                        contentDescription = null,
                        tint = iconColor,
                        modifier = Modifier.size(20.dp)
                    )
                }
                Spacer(modifier = Modifier.width(12.dp))
                Text(
                    text = title,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold,
                    color = MaterialTheme.colorScheme.onSurface
                )
            }

            Spacer(modifier = Modifier.height(16.dp))

            // Stats row
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                StatColumn("Latest", metricSummary.latest, unit)
                StatColumn("Average", metricSummary.avg, unit)
                StatColumn("Min", metricSummary.min, unit)
                StatColumn("Max", metricSummary.max, unit)
            }

            Spacer(modifier = Modifier.height(8.dp))

            // Samples count
            Text(
                text = "${metricSummary.samples} readings in last 7 days",
                style = MaterialTheme.typography.bodySmall,
                color = VitalisTextMuted
            )
        }
    }
}

@Composable
private fun StatColumn(
    label: String,
    value: Double?,
    unit: String
) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            color = VitalisTextMuted
        )
        Spacer(modifier = Modifier.height(4.dp))
        Text(
            text = value?.let {
                if (it >= 100) it.toInt().toString()
                else String.format("%.1f", it)
            } ?: "--",
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.SemiBold,
            color = MaterialTheme.colorScheme.onSurface
        )
        if (unit.isNotEmpty()) {
            Text(
                text = unit,
                style = MaterialTheme.typography.labelSmall,
                color = VitalisTextSecondary
            )
        }
    }
}

// ═══════════════════════════════════════════════════════════════════════════════
// Data helpers
// ═══════════════════════════════════════════════════════════════════════════════

private data class MetricDisplayItem(
    val title: String,
    val icon: ImageVector,
    val color: Color,
    val summary: MetricSummary,
    val unit: String
)

private fun getMetricDisplayItems(summary: Map<String, MetricSummary>): List<MetricDisplayItem> {
    val items = mutableListOf<MetricDisplayItem>()

    summary[VitalsMetricType.HEART_RATE]?.let {
        items.add(MetricDisplayItem("Heart Rate", Icons.Outlined.Favorite, VitalisDanger, it, "bpm"))
    }
    summary[VitalsMetricType.RESTING_HEART_RATE]?.let {
        items.add(MetricDisplayItem("Resting Heart Rate", Icons.Outlined.FavoriteBorder, Color(0xFFE91E63), it, "bpm"))
    }
    summary[VitalsMetricType.STEPS]?.let {
        items.add(MetricDisplayItem("Steps", Icons.AutoMirrored.Outlined.DirectionsRun, VitalisPrimary, it, "steps"))
    }
    summary[VitalsMetricType.SLEEP_MINUTES]?.let {
        items.add(MetricDisplayItem("Sleep Duration", Icons.Outlined.Bed, Color(0xFF6366F1), it, "min"))
    }
    summary[VitalsMetricType.DEEP_SLEEP_MINUTES]?.let {
        items.add(MetricDisplayItem("Deep Sleep", Icons.Outlined.Bed, Color(0xFF4F46E5), it, "min"))
    }
    summary[VitalsMetricType.SPO2]?.let {
        items.add(MetricDisplayItem("Blood Oxygen (SpO2)", Icons.Outlined.Speed, VitalisSuccess, it, "%"))
    }
    summary[VitalsMetricType.HRV_MS]?.let {
        items.add(MetricDisplayItem("Heart Rate Variability", Icons.Outlined.Timeline, VitalisWarning, it, "ms"))
    }
    summary[VitalsMetricType.CALORIES_BURNED]?.let {
        items.add(MetricDisplayItem("Calories Burned", Icons.Outlined.LocalFireDepartment, Color(0xFFFF5722), it, "kcal"))
    }
    summary[VitalsMetricType.ACTIVE_MINUTES]?.let {
        items.add(MetricDisplayItem("Active Minutes", Icons.AutoMirrored.Outlined.DirectionsRun, VitalisPrimary, it, "min"))
    }

    return items
}
