package com.vitalis.health.ui.example

import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.CloudUpload
import androidx.compose.material.icons.outlined.Forum
import androidx.compose.material.icons.outlined.Notifications
import androidx.compose.material.icons.outlined.Person
import androidx.compose.material.icons.outlined.SpaceDashboard
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.livedata.observeAsState
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.ViewModelProvider
import com.vitalis.health.VitalisApp
import com.vitalis.health.data.model.Alert
import com.vitalis.health.data.model.AlertEvidence
import com.vitalis.health.data.model.DashboardData
import com.vitalis.health.data.model.ProcessReportResponse
import com.vitalis.health.ui.AlertsViewModel
import com.vitalis.health.ui.AssistantViewModel
import com.vitalis.health.ui.DashboardViewModel
import com.vitalis.health.ui.ReportUploadViewModel
import com.vitalis.health.ui.components.PLACEHOLDER_REPORTS
import com.vitalis.health.ui.components.ReportTimeline
import com.vitalis.health.ui.components.ReportTimelineItem
import com.vitalis.health.ui.components.ReportType
import com.vitalis.health.ui.components.ExtractionMethod
import com.vitalis.health.ui.components.ReportUploadScreen
import com.vitalis.health.ui.components.ReportDetailScreen
import com.vitalis.health.ui.components.ProfileConsentScreen
import com.vitalis.health.ui.components.VitalisEmptyScreen
import com.vitalis.health.ui.components.VitalisErrorScreen
import com.vitalis.health.ui.components.VitalisLoadingScreen
import com.vitalis.health.ui.theme.MetricTextStyle
import com.vitalis.health.ui.theme.VitalisBgApp
import com.vitalis.health.ui.theme.VitalisBorder
import com.vitalis.health.ui.theme.VitalisDanger
import com.vitalis.health.ui.theme.VitalisPrimary
import com.vitalis.health.ui.theme.VitalisPrimaryLight
import com.vitalis.health.ui.theme.VitalisSuccess
import com.vitalis.health.ui.theme.VitalisTextMuted
import com.vitalis.health.ui.theme.VitalisTextPrimary
import com.vitalis.health.ui.theme.VitalisTextSecondary
import com.vitalis.health.ui.theme.VitalisTheme
import com.vitalis.health.ui.theme.VitalisWarning

/**
 * Example Activity demonstrating full integration:
 *   UI → ViewModel → Repository → API Adapter → Backend
 *
 * Shows four tabs: Dashboard, Alerts, AI Chat, Profile
 */
class ExampleActivity : ComponentActivity() {

    private lateinit var dashboardVm: DashboardViewModel
    private lateinit var alertsVm: AlertsViewModel
    private lateinit var assistantVm: AssistantViewModel
    private lateinit var uploadVm: ReportUploadViewModel

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val factory = (application as VitalisApp).viewModelFactory
        dashboardVm = ViewModelProvider(this, factory)[DashboardViewModel::class.java]
        alertsVm = ViewModelProvider(this, factory)[AlertsViewModel::class.java]
        assistantVm = ViewModelProvider(this, factory)[AssistantViewModel::class.java]
        uploadVm = ViewModelProvider(this, factory)[ReportUploadViewModel::class.java]

        // Kick off data loads
        val userId = "00000000-0000-0000-0000-000000000001"
        dashboardVm.loadDashboard(userId)
        alertsVm.loadAlerts(userId)

        setContent {
            VitalisTheme {
                MainScreen(
                    dashboardVm = dashboardVm,
                    alertsVm = alertsVm,
                    assistantVm = assistantVm,
                    uploadVm = uploadVm,
                    userId = userId
                )
            }
        }
    }
}

