package com.vitalis.health.ui.components

import android.content.Intent
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInVertically
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
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
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
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
import com.vitalis.health.ui.theme.MetricValueTextStyle
import com.vitalis.health.ui.theme.LocalVitalisColors
import com.vitalis.health.ui.theme.SectionHeaderStyle
import com.vitalis.health.ui.theme.VitalisBgApp
import com.vitalis.health.ui.theme.VitalisBorderLight
import com.vitalis.health.ui.theme.VitalisDanger
import com.vitalis.health.ui.theme.VitalisDangerBg
import com.vitalis.health.ui.theme.VitalisMetricHeart
import com.vitalis.health.ui.theme.VitalisMetricHeartBg
import com.vitalis.health.ui.theme.VitalisMetricSleep
import com.vitalis.health.ui.theme.VitalisMetricSleepBg
import com.vitalis.health.ui.theme.VitalisPrimary
import com.vitalis.health.ui.theme.VitalisPrimaryDeeper
import com.vitalis.health.ui.theme.VitalisPrimaryLight
import com.vitalis.health.ui.theme.VitalisSuccess
import com.vitalis.health.ui.theme.VitalisSuccessBg
import com.vitalis.health.ui.theme.VitalisTextMuted
import com.vitalis.health.ui.theme.VitalisTextPrimary
import com.vitalis.health.ui.theme.VitalisTextSecondary
import com.vitalis.health.ui.theme.VitalisWarning
import com.vitalis.health.ui.theme.VitalisWarningBg

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
    val colors = LocalVitalisColors.current
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
            .background(colors.bgApp)
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
// Sub-screens — Onboarding style matching HTML .onboarding-screen
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
        modifier = Modifier
            .fillMaxSize()
            .background(VitalisBgApp),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(16.dp),
            modifier = Modifier.padding(32.dp)
        ) {
            // Icon box matching .onboarding-screen icon
            Box(
                modifier = Modifier
                    .size(88.dp)
                    .clip(RoundedCornerShape(22.dp))
                    .background(VitalisPrimaryLight),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Outlined.HealthAndSafety,
                    contentDescription = null,
                    tint = VitalisPrimary,
                    modifier = Modifier.size(44.dp)
                )
            }

            Spacer(modifier = Modifier.height(4.dp))

            Text(
                text = "Health Connect Required",
                style = MaterialTheme.typography.headlineSmall,
                fontWeight = FontWeight.Bold,
                color = VitalisTextPrimary,
                textAlign = TextAlign.Center
            )

            Text(
                text = "To sync your wearable data, please install Health Connect from the Play Store.",
                style = MaterialTheme.typography.bodyMedium,
                color = VitalisTextSecondary,
                textAlign = TextAlign.Center
            )

            Spacer(modifier = Modifier.height(8.dp))

            // btn-primary style
            Button(
                onClick = onInstallClick,
                colors = ButtonDefaults.buttonColors(
                    containerColor = VitalisPrimary,
                    contentColor = Color.White
                ),
                shape = RoundedCornerShape(6.dp),
                modifier = Modifier
                    .fillMaxWidth()
                    .height(48.dp)
            ) {
                Icon(
                    imageVector = Icons.Outlined.PlayArrow,
                    contentDescription = null,
                    modifier = Modifier.size(20.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    "Install Health Connect",
                    fontWeight = FontWeight.SemiBold
                )
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
        modifier = Modifier
            .fillMaxSize()
            .background(VitalisBgApp),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(16.dp),
            modifier = Modifier.padding(32.dp)
        ) {
            Box(
                modifier = Modifier
                    .size(88.dp)
                    .clip(RoundedCornerShape(22.dp))
                    .background(VitalisWarningBg),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Outlined.Refresh,
                    contentDescription = null,
                    tint = VitalisWarning,
                    modifier = Modifier.size(44.dp)
                )
            }

            Spacer(modifier = Modifier.height(4.dp))

            Text(
                text = "Health Connect Update Required",
                style = MaterialTheme.typography.headlineSmall,
                fontWeight = FontWeight.Bold,
                color = VitalisTextPrimary,
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
                colors = ButtonDefaults.buttonColors(
                    containerColor = VitalisWarning,
                    contentColor = Color.White
                ),
                shape = RoundedCornerShape(6.dp),
                modifier = Modifier
                    .fillMaxWidth()
                    .height(48.dp)
            ) {
                Icon(
                    imageVector = Icons.Outlined.Refresh,
                    contentDescription = null,
                    modifier = Modifier.size(20.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    "Update Health Connect",
                    fontWeight = FontWeight.SemiBold
                )
            }
        }
    }
}

