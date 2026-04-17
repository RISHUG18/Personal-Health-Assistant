package com.vitalis.health.ui.components

import android.content.Intent
import android.graphics.Paint
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInVertically
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.gestures.detectTapGestures
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
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
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
import java.time.LocalDate
import java.time.format.DateTimeFormatter
import java.util.Locale
import java.util.concurrent.TimeUnit
import kotlin.math.roundToInt

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
    val lastSyncedAtMillis by viewModel.lastSyncedAtMillis.collectAsState()

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
                if (currentPermState is VitalsViewModel.PermissionState.PermanentlyDenied) {
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
                            lastSyncedAtMillis = lastSyncedAtMillis,
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
    lastSyncedAtMillis: Long?,
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
                lastSyncedTime = formatLastSyncedLabel(lastSyncedAtMillis, syncState),
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
    lastSyncedTime: String,
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
                    Spacer(modifier = Modifier.height(2.dp))
                    Text(
                        text = "Last synced: $lastSyncedTime",
                        style = MaterialTheme.typography.labelSmall,
                        color = colors.textMuted,
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
                trendPoints = buildSparklinePoints(stepsMetric),
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
                trendPoints = buildSparklinePoints(sleepMetric),
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
                trendPoints = buildSparklinePoints(heartMetric),
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
                trendPoints = buildSparklinePoints(spO2Metric),
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
    trendPoints: List<Double> = emptyList(),
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
                if (trendPoints.size >= 2) {
                    val minValue = trendPoints.minOrNull() ?: 0.0
                    val maxValue = trendPoints.maxOrNull() ?: minValue
                    val valueRange = (maxValue - minValue).takeIf { it > 0.0001 } ?: 1.0
                    val xStep = size.width / trendPoints.lastIndex.coerceAtLeast(1)

                    val chartPoints = trendPoints.mapIndexed { index, pointValue ->
                        val normalized = ((pointValue - minValue) / valueRange).toFloat()
                        Offset(
                            x = index * xStep,
                            y = (size.height - (normalized * size.height)).coerceIn(0f, size.height),
                        )
                    }

                    val sparklinePath = Path().apply {
                        moveTo(chartPoints.first().x, chartPoints.first().y)
                        for (index in 1 until chartPoints.size) {
                            val previous = chartPoints[index - 1]
                            val current = chartPoints[index]
                            val controlX = (previous.x + current.x) / 2f
                            cubicTo(
                                controlX,
                                previous.y,
                                controlX,
                                current.y,
                                current.x,
                                current.y,
                            )
                        }
                    }

                    drawPath(
                        path = sparklinePath,
                        color = iconColor.copy(alpha = 0.75f),
                        style = Stroke(width = 2.dp.toPx(), cap = StrokeCap.Round),
                    )
                }
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
    val sevenDayTrend = remember(metricSummary) { buildSevenDayTrendPoints(metricSummary) }
    // FIX E: Derive label count from the actual trend point count so label and
    // data arrays are always aligned. If the backend sends 8 points (UTC day-
    // boundary artefact) the chart labels them properly rather than falling back
    // to the "Day N" placeholder on line 1617.
    val dayLabels = remember(sevenDayTrend.size) { buildDayLabels(sevenDayTrend.size) }
    var showTrend by rememberSaveable(title) { mutableStateOf(false) }

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

                Spacer(modifier = Modifier.height(14.dp))

                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(10.dp))
                        .background(iconBgColor.copy(alpha = 0.45f))
                        .clickable { showTrend = !showTrend }
                        .padding(horizontal = 12.dp, vertical = 10.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(
                            imageVector = Icons.Outlined.Timeline,
                            contentDescription = null,
                            tint = iconColor,
                            modifier = Modifier.size(16.dp)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = if (showTrend) "Hide 7-Day Trend" else "View 7-Day Trend",
                            style = MaterialTheme.typography.labelLarge,
                            color = MaterialTheme.colorScheme.onSurface,
                            fontWeight = FontWeight.SemiBold
                        )
                    }

                    Text(
                        text = if (showTrend) "Hide" else "View",
                        style = MaterialTheme.typography.labelMedium,
                        color = iconColor,
                        fontWeight = FontWeight.SemiBold
                    )
                }

                AnimatedVisibility(
                    visible = showTrend,
                    enter = fadeIn() + slideInVertically { it / 4 },
                    exit = fadeOut()
                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(top = 12.dp)
                    ) {
                        DetailedTrendChart(
                            trendPoints = sevenDayTrend,
                            dayLabels = dayLabels,
                            unit = unit,
                            accentColor = iconColor,
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun DetailedTrendChart(
    trendPoints: List<Double>,
    dayLabels: List<String>,
    unit: String,
    accentColor: Color,
) {
    val colors = LocalVitalisColors.current
    val density = LocalDensity.current
    val chartHorizontalPaddingPx = with(density) { 8.dp.toPx() }
    val dashPathEffect = remember {
        PathEffect.dashPathEffect(floatArrayOf(10f, 8f), 0f)
    }
    val tooltipBackgroundColor = MaterialTheme.colorScheme.surface
    val tooltipTextColor = MaterialTheme.colorScheme.onSurface
    val tooltipStrokeColor = accentColor.copy(alpha = 0.28f)
    var selectedIndex by remember(trendPoints) { mutableStateOf<Int?>(null) }

    val minValue = trendPoints.minOrNull() ?: 0.0
    val maxValue = trendPoints.maxOrNull() ?: minValue
    val latestValue = trendPoints.lastOrNull() ?: 0.0
    val visibleDayLabels = remember(dayLabels, trendPoints.size) {
        dayLabels.takeLast(dayLabels.size.coerceAtMost(trendPoints.size))
    }

    Surface(
        shape = RoundedCornerShape(12.dp),
        color = accentColor.copy(alpha = 0.06f),
        tonalElevation = 0.dp
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Trend Overview",
                    style = MaterialTheme.typography.labelLarge,
                    color = VitalisTextPrimary,
                    fontWeight = FontWeight.SemiBold
                )

                Text(
                    text = "Latest ${formatMetricValue(latestValue)}${if (unit.isNotEmpty()) " $unit" else ""}",
                    style = MaterialTheme.typography.labelMedium,
                    color = accentColor,
                    fontWeight = FontWeight.SemiBold
                )
            }

            Canvas(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(160.dp)
                    .pointerInput(trendPoints, chartHorizontalPaddingPx) {
                        detectTapGestures { tapOffset ->
                            selectedIndex = mapTrendSelectionIndex(
                                tapX = tapOffset.x,
                                canvasWidth = size.width.toFloat(),
                                pointCount = trendPoints.size,
                                horizontalPaddingPx = chartHorizontalPaddingPx,
                            )
                        }
                    }
                    .pointerInput(trendPoints, chartHorizontalPaddingPx) {
                        detectDragGestures(
                            onDragStart = { startOffset ->
                                selectedIndex = mapTrendSelectionIndex(
                                    tapX = startOffset.x,
                                    canvasWidth = size.width.toFloat(),
                                    pointCount = trendPoints.size,
                                    horizontalPaddingPx = chartHorizontalPaddingPx,
                                )
                            },
                            onDrag = { change, _ ->
                                selectedIndex = mapTrendSelectionIndex(
                                    tapX = change.position.x,
                                    canvasWidth = size.width.toFloat(),
                                    pointCount = trendPoints.size,
                                    horizontalPaddingPx = chartHorizontalPaddingPx,
                                )
                            },
                        )
                    }
            ) {
                if (trendPoints.size < 2) {
                    return@Canvas
                }

                val left = 8.dp.toPx()
                val right = size.width - 8.dp.toPx()
                val top = 8.dp.toPx()
                val bottom = size.height - 8.dp.toPx()

                val gridRows = 4
                for (row in 0 until gridRows) {
                    val y = top + ((bottom - top) * row / (gridRows - 1).toFloat())
                    drawLine(
                        color = accentColor.copy(alpha = 0.14f),
                        start = Offset(left, y),
                        end = Offset(right, y),
                        strokeWidth = 1.dp.toPx(),
                    )
                }

                val valueRange = (maxValue - minValue).takeIf { it > 0.0001 } ?: 1.0
                val xStep = (right - left) / trendPoints.lastIndex.coerceAtLeast(1)

                val chartPoints = trendPoints.mapIndexed { index, value ->
                    val normalized = ((value - minValue) / valueRange).toFloat()
                    Offset(
                        x = left + index * xStep,
                        y = bottom - ((bottom - top) * normalized),
                    )
                }

                val linePath = Path().apply {
                    moveTo(chartPoints.first().x, chartPoints.first().y)
                    for (index in 1 until chartPoints.size) {
                        val previous = chartPoints[index - 1]
                        val current = chartPoints[index]
                        val controlX = (previous.x + current.x) / 2f
                        cubicTo(
                            controlX,
                            previous.y,
                            controlX,
                            current.y,
                            current.x,
                            current.y,
                        )
                    }
                }

                val areaPath = Path().apply {
                    addPath(linePath)
                    lineTo(chartPoints.last().x, bottom)
                    lineTo(chartPoints.first().x, bottom)
                    close()
                }

                drawPath(
                    path = areaPath,
                    brush = Brush.verticalGradient(
                        colors = listOf(
                            accentColor.copy(alpha = 0.30f),
                            accentColor.copy(alpha = 0.02f),
                        ),
                        startY = top,
                        endY = bottom,
                    ),
                )

                drawPath(
                    path = linePath,
                    color = accentColor,
                    style = Stroke(width = 2.5.dp.toPx(), cap = StrokeCap.Round),
                )

                chartPoints.forEachIndexed { index, point ->
                    val pointRadius = if (index == chartPoints.lastIndex) 4.2.dp.toPx() else 3.dp.toPx()
                    drawCircle(
                        color = Color.White,
                        radius = pointRadius + 1.8.dp.toPx(),
                        center = point,
                    )
                    drawCircle(
                        color = accentColor,
                        radius = pointRadius,
                        center = point,
                    )
                }

                val activeIndex = selectedIndex?.coerceIn(0, chartPoints.lastIndex)
                if (activeIndex != null) {
                    val activePoint = chartPoints[activeIndex]

                    drawLine(
                        color = colors.textMuted.copy(alpha = 0.65f),
                        start = Offset(activePoint.x, top),
                        end = Offset(activePoint.x, bottom),
                        strokeWidth = 1.2.dp.toPx(),
                        pathEffect = dashPathEffect,
                    )

                    drawCircle(
                        color = Color.White,
                        radius = 6.5.dp.toPx(),
                        center = activePoint,
                    )
                    drawCircle(
                        color = accentColor,
                        radius = 4.6.dp.toPx(),
                        center = activePoint,
                    )

                    val selectedDayLabel = visibleDayLabels.getOrNull(activeIndex) ?: "Day ${activeIndex + 1}"
                    val selectedValueText =
                        "${selectedDayLabel.uppercase(Locale.US)}  ${formatMetricValue(trendPoints[activeIndex])}${if (unit.isNotEmpty()) " $unit" else ""}"

                    val textPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                        color = tooltipTextColor.toArgb()
                        textSize = 11.sp.toPx()
                        typeface = android.graphics.Typeface.create(
                            android.graphics.Typeface.DEFAULT,
                            android.graphics.Typeface.BOLD,
                        )
                    }
                    val textWidth = textPaint.measureText(selectedValueText)
                    val fontMetrics = textPaint.fontMetrics
                    val textHeight = fontMetrics.descent - fontMetrics.ascent

                    val tooltipHorizontalPadding = 10.dp.toPx()
                    val tooltipVerticalPadding = 6.dp.toPx()
                    val tooltipWidth = textWidth + (tooltipHorizontalPadding * 2f)
                    val tooltipHeight = textHeight + (tooltipVerticalPadding * 2f)

                    val minTooltipLeft = left
                    val maxTooltipLeft = (right - tooltipWidth).coerceAtLeast(minTooltipLeft)
                    val tooltipLeft =
                        (activePoint.x - (tooltipWidth / 2f)).coerceIn(minTooltipLeft, maxTooltipLeft)
                    val tooltipTop = (top + 2.dp.toPx()).coerceAtLeast(0f)

                    drawRoundRect(
                        color = tooltipBackgroundColor,
                        topLeft = Offset(tooltipLeft, tooltipTop),
                        size = Size(tooltipWidth, tooltipHeight),
                        cornerRadius = CornerRadius(10.dp.toPx(), 10.dp.toPx()),
                    )
                    drawRoundRect(
                        color = tooltipStrokeColor,
                        topLeft = Offset(tooltipLeft, tooltipTop),
                        size = Size(tooltipWidth, tooltipHeight),
                        cornerRadius = CornerRadius(10.dp.toPx(), 10.dp.toPx()),
                        style = Stroke(width = 1.dp.toPx()),
                    )

                    val textBaseline = tooltipTop + tooltipVerticalPadding - fontMetrics.ascent
                    drawContext.canvas.nativeCanvas.drawText(
                        selectedValueText,
                        tooltipLeft + tooltipHorizontalPadding,
                        textBaseline,
                        textPaint,
                    )
                }
            }

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                visibleDayLabels.forEachIndexed { index, label ->
                    val isSelected = selectedIndex == index
                    Text(
                        text = label.uppercase(Locale.US),
                        style = MaterialTheme.typography.labelSmall,
                        color = if (isSelected) accentColor else VitalisTextMuted,
                        fontWeight = if (isSelected) FontWeight.SemiBold else FontWeight.Medium,
                        fontSize = 10.sp,
                    )
                }
            }

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                Text(
                    text = "Low ${formatMetricValue(minValue)}${if (unit.isNotEmpty()) " $unit" else ""}",
                    style = MaterialTheme.typography.labelSmall,
                    color = VitalisTextMuted,
                )
                Text(
                    text = "High ${formatMetricValue(maxValue)}${if (unit.isNotEmpty()) " $unit" else ""}",
                    style = MaterialTheme.typography.labelSmall,
                    color = VitalisTextMuted,
                )
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

    // ── Heart Rate ────────────────────────────────────────────────────────────
    // The app now sends three metric types per day: heart_rate (avg), heart_rate_min,
    // heart_rate_max. We synthesise a single MetricSummary for the card that uses
    // the avg-of-avgs for avg/latest, and the true min/max from the dedicated types.
    val hrSummary = summary[VitalsMetricType.HEART_RATE]
    if (hrSummary != null) {
        val trueMin   = summary[VitalsMetricType.HEART_RATE_MIN]?.min  ?: hrSummary.min
        val trueMax   = summary[VitalsMetricType.HEART_RATE_MAX]?.max  ?: hrSummary.max
        val displayHr = hrSummary.copy(min = trueMin, max = trueMax)
        items.add(MetricDisplayItem("Heart Rate", Icons.Outlined.Favorite, VitalisMetricHeart, VitalisMetricHeartBg, displayHr, "bpm"))
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
    // Calories: now sourced from TotalCaloriesBurnedRecord (active + BMR),
    // matching Google Fit's "Calories" display.
    summary[VitalsMetricType.CALORIES_BURNED]?.let {
        items.add(MetricDisplayItem("Total Calories", Icons.Outlined.LocalFireDepartment, Color(0xFFFF5722), Color(0xFFFBE9E7), it, "kcal"))
    }

    return items
}