// ─── Compose UI ──────────────────────────────────────────

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MainScreen(
    dashboardVm: DashboardViewModel,
    alertsVm: AlertsViewModel,
    assistantVm: AssistantViewModel,
    uploadVm: ReportUploadViewModel,
    userId: String
) {
    var selectedTab by remember { mutableIntStateOf(0) }

    // Track uploaded reports to prepend to timeline
    val uploadedReports = remember { mutableStateListOf<ReportTimelineItem>() }

    // Track the last successful result for detail view
    val uploadState by uploadVm.uiState.observeAsState(ReportUploadViewModel.UiState.Idle)
    var showDetailScreen by remember { mutableStateOf(false) }
    var detailResult by remember { mutableStateOf<ProcessReportResponse?>(null) }

    // When upload succeeds, build a timeline item and prepend it
    LaunchedEffect(uploadState) {
        if (uploadState is ReportUploadViewModel.UiState.Success) {
            val result = (uploadState as ReportUploadViewModel.UiState.Success).result
            detailResult = result
            val useGemini = uploadVm.useGemini.value ?: false
            val newItem = ReportTimelineItem(
                reportId = result.reportId,
                reportName = "Report ${result.reportId.take(8)}",
                uploadDate = "Just now",
                reportType = ReportType.LAB,
                riskLabel = "New",
                riskLevel = "normal",
                highlight = result.ocrTextPreview.take(80).ifEmpty { "Report processed" },
                extractionMethod = if (useGemini) ExtractionMethod.AI else ExtractionMethod.STANDARD,
                sourceFilename = result.storagePath.substringAfterLast('/'),
                pageNumber = null,
            )
            // Prepend only if not already present
            if (uploadedReports.none { it.reportId == newItem.reportId }) {
                uploadedReports.add(0, newItem)
            }
        }
    }

    // If detail screen is open, show it instead of tabs
    if (showDetailScreen && detailResult != null) {
        ReportDetailScreen(
            result = detailResult!!,
            onBack = { showDetailScreen = false },
        )
        return
    }

    Scaffold(
        bottomBar = {
            NavigationBar {
                NavigationBarItem(
                    selected = selectedTab == 0,
                    onClick = { selectedTab = 0 },
                    label = { Text("Dashboard") },
                    icon = { Icon(Icons.Outlined.SpaceDashboard, contentDescription = "Dashboard") }
                )
                NavigationBarItem(
                    selected = selectedTab == 1,
                    onClick = { selectedTab = 1 },
                    label = { Text("Upload") },
                    icon = { Icon(Icons.Outlined.CloudUpload, contentDescription = "Upload") }
                )
                NavigationBarItem(
                    selected = selectedTab == 2,
                    onClick = { selectedTab = 2 },
                    label = { Text("Alerts") },
                    icon = { Icon(Icons.Outlined.Notifications, contentDescription = "Alerts") }
                )
                NavigationBarItem(
                    selected = selectedTab == 3,
                    onClick = { selectedTab = 3 },
                    label = { Text("Assistant") },
                    icon = { Icon(Icons.Outlined.Forum, contentDescription = "Assistant") }
                )
                NavigationBarItem(
                    selected = selectedTab == 4,
                    onClick = { selectedTab = 4 },
                    label = { Text("Profile") },
                    icon = { Icon(Icons.Outlined.Person, contentDescription = "Profile") }
                )
            }
        }
    ) { padding ->
        Box(Modifier.padding(padding)) {
            when (selectedTab) {
                0 -> DashboardScreen(dashboardVm, uploadedReports)
                1 -> ReportUploadScreen(
                    viewModel = uploadVm,
                    userId = userId,
                    onViewResult = { showDetailScreen = true },
                )
                2 -> AlertsScreen(alertsVm)
                3 -> AssistantScreen(assistantVm, userId)
                4 -> ProfileConsentScreen()
            }
        }
    }
}

// ─── Dashboard Tab ───────────────────────────────────────

@Composable
fun DashboardScreen(vm: DashboardViewModel, uploadedReports: List<ReportTimelineItem> = emptyList()) {
    val state by vm.dashboardState.observeAsState()

    when (val s = state) {
        is DashboardViewModel.UiState.Loading -> VitalisLoadingScreen(label = "Fetching your health data…")
        is DashboardViewModel.UiState.Error   -> VitalisErrorScreen(
            message = s.message,
            onRetry = { vm.loadDashboard("00000000-0000-0000-0000-000000000001") },
        )
        is DashboardViewModel.UiState.Success -> DashboardContent(s.data, uploadedReports)
        null -> VitalisEmptyScreen(
            message = "No dashboard data yet",
            subtitle = "Pull down to refresh",
        )
    }
}