@Composable
private fun PermissionRequestScreen(
    onRequestPermissions: () -> Unit
) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(VitalisBgApp),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(16.dp),
            modifier = Modifier.padding(32.dp)
        ) {
            Box(
                modifier = Modifier
                    .size(88.dp)
                    .clip(RoundedCornerShape(22.dp))
                    .background(VitalisPrimaryLight),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Outlined.MonitorHeart,
                    contentDescription = null,
                    tint = VitalisPrimary,
                    modifier = Modifier.size(44.dp)
                )
            }

            Spacer(modifier = Modifier.height(4.dp))

            Text(
                text = "Connect Your Health Data",
                style = MaterialTheme.typography.headlineSmall,
                fontWeight = FontWeight.Bold,
                color = VitalisTextPrimary,
                textAlign = TextAlign.Center
            )

            Text(
                text = "Grant access to Health Connect to sync your vitals including heart rate, steps, sleep, and more.",
                style = MaterialTheme.typography.bodyMedium,
                color = VitalisTextSecondary,
                textAlign = TextAlign.Center
            )

            // Permission list
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(14.dp),
                colors = CardDefaults.cardColors(containerColor = Color.White),
                elevation = CardDefaults.cardElevation(defaultElevation = 0.dp)
            ) {
                Column(
                    verticalArrangement = Arrangement.spacedBy(0.dp),
                    modifier = Modifier.padding(vertical = 4.dp)
                ) {
                    PermissionItem("Heart Rate & HRV")
                    PermissionItem("Steps & Activity")
                    PermissionItem("Sleep Data")
                    PermissionItem("Blood Oxygen (SpO2)")
                    PermissionItem("Calories Burned")
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            // btn-primary
            Button(
                onClick = onRequestPermissions,
                colors = ButtonDefaults.buttonColors(
                    containerColor = VitalisPrimary,
                    contentColor = Color.White
                ),
                shape = RoundedCornerShape(6.dp),
                modifier = Modifier
                    .fillMaxWidth()
                    .height(48.dp)
            ) {
                Text(
                    "Grant Permissions",
                    fontWeight = FontWeight.SemiBold
                )
            }
        }
    }
}

@Composable
private fun PermissionItem(text: String) {
    Row(
        verticalAlignment = Alignment.CenterVertically,
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 10.dp)
    ) {
        Box(
            modifier = Modifier
                .size(28.dp)
                .clip(RoundedCornerShape(7.dp))
                .background(VitalisSuccessBg),
            contentAlignment = Alignment.Center
        ) {
            Icon(
                imageVector = Icons.Filled.CheckCircle,
                contentDescription = null,
                tint = VitalisSuccess,
                modifier = Modifier.size(16.dp)
            )
        }
        Spacer(modifier = Modifier.width(12.dp))
        Text(
            text = text,
            style = MaterialTheme.typography.bodyMedium,
            color = VitalisTextPrimary
        )
    }
}