private fun buildSevenDayTrendPoints(metricSummary: MetricSummary): List<Double> {
    val backendTrendPoints = metricSummary.trendPoints.orEmpty().filter { it.isFinite() }
    if (backendTrendPoints.isNotEmpty()) {
        return backendTrendPoints
    }

    return List(7) { 0.0 }
}

/**
 * Build a list of [count] day-of-week abbreviations ending with today.
 *
 * FIX E: Replaces the old `buildSevenDayLabels()` which was hardcoded to 7
 * entries. When the backend returns a different number of trend_points (e.g. 8
 * due to a UTC midnight boundary overlap) the label list must match exactly,
 * otherwise the tooltip falls back to "Day N+1" for the last point.
 */
private fun buildDayLabels(count: Int): List<String> {
    if (count <= 0) return emptyList()
    val formatter = DateTimeFormatter.ofPattern("EEE", Locale.US)
    val today = LocalDate.now()
    return (count - 1 downTo 0).map { dayOffset ->
        today.minusDays(dayOffset.toLong()).format(formatter)
    }
}

private fun formatMetricValue(value: Double): String {
    return if (value >= 100) {
        value.toInt().toString()
    } else {
        String.format(Locale.US, "%.1f", value)
    }
}

private fun mapTrendSelectionIndex(
    tapX: Float,
    canvasWidth: Float,
    pointCount: Int,
    horizontalPaddingPx: Float,
): Int? {
    if (pointCount <= 0 || canvasWidth <= 0f) {
        return null
    }
    if (pointCount == 1) {
        return 0
    }

    val left = horizontalPaddingPx
    val right = (canvasWidth - horizontalPaddingPx).coerceAtLeast(left)
    val xStep = (right - left) / (pointCount - 1)

    if (xStep <= 0f) {
        return 0
    }

    val clampedX = tapX.coerceIn(left, right)
    return ((clampedX - left) / xStep).roundToInt().coerceIn(0, pointCount - 1)
}