@Composable
fun DashboardContent(data: DashboardData, uploadedReports: List<ReportTimelineItem> = emptyList()) {
    // Prepend uploaded reports to placeholder data
    val allReports = uploadedReports + PLACEHOLDER_REPORTS
    Column(
        Modifier
            .fillMaxSize()
            .background(VitalisBgApp)
            .verticalScroll(rememberScrollState())
            .padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        // ── Patient Summary ──
        PatientSummaryCard(data)

        // ── Wellbeing Score ──
        WellbeingScoreCard(data)

        // ── Active Alerts ──
        ActiveAlertsSection(data)

        // ── Report Timeline ──
        ReportTimeline(reports = allReports)
    }
}

/* ── Patient Summary ─────────────────────────────────── */

@Composable
private fun PatientSummaryCard(data: DashboardData) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(18.dp),
        colors = CardDefaults.cardColors(containerColor = Color.White),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
    ) {
        Column(Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text(
                data.greeting,
                style = MaterialTheme.typography.headlineSmall,
                color = VitalisTextPrimary,
                fontWeight = FontWeight.Bold,
            )

            Row(horizontalArrangement = Arrangement.spacedBy(24.dp)) {
                InfoChip(label = "Patient ID", value = data.userId)
                data.environment?.let { env ->
                    env.weather?.let { InfoChip(label = "Weather", value = it) }
                }
            }

            data.environment?.let { env ->
                env.aqi?.let { aqi ->
                    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text("AQI", style = MaterialTheme.typography.labelSmall, color = VitalisTextMuted)
                        Surface(
                            shape = RoundedCornerShape(6.dp),
                            color = if (aqi <= 50) VitalisSuccess.copy(alpha = .12f) else VitalisWarning.copy(alpha = .12f),
                        ) {
                            Text(
                                "$aqi",
                                modifier = Modifier.padding(horizontal = 10.dp, vertical = 3.dp),
                                style = MaterialTheme.typography.labelSmall,
                                fontWeight = FontWeight.SemiBold,
                                color = if (aqi <= 50) VitalisSuccess else VitalisWarning,
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun InfoChip(label: String, value: String) {
    Column {
        Text(label, style = MaterialTheme.typography.labelSmall, color = VitalisTextMuted)
        Text(value, style = MaterialTheme.typography.bodyMedium, color = VitalisTextPrimary, fontWeight = FontWeight.Medium)
    }
}

/* ── Wellbeing Score Card ─────────────────────────────── */

@Composable
private fun WellbeingScoreCard(data: DashboardData) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(24.dp),
        colors = CardDefaults.cardColors(containerColor = Color.White),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
    ) {
        Column {
            // gradient-like top accent bar
            Box(
                Modifier
                    .fillMaxWidth()
                    .height(4.dp)
                    .clip(RoundedCornerShape(topStart = 24.dp, topEnd = 24.dp))
                    .background(VitalisPrimary)
            )

            Column(
                Modifier.padding(horizontal = 28.dp, vertical = 24.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                Text(
                    "Wellbeing Score",
                    style = MaterialTheme.typography.titleMedium,
                    color = VitalisTextSecondary,
                )

                Text(
                    "${data.wellbeingScore}",
                    style = MetricTextStyle.copy(fontSize = 42.sp),
                    color = VitalisPrimary,
                )

                // progress bar
                @Suppress("DEPRECATION")
                LinearProgressIndicator(
                    progress = (data.wellbeingScore / 100f).coerceIn(0f, 1f),
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(8.dp)
                        .clip(RoundedCornerShape(4.dp)),
                    color = VitalisPrimary,
                    trackColor = VitalisPrimaryLight.copy(alpha = .25f),
                )

                // trend badge
                val trendColor = when {
                    data.wellbeingTrend.contains("up", ignoreCase = true) -> VitalisSuccess
                    data.wellbeingTrend.contains("down", ignoreCase = true) -> VitalisDanger
                    else -> VitalisTextMuted
                }
                Surface(
                    shape = RoundedCornerShape(6.dp),
                    color = trendColor.copy(alpha = .12f),
                ) {
                    Text(
                        data.wellbeingTrend,
                        modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
                        style = MaterialTheme.typography.labelSmall,
                        fontWeight = FontWeight.SemiBold,
                        color = trendColor,
                    )
                }
            }
        }
    }
}

/* ── Active Alerts Section ────────────────────────────── */

private val PLACEHOLDER_ALERTS = listOf(
    Alert(
        id = "alrt_001",
        title = "Low Hemoglobin",
        severity = "high",
        message = "Hemoglobin below normal range (11.2 g/dL)",
        timestamp = "2025-05-15T10:30:00Z",
        evidence = AlertEvidence(
            metric = "hemoglobin",
            value = "11.2",
            threshold = "12.0-16.0",
            sourceFilename = "bloodwork_may2025.pdf",
            pageNumber = 1,
        ),
    ),
    Alert(
        id = "alrt_002",
        title = "Elevated Blood Pressure",
        severity = "medium",
        message = "Blood pressure trending above 140/90 mmHg",
        timestamp = "2025-05-14T08:15:00Z",
        evidence = AlertEvidence(
            metric = "systolicBP",
            value = "145",
            threshold = "90-120",
        ),
    ),
)

@Composable
private fun ActiveAlertsSection(data: DashboardData) {
    Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Row(
            Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                "Active Alerts",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
                color = VitalisTextPrimary,
            )
            Surface(
                shape = CircleShape,
                color = VitalisDanger.copy(alpha = .12f),
            ) {
                Text(
                    "${data.activeAlertsCount}",
                    modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
                    style = MaterialTheme.typography.labelSmall,
                    fontWeight = FontWeight.Bold,
                    color = VitalisDanger,
                )
            }
        }

        PLACEHOLDER_ALERTS.forEach { alert ->
            AlertDashboardCard(alert)
        }
    }
}

@Composable
private fun AlertDashboardCard(alert: Alert) {
    val borderColor = when (alert.severity) {
        "high" -> VitalisDanger
        "medium" -> VitalisWarning
        else -> VitalisSuccess
    }

    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(14.dp),
        colors = CardDefaults.cardColors(containerColor = Color.White),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
    ) {
        Column(
            Modifier
                .drawBehind {
                    drawRect(
                        color = borderColor,
                        topLeft = Offset.Zero,
                        size = Size(3.dp.toPx(), size.height),
                    )
                }
                .padding(start = 6.dp)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    alert.title,
                    style = MaterialTheme.typography.labelSmall,
                    color = VitalisTextMuted,
                )
                SeverityBadge(alert.severity)
            }
            Text(
                alert.message,
                style = MaterialTheme.typography.bodyMedium,
                color = VitalisTextPrimary,
            )
            alert.evidence?.sourceFilename?.let { filename ->
                Text(
                    "Source: $filename",
                    style = MaterialTheme.typography.labelSmall,
                    color = VitalisTextMuted,
                )
            }
        }
    }
}