@Composable
private fun PermissionDeniedScreen(
    onOpenSettings: () -> Unit,
    onRetryPermissions: () -> Unit
) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(VitalisBgApp),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(16.dp),
            modifier = Modifier.padding(32.dp)
        ) {
            Box(
                modifier = Modifier
                    .size(88.dp)
                    .clip(RoundedCornerShape(22.dp))
                    .background(VitalisWarningBg),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Outlined.Warning,
                    contentDescription = null,
                    tint = VitalisWarning,
                    modifier = Modifier.size(44.dp)
                )
            }

            Spacer(modifier = Modifier.height(4.dp))

            Text(
                text = "Permissions Required",
                style = MaterialTheme.typography.headlineSmall,
                fontWeight = FontWeight.Bold,
                color = VitalisTextPrimary,
                textAlign = TextAlign.Center
            )

            Text(
                text = "Health Connect permissions were denied. To sync your wearable data, please grant permissions in Health Connect settings.",
                style = MaterialTheme.typography.bodyMedium,
                color = VitalisTextSecondary,
                textAlign = TextAlign.Center
            )

            Spacer(modifier = Modifier.height(8.dp))

            // btn-primary
            Button(
                onClick = onOpenSettings,
                colors = ButtonDefaults.buttonColors(
                    containerColor = VitalisPrimary,
                    contentColor = Color.White
                ),
                shape = RoundedCornerShape(6.dp),
                modifier = Modifier
                    .fillMaxWidth()
                    .height(48.dp)
            ) {
                Icon(
                    imageVector = Icons.Outlined.HealthAndSafety,
                    contentDescription = null,
                    modifier = Modifier.size(20.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    "Open Health Connect Settings",
                    fontWeight = FontWeight.SemiBold
                )
            }

            // btn-outline
            OutlinedButton(
                onClick = onRetryPermissions,
                shape = RoundedCornerShape(6.dp),
                modifier = Modifier
                    .fillMaxWidth()
                    .height(48.dp),
                colors = ButtonDefaults.outlinedButtonColors(
                    contentColor = VitalisPrimary
                )
            ) {
                Icon(
                    imageVector = Icons.Outlined.Refresh,
                    contentDescription = null,
                    modifier = Modifier.size(20.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    "Check Permissions Again",
                    fontWeight = FontWeight.SemiBold
                )
            }
        }
    }
}

// ═══════════════════════════════════════════════════════════════════════════════
// Main Dashboard Content — matches .main-screen layout from HTML
// ═══════════════════════════════════════════════════════════════════════════════

@Composable
private fun VitalsDashboardContent(
    summaryState: VitalsViewModel.SummaryState,
    syncState: VitalsViewModel.SyncState,
    onSyncClick: () -> Unit,
    onRefreshClick: () -> Unit,
    onSyncDismiss: () -> Unit
) {
    val colors = LocalVitalisColors.current

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .background(colors.bgApp),
        verticalArrangement = Arrangement.spacedBy(0.dp)
    ) {
        // ── Top Bar matching .top-bar ──
        item {
            TopBarSection(
                syncState = syncState,
                onSyncClick = onSyncClick
            )
        }

        // Sync status banner
        item {
            AnimatedVisibility(
                visible = syncState !is VitalsViewModel.SyncState.Idle,
                enter = fadeIn() + slideInVertically(),
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
                        CircularProgressIndicator(
                            color = VitalisPrimary,
                            strokeWidth = 3.dp
                        )
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
                item {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 24.dp, vertical = 20.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        Text(
                            text = "KEY METRICS",
                            style = SectionHeaderStyle,
                            color = colors.textMuted,
                        )

                        KeyMetricsRow(summary = summaryState.summary.summary)
                    }
                }

                item {
                    Text(
                        text = "DETAILED BREAKDOWN",
                        style = SectionHeaderStyle,
                        color = colors.textMuted,
                        modifier = Modifier.padding(
                            start = 24.dp,
                            end = 24.dp,
                            top = 4.dp,
                            bottom = 8.dp
                        )
                    )
                }

                // Detailed metrics cards
                items(getMetricDisplayItems(summaryState.summary.summary)) { item ->
                    MetricDetailCard(
                        title = item.title,
                        icon = item.icon,
                        iconColor = item.color,
                        iconBgColor = item.bgColor,
                        metricSummary = item.summary,
                        unit = item.unit
                    )
                }
            }
        }

        item {
            Spacer(modifier = Modifier.height(24.dp))
        }
    }
}

// ═══════════════════════════════════════════════════════════════════════════════
// Top Bar — matches .top-bar from HTML
// ═══════════════════════════════════════════════════════════════════════════════