private fun buildSparklinePoints(metricSummary: MetricSummary?): List<Double> {
    if (metricSummary == null) return emptyList()

    val backendTrendPoints = metricSummary.trendPoints.orEmpty().filter { it.isFinite() }
    if (backendTrendPoints.size >= 2) {
        return backendTrendPoints
    }

    // Fallback until backend trend_points is wired: derive a simple line from aggregate stats.
    return listOfNotNull(
        metricSummary.min,
        metricSummary.avg,
        metricSummary.latest,
        metricSummary.max,
    )
}

private fun formatLastSyncedLabel(
    lastSyncedAtMillis: Long?,
    syncState: VitalsViewModel.SyncState,
): String {
    if (syncState is VitalsViewModel.SyncState.Reading ||
        syncState is VitalsViewModel.SyncState.Uploading
    ) {
        return "sync in progress"
    }

    val lastSynced = lastSyncedAtMillis ?: return "not synced yet"
    val elapsedMillis = (System.currentTimeMillis() - lastSynced).coerceAtLeast(0L)
    val elapsedMinutes = TimeUnit.MILLISECONDS.toMinutes(elapsedMillis)

    return when {
        elapsedMinutes < 1 -> "just now"
        elapsedMinutes < 60 -> "$elapsedMinutes min${if (elapsedMinutes == 1L) "" else "s"} ago"
        elapsedMinutes < 1440 -> {
            val hours = elapsedMinutes / 60
            "$hours hr${if (hours == 1L) "" else "s"} ago"
        }
        else -> {
            val days = elapsedMinutes / 1440
            "$days day${if (days == 1L) "" else "s"} ago"
        }
    }
}