// ─── Alerts Tab ──────────────────────────────────────────

@Composable
fun AlertsScreen(vm: AlertsViewModel) {
    val state by vm.alertsState.observeAsState()

    when (val s = state) {
        is AlertsViewModel.UiState.Loading -> VitalisLoadingScreen(label = "Checking for alerts…")
        is AlertsViewModel.UiState.Error   -> VitalisErrorScreen(
            message = s.message,
            onRetry = { vm.loadAlerts("00000000-0000-0000-0000-000000000001") },
        )
        is AlertsViewModel.UiState.Success -> {
            if (s.alerts.isEmpty()) {
                VitalisEmptyScreen(
                    message = "No active alerts",
                    subtitle = "You're all clear — great job keeping up with your health!",
                    icon = Icons.Outlined.Notifications,
                )
            } else {
                AlertsList(s.alerts)
            }
        }
        null -> VitalisEmptyScreen(
            message = "No alerts loaded",
            subtitle = "Pull down to refresh",
        )
    }
}

@Composable
fun AlertsList(alerts: List<Alert>) {
    LazyColumn(
        Modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        items(alerts, key = { it.id }) { alert ->
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp)) {
                    Row(
                        Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text(alert.title, fontWeight = FontWeight.Bold)
                        SeverityBadge(alert.severity)
                    }
                    Spacer(Modifier.height(6.dp))
                    Text(alert.message, style = MaterialTheme.typography.bodyMedium)
                    alert.evidence?.let { ev ->
                        Spacer(Modifier.height(8.dp))
                        Text(
                            "Source: ${ev.source ?: "—"}  •  ${ev.metric ?: ""}: ${ev.value ?: ""}",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun SeverityBadge(severity: String) {
    val color = when (severity) {
        "high"   -> Color(0xFFC0392B)
        "medium" -> Color(0xFFC27817)
        else     -> Color(0xFF1E7D5A)
    }
    Surface(shape = MaterialTheme.shapes.small, color = color.copy(alpha = 0.12f)) {
        Text(
            severity.uppercase(),
            Modifier.padding(horizontal = 8.dp, vertical = 2.dp),
            color = color,
            style = MaterialTheme.typography.labelSmall,
            fontWeight = FontWeight.Bold
        )
    }
}

// ─── AI Assistant Tab ────────────────────────────────────

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AssistantScreen(vm: AssistantViewModel, userId: String) {
    val chatHistory by vm.chatHistory.observeAsState(emptyList())
    val uiState by vm.uiState.observeAsState()
    var queryText by remember { mutableStateOf("") }
    val context = LocalContext.current

    Column(Modifier.fillMaxSize()) {
        // Chat messages
        LazyColumn(
            Modifier
                .weight(1f)
                .fillMaxWidth(),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            items(chatHistory) { msg ->
                Row(
                    Modifier.fillMaxWidth(),
                    horizontalArrangement = if (msg.isUser) Arrangement.End else Arrangement.Start
                ) {
                    Surface(
                        shape = MaterialTheme.shapes.medium,
                        color = if (msg.isUser)
                            MaterialTheme.colorScheme.primary
                        else
                            MaterialTheme.colorScheme.surfaceVariant,
                        tonalElevation = 1.dp
                    ) {
                        Column(Modifier.padding(12.dp)) {
                            Text(
                                msg.text,
                                color = if (msg.isUser)
                                    MaterialTheme.colorScheme.onPrimary
                                else
                                    MaterialTheme.colorScheme.onSurfaceVariant
                            )
                            if (msg.citations.isNotEmpty()) {
                                Spacer(Modifier.height(6.dp))
                                for (c in msg.citations) {
                                    Text(
                                        "[${c.sourceFile} p.${c.page}] ${c.snippet}",
                                        style = MaterialTheme.typography.bodySmall,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f)
                                    )
                                }
                            }
                        }
                    }
                }
            }

            // Loading indicator inline with chat
            if (uiState is AssistantViewModel.UiState.Loading) {
                item {
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.Start) {
                        CircularProgressIndicator(
                            modifier = Modifier
                                .padding(8.dp)
                                .size(24.dp),
                            strokeWidth = 2.dp,
                            color = MaterialTheme.colorScheme.primary,
                        )
                    }
                }
            }

            // Error state inline with chat
            if (uiState is AssistantViewModel.UiState.Error) {
                item {
                    val errMsg = (uiState as AssistantViewModel.UiState.Error).message
                    Surface(
                        modifier = Modifier
                            .fillMaxWidth(0.85f)
                            .padding(vertical = 4.dp),
                        shape = MaterialTheme.shapes.medium,
                        color = MaterialTheme.colorScheme.errorContainer,
                    ) {
                        Text(
                            text = "Error: $errMsg",
                            modifier = Modifier.padding(12.dp),
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onErrorContainer,
                        )
                    }
                }
            }
        }

        // Input bar
        Row(
            Modifier
                .fillMaxWidth()
                .padding(12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            OutlinedTextField(
                value = queryText,
                onValueChange = { queryText = it },
                modifier = Modifier.weight(1f),
                placeholder = { Text("Ask a health question…") },
                singleLine = true
            )
            Spacer(Modifier.width(8.dp))
            Button(
                onClick = {
                    val q = queryText.trim()
                    if (q.isNotEmpty()) {
                        vm.sendQuery(userId, q)
                        queryText = ""
                    } else {
                        Toast.makeText(context, "Type a question first", Toast.LENGTH_SHORT).show()
                    }
                },
                enabled = uiState !is AssistantViewModel.UiState.Loading
            ) {
                Text("Send")
            }
        }
    }
}

// ─── Shared helpers ──────────────────────────────────────