@Composable
private fun TopBarSection(
    syncState: VitalsViewModel.SyncState,
    onSyncClick: () -> Unit
) {
    val colors = LocalVitalisColors.current

    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .shadow(
                elevation = 1.dp,
                shape = RoundedCornerShape(bottomStart = 0.dp, bottomEnd = 0.dp),
                ambientColor = VitalisPrimary.copy(alpha = 0.08f),
                spotColor = VitalisPrimary.copy(alpha = 0.08f)
            ),
        color = MaterialTheme.colorScheme.surface,
        shadowElevation = 0.dp
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 24.dp, vertical = 18.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = "Health Overview",
                        style = MaterialTheme.typography.headlineSmall,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.onSurface
                    )
                    Spacer(modifier = Modifier.height(2.dp))
                    Text(
                        text = "Vitals & personal metrics",
                        style = MaterialTheme.typography.bodySmall,
                        color = colors.textMuted
                    )
                }

                // Sync button - btn-outline style
                SyncButton(
                    syncState = syncState,
                    onClick = onSyncClick
                )
            }
        }
    }
}

// ═══════════════════════════════════════════════════════════════════════════════
// Helper Components — Redesigned to match HTML
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
        shape = RoundedCornerShape(6.dp),
        colors = ButtonDefaults.outlinedButtonColors(
            contentColor = VitalisPrimary
        ),
        modifier = Modifier.height(38.dp)
    ) {
        if (isLoading) {
            CircularProgressIndicator(
                modifier = Modifier.size(16.dp),
                color = VitalisPrimary,
                strokeWidth = 2.dp
            )
        } else {
            Icon(
                imageVector = Icons.Filled.Sync,
                contentDescription = "Sync",
                modifier = Modifier.size(16.dp)
            )
        }
        Spacer(modifier = Modifier.width(6.dp))
        Text(
            text = when (syncState) {
                is VitalsViewModel.SyncState.Reading -> "Reading…"
                is VitalsViewModel.SyncState.Uploading -> "Uploading…"
                else -> "Sync Now"
            },
            style = MaterialTheme.typography.labelMedium,
            fontWeight = FontWeight.SemiBold
        )
    }
}

@Composable
private fun SyncStatusBanner(
    syncState: VitalsViewModel.SyncState,
    onDismiss: () -> Unit
) {
    val (color, bgColor, icon, message) = when (syncState) {
        is VitalsViewModel.SyncState.Reading -> BannerStyle(
            VitalisWarning, VitalisWarningBg,
            Icons.Outlined.Refresh, "Reading from Health Connect…"
        )
        is VitalsViewModel.SyncState.Uploading -> BannerStyle(
            VitalisPrimary, VitalisPrimaryLight,
            Icons.Filled.Sync, "Uploading to server…"
        )
        is VitalsViewModel.SyncState.Success -> BannerStyle(
            VitalisSuccess, VitalisSuccessBg,
            Icons.Filled.CheckCircle,
            "Synced ${syncState.inserted} readings (${syncState.skipped} skipped)"
        )
        is VitalsViewModel.SyncState.Error -> BannerStyle(
            VitalisDanger, VitalisDangerBg,
            Icons.Outlined.Warning, syncState.message
        )
        else -> return
    }

    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 4.dp)
            .drawBehind {
                // Colored left border
                drawRect(
                    color = color,
                    topLeft = Offset.Zero,
                    size = androidx.compose.ui.geometry.Size(3.dp.toPx(), size.height)
                )
            },
        shape = RoundedCornerShape(10.dp),
        color = bgColor
    ) {
        Row(
            modifier = Modifier.padding(14.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(30.dp)
                    .clip(RoundedCornerShape(8.dp))
                    .background(color.copy(alpha = 0.15f)),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = icon,
                    contentDescription = null,
                    tint = color,
                    modifier = Modifier.size(16.dp)
                )
            }
            Spacer(modifier = Modifier.width(12.dp))
            Text(
                text = message,
                style = MaterialTheme.typography.bodySmall,
                color = color,
                fontWeight = FontWeight.Medium,
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
                    fontWeight = FontWeight.SemiBold,
                    modifier = Modifier
                        .clip(RoundedCornerShape(4.dp))
                        .background(color.copy(alpha = 0.1f))
                        .clickable { onDismiss() }
                        .padding(horizontal = 10.dp, vertical = 5.dp)
                )
            }
        }
    }
}

private data class BannerStyle(
    val color: Color,
    val bgColor: Color,
    val icon: ImageVector,
    val message: String
)

@Composable
private fun EmptyVitalsCard(onSyncClick: () -> Unit) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp),
        shape = RoundedCornerShape(18.dp),
        colors = CardDefaults.cardColors(containerColor = Color.White),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(28.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Box(
                modifier = Modifier
                    .size(64.dp)
                    .clip(RoundedCornerShape(16.dp))
                    .background(VitalisPrimaryLight),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Outlined.MonitorHeart,
                    contentDescription = null,
                    tint = VitalisPrimary,
                    modifier = Modifier.size(32.dp)
                )
            }
            Spacer(modifier = Modifier.height(16.dp))
            Text(
                text = "No Vitals Data Yet",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.SemiBold,
                color = VitalisTextPrimary
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = "Sync your wearable data to see your health metrics",
                style = MaterialTheme.typography.bodySmall,
                color = VitalisTextSecondary,
                textAlign = TextAlign.Center
            )
            Spacer(modifier = Modifier.height(20.dp))
            Button(
                onClick = onSyncClick,
                colors = ButtonDefaults.buttonColors(
                    containerColor = VitalisPrimary,
                    contentColor = Color.White
                ),
                shape = RoundedCornerShape(6.dp),
                modifier = Modifier.height(42.dp)
            ) {
                Icon(
                    imageVector = Icons.Filled.Sync,
                    contentDescription = null,
                    modifier = Modifier.size(18.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text("Sync Now", fontWeight = FontWeight.SemiBold)
            }
        }
    }
}

// ═══════════════════════════════════════════════════════════════════════════════
// Key Metrics Row — matches .metric-cards-grid from HTML
// ═══════════════════════════════════════════════════════════════════════════════

@Composable
private fun KeyMetricsRow(summary: Map<String, MetricSummary>) {
    val stepsMetric = summary[VitalsMetricType.STEPS]
    val heartMetric = summary[VitalsMetricType.HEART_RATE]
    val sleepMetric = summary[VitalsMetricType.SLEEP_MINUTES]
    val spO2Metric = summary[VitalsMetricType.SPO2]

    Column(
        verticalArrangement = Arrangement.spacedBy(12.dp),
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            KeyMetricCard(
                modifier = Modifier.weight(1f),
                title = "Steps",
                value = stepsMetric?.latest?.toInt()?.toString() ?: "--",
                unit = "",
                icon = Icons.AutoMirrored.Outlined.DirectionsRun,
                iconColor = VitalisPrimary,
                iconBgColor = VitalisPrimaryLight,
                subtitle = "Latest reading",
            )

            KeyMetricCard(
                modifier = Modifier.weight(1f),
                title = "Sleep",
                value = sleepMetric?.latest?.let { String.format("%.1f", it / 60.0) } ?: "--",
                unit = "h",
                icon = Icons.Outlined.Bed,
                iconColor = VitalisMetricSleep,
                iconBgColor = VitalisMetricSleepBg,
                subtitle = "Last night",
            )
        }

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            KeyMetricCard(
                modifier = Modifier.weight(1f),
                title = "Heart Rate",
                value = heartMetric?.avg?.toInt()?.toString() ?: "--",
                unit = "bpm",
                icon = Icons.Outlined.Favorite,
                iconColor = VitalisMetricHeart,
                iconBgColor = VitalisMetricHeartBg,
                subtitle = "Resting",
            )

            KeyMetricCard(
                modifier = Modifier.weight(1f),
                title = "SpO2",
                value = spO2Metric?.latest?.toInt()?.toString() ?: "--",
                unit = "%",
                icon = Icons.Outlined.Speed,
                iconColor = VitalisSuccess,
                iconBgColor = VitalisSuccessBg,
                subtitle = "Latest reading",
            )
        }
    }
}

// ═══════════════════════════════════════════════════════════════════════════════
// Key Metric Card — matches .metric-card from HTML
// ═══════════════════════════════════════════════════════════════════════════════

@Composable
private fun KeyMetricCard(
    modifier: Modifier = Modifier,
    title: String,
    value: String,
    unit: String,
    icon: ImageVector,
    iconColor: Color,
    iconBgColor: Color = iconColor.copy(alpha = 0.1f),
    subtitle: String,
) {
    val colors = LocalVitalisColors.current

    Card(
        modifier = modifier
            .shadow(
                elevation = 1.dp,
                shape = RoundedCornerShape(10.dp),
                ambientColor = VitalisPrimary.copy(alpha = 0.06f),
                spotColor = VitalisPrimary.copy(alpha = 0.06f)
            )
            .border(
                width = 1.dp,
                color = colors.borderLight,
                shape = RoundedCornerShape(10.dp)
            ),
        shape = RoundedCornerShape(10.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp)
    ) {
        Column(
            modifier = Modifier.padding(14.dp)
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically
            ) {
                // Icon box
                Box(
                    modifier = Modifier
                        .size(30.dp)
                        .clip(RoundedCornerShape(8.dp))
                        .background(iconBgColor),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = icon,
                        contentDescription = null,
                        tint = iconColor,
                        modifier = Modifier.size(16.dp)
                    )
                }
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = title,
                    style = MaterialTheme.typography.labelSmall,
                    color = colors.textMuted,
                    fontSize = 12.sp
                )
            }
            Spacer(modifier = Modifier.height(14.dp))
            Row(
                verticalAlignment = Alignment.Bottom
            ) {
                Text(
                    text = value,
                    style = MetricValueTextStyle,
                    color = MaterialTheme.colorScheme.onSurface
                )
                if (unit.isNotEmpty()) {
                    Spacer(modifier = Modifier.width(4.dp))
                    Text(
                        text = unit,
                        style = MaterialTheme.typography.bodySmall,
                        color = colors.textMuted,
                        modifier = Modifier.padding(bottom = 3.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.height(6.dp))
            Text(
                text = subtitle,
                style = MaterialTheme.typography.labelSmall,
                color = colors.textMuted,
                fontWeight = FontWeight.SemiBold
            )

            // Mini sparkline
            Spacer(modifier = Modifier.height(10.dp))
            Canvas(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(24.dp)
            ) {
                val w = size.width
                val h = size.height
                val path = Path().apply {
                    moveTo(0f, h * 0.7f)
                    cubicTo(w * 0.2f, h * 0.5f, w * 0.35f, h * 0.3f, w * 0.5f, h * 0.45f)
                    cubicTo(w * 0.65f, h * 0.6f, w * 0.8f, h * 0.2f, w, h * 0.35f)
                }
                drawPath(
                    path = path,
                    color = iconColor.copy(alpha = 0.6f),
                    style = Stroke(width = 2.dp.toPx(), cap = StrokeCap.Round)
                )
            }
        }
    }
}

// ═══════════════════════════════════════════════════════════════════════════════
// Metric Detail Card — matches .wellness-card expanded from HTML
// ═══════════════════════════════════════════════════════════════════════════════

@Composable
private fun MetricDetailCard(
    title: String,
    icon: ImageVector,
    iconColor: Color,
    iconBgColor: Color = iconColor.copy(alpha = 0.1f),
    metricSummary: MetricSummary,
    unit: String
) {
    val colors = LocalVitalisColors.current

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 24.dp, vertical = 6.dp)
            .shadow(
                elevation = 1.dp,
                shape = RoundedCornerShape(14.dp),
                ambientColor = VitalisPrimary.copy(alpha = 0.06f),
                spotColor = VitalisPrimary.copy(alpha = 0.06f)
            ),
        shape = RoundedCornerShape(14.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp)
    ) {
        Column {
            // Top gradient bar (3dp)
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(3.dp)
                    .background(
                        Brush.horizontalGradient(
                            colors = listOf(iconColor, iconColor.copy(alpha = 0.3f))
                        )
                    )
            )

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
                            .clip(RoundedCornerShape(10.dp))
                            .background(iconBgColor),
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
                    StatColumn("Latest", metricSummary.latest, unit, iconColor)
                    StatColumn("Typical", metricSummary.avg, unit, VitalisTextMuted)
                    StatColumn("Min", metricSummary.min, unit, VitalisTextMuted)
                    StatColumn("Max", metricSummary.max, unit, VitalisTextMuted)
                }

                Spacer(modifier = Modifier.height(12.dp))

                // Samples count
                Surface(
                    shape = RoundedCornerShape(6.dp),
                    color = colors.bgApp,
                    tonalElevation = 0.dp
                ) {
                    Text(
                        text = "${metricSummary.samples} readings in last 7 days",
                        style = MaterialTheme.typography.bodySmall,
                        color = colors.textMuted,
                        modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp)
                    )
                }
            }
        }
    }
}

@Composable
private fun StatColumn(
    label: String,
    value: Double?,
    unit: String,
    accentColor: Color = VitalisTextMuted
) {
    val colors = LocalVitalisColors.current

    Column(
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            color = colors.textMuted,
            fontSize = 11.sp
        )
        Spacer(modifier = Modifier.height(4.dp))
        Text(
            text = value?.let {
                if (it >= 100) it.toInt().toString()
                else String.format("%.1f", it)
            } ?: "--",
            style = MetricTextStyle.copy(
                fontWeight = FontWeight.Bold,
                fontSize = 18.sp,
                letterSpacing = (-0.3).sp
            ),
            color = accentColor
        )
        if (unit.isNotEmpty()) {
            Text(
                text = unit,
                style = MaterialTheme.typography.labelSmall,
                color = colors.textMuted,
                fontSize = 10.sp
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
    val bgColor: Color,
    val summary: MetricSummary,
    val unit: String
)

private fun getMetricDisplayItems(summary: Map<String, MetricSummary>): List<MetricDisplayItem> {
    val items = mutableListOf<MetricDisplayItem>()

    summary[VitalsMetricType.HEART_RATE]?.let {
        items.add(MetricDisplayItem("Heart Rate", Icons.Outlined.Favorite, VitalisMetricHeart, VitalisMetricHeartBg, it, "bpm"))
    }
    summary[VitalsMetricType.RESTING_HEART_RATE]?.let {
        items.add(MetricDisplayItem("Resting Heart Rate", Icons.Outlined.FavoriteBorder, Color(0xFFE91E63), Color(0xFFFCE4EC), it, "bpm"))
    }
    summary[VitalsMetricType.STEPS]?.let {
        items.add(MetricDisplayItem("Steps", Icons.AutoMirrored.Outlined.DirectionsRun, VitalisPrimary, VitalisPrimaryLight, it, "steps"))
    }
    summary[VitalsMetricType.SLEEP_MINUTES]?.let {
        items.add(MetricDisplayItem("Sleep Duration", Icons.Outlined.Bed, VitalisMetricSleep, VitalisMetricSleepBg, it, "min"))
    }
    summary[VitalsMetricType.DEEP_SLEEP_MINUTES]?.let {
        items.add(MetricDisplayItem("Deep Sleep", Icons.Outlined.Bed, Color(0xFF4F46E5), Color(0xFFEEF2FF), it, "min"))
    }
    summary[VitalsMetricType.SPO2]?.let {
        items.add(MetricDisplayItem("Blood Oxygen (SpO2)", Icons.Outlined.Speed, VitalisSuccess, VitalisSuccessBg, it, "%"))
    }
    summary[VitalsMetricType.HRV_MS]?.let {
        items.add(MetricDisplayItem("Heart Rate Variability", Icons.Outlined.Timeline, VitalisWarning, VitalisWarningBg, it, "ms"))
    }
    summary[VitalsMetricType.CALORIES_BURNED]?.let {
        items.add(MetricDisplayItem("Calories Burned", Icons.Outlined.LocalFireDepartment, Color(0xFFFF5722), Color(0xFFFBE9E7), it, "kcal"))
    }
    summary[VitalsMetricType.ACTIVE_MINUTES]?.let {
        items.add(MetricDisplayItem("Active Minutes", Icons.AutoMirrored.Outlined.DirectionsRun, VitalisPrimary, VitalisPrimaryLight, it, "min"))
    }

    return items
}
