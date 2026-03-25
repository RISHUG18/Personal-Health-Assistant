package com.vitalis.health.ui.example

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
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
import androidx.compose.material.icons.outlined.LocationOff
import androidx.compose.material.icons.outlined.Notifications
import androidx.compose.material.icons.outlined.Person
import androidx.compose.material.icons.outlined.SpaceDashboard
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.livedata.observeAsState
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.lifecycle.ViewModelProvider
import com.google.android.gms.location.FusedLocationProviderClient
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import com.google.android.gms.tasks.CancellationTokenSource
import com.vitalis.health.VitalisApp
import com.vitalis.health.data.model.Alert
import com.vitalis.health.data.model.DashboardAlert
import com.vitalis.health.data.model.DashboardData
import com.vitalis.health.data.model.ProcessReportResponse
import com.vitalis.health.ui.AlertsViewModel
import com.vitalis.health.ui.AssistantViewModel
import com.vitalis.health.ui.AuthViewModel
import com.vitalis.health.ui.DashboardViewModel
import com.vitalis.health.ui.ReportUploadViewModel
import com.vitalis.health.ui.components.LoginScreen
import com.vitalis.health.ui.components.RegisterScreen
import com.vitalis.health.ui.components.ReportTimeline
import com.vitalis.health.ui.components.ReportTimelineItem
import com.vitalis.health.ui.components.ReportType
import com.vitalis.health.ui.components.ExtractionMethod
import com.vitalis.health.data.model.ReportSummary
import com.vitalis.health.ui.components.ReportUploadScreen
import com.vitalis.health.ui.components.ReportDetailScreen
import com.vitalis.health.ui.components.ProfileConsentScreen
import com.vitalis.health.ui.components.VitalisEmptyScreen
import com.vitalis.health.ui.components.VitalisErrorScreen
import com.vitalis.health.ui.components.VitalisLoadingScreen
import com.vitalis.health.ui.theme.VitalisBgApp
import com.vitalis.health.ui.theme.VitalisDanger
import com.vitalis.health.ui.theme.VitalisPrimary
import com.vitalis.health.ui.theme.VitalisSuccess
import com.vitalis.health.ui.theme.VitalisTextMuted
import com.vitalis.health.ui.theme.VitalisTextPrimary
import com.vitalis.health.ui.theme.VitalisTheme
import com.vitalis.health.ui.theme.VitalisWarning

/**
 * App navigation state for auth vs main flow
 */
enum class AppState {
    LOGIN,
    REGISTER,
    MAIN
}

/**
 * Example Activity demonstrating full integration:
 *   UI → ViewModel → Repository → API Adapter → Backend
 *
 * Shows five tabs: Dashboard, Upload, Alerts, AI Chat, Profile
 * Includes authentication flow with login/register screens.
 */
class ExampleActivity : ComponentActivity() {

    private lateinit var dashboardVm: DashboardViewModel
    private lateinit var alertsVm: AlertsViewModel
    private lateinit var assistantVm: AssistantViewModel
    private lateinit var uploadVm: ReportUploadViewModel
    private lateinit var authVm: AuthViewModel
    private lateinit var fusedLocationClient: FusedLocationProviderClient

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Initialize location client
        fusedLocationClient = LocationServices.getFusedLocationProviderClient(this)

        val factory = (application as VitalisApp).viewModelFactory
        dashboardVm = ViewModelProvider(this, factory)[DashboardViewModel::class.java]
        alertsVm = ViewModelProvider(this, factory)[AlertsViewModel::class.java]
        assistantVm = ViewModelProvider(this, factory)[AssistantViewModel::class.java]
        uploadVm = ViewModelProvider(this, factory)[ReportUploadViewModel::class.java]
        authVm = ViewModelProvider(this, factory)[AuthViewModel::class.java]

        setContent {
            VitalisTheme {
                // Track app navigation state
                var appState by remember {
                    mutableStateOf(
                        if (authVm.isLoggedIn()) AppState.MAIN else AppState.LOGIN
                    )
                }

                when (appState) {
                    AppState.LOGIN -> {
                        LoginScreen(
                            viewModel = authVm,
                            onLoginSuccess = { userId ->
                                // Load alerts for this user
                                alertsVm.loadAlerts(userId)
                                appState = AppState.MAIN
                            },
                            onNavigateToRegister = {
                                appState = AppState.REGISTER
                            }
                        )
                    }
                    AppState.REGISTER -> {
                        RegisterScreen(
                            viewModel = authVm,
                            onRegisterSuccess = { userId ->
                                // Load alerts for this user
                                alertsVm.loadAlerts(userId)
                                appState = AppState.MAIN
                            },
                            onNavigateToLogin = {
                                appState = AppState.LOGIN
                            }
                        )
                    }
                    AppState.MAIN -> {
                        // Get userId dynamically from auth
                        val userId = authVm.getUserId()
                        if (userId == null) {
                            // Token invalid or missing, redirect to login
                            appState = AppState.LOGIN
                        } else {
                            // Load alerts if not already loaded
                            LaunchedEffect(userId) {
                                alertsVm.loadAlerts(userId)
                            }

                            MainScreen(
                                dashboardVm = dashboardVm,
                                alertsVm = alertsVm,
                                assistantVm = assistantVm,
                                uploadVm = uploadVm,
                                userId = userId,
                                fusedLocationClient = fusedLocationClient,
                                onLogoutClick = {
                                    authVm.logout()
                                    appState = AppState.LOGIN
                                }
                            )
                        }
                    }
                }
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
    userId: String,
    fusedLocationClient: FusedLocationProviderClient,
    onLogoutClick: () -> Unit = {}
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
                0 -> DashboardScreen(
                    vm = dashboardVm,
                    userId = userId,
                    fusedLocationClient = fusedLocationClient,
                    uploadedReports = uploadedReports
                )
                1 -> ReportUploadScreen(
                    viewModel = uploadVm,
                    userId = userId,
                    onViewResult = { showDetailScreen = true },
                )
                2 -> AlertsScreen(alertsVm, userId)
                3 -> AssistantScreen(assistantVm, userId)
                4 -> ProfileConsentScreen(onLogoutClick = onLogoutClick)
            }
        }
    }
}

// ─── Dashboard Tab ───────────────────────────────────────

@Composable
fun DashboardScreen(
    vm: DashboardViewModel,
    userId: String,
    fusedLocationClient: FusedLocationProviderClient,
    uploadedReports: List<ReportTimelineItem> = emptyList()
) {
    val context = LocalContext.current
    val state by vm.dashboardState.collectAsState()

    // Location permission launcher
    val locationPermissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        val fineLocationGranted = permissions[Manifest.permission.ACCESS_FINE_LOCATION] == true
        val coarseLocationGranted = permissions[Manifest.permission.ACCESS_COARSE_LOCATION] == true

        if (fineLocationGranted || coarseLocationGranted) {
            // Permission granted, fetch location
            fetchLocation(fusedLocationClient, context) { location ->
                vm.loadDashboard(userId, location)
            }
        } else {
            // Permission denied, load without location
            vm.onLocationPermissionDenied(userId)
            Toast.makeText(
                context,
                "Location permission denied. Weather data unavailable.",
                Toast.LENGTH_LONG
            ).show()
        }
    }

    // Initial load: check permissions and load dashboard
    LaunchedEffect(Unit) {
        val hasLocationPermission = ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.ACCESS_FINE_LOCATION
        ) == PackageManager.PERMISSION_GRANTED || ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.ACCESS_COARSE_LOCATION
        ) == PackageManager.PERMISSION_GRANTED

        if (hasLocationPermission) {
            // Fetch location and load dashboard
            fetchLocation(fusedLocationClient, context) { location ->
                vm.loadDashboard(userId, location)
            }
        } else {
            // Request permission
            locationPermissionLauncher.launch(
                arrayOf(
                    Manifest.permission.ACCESS_FINE_LOCATION,
                    Manifest.permission.ACCESS_COARSE_LOCATION
                )
            )
        }
    }

    when (val s = state) {
        is DashboardViewModel.UiState.Loading -> VitalisLoadingScreen(label = "Fetching your health data…")
        is DashboardViewModel.UiState.Error -> VitalisErrorScreen(
            message = s.message,
            onRetry = { vm.retry() },
        )
        is DashboardViewModel.UiState.Success -> DashboardContent(
            data = s.data,
            locationAvailable = s.locationAvailable,
            uploadedReports = uploadedReports,
            onRequestLocation = {
                locationPermissionLauncher.launch(
                    arrayOf(
                        Manifest.permission.ACCESS_FINE_LOCATION,
                        Manifest.permission.ACCESS_COARSE_LOCATION
                    )
                )
            }
        )
        is DashboardViewModel.UiState.LocationPermissionRequired -> {
            if (s.data != null) {
                DashboardContent(
                    data = s.data,
                    locationAvailable = false,
                    uploadedReports = uploadedReports,
                    onRequestLocation = {
                        locationPermissionLauncher.launch(
                            arrayOf(
                                Manifest.permission.ACCESS_FINE_LOCATION,
                                Manifest.permission.ACCESS_COARSE_LOCATION
                            )
                        )
                    }
                )
            } else {
                VitalisLoadingScreen(label = "Loading…")
            }
        }
    }
}

/**
 * Fetch current location using FusedLocationProviderClient.
 */
private fun fetchLocation(
    fusedLocationClient: FusedLocationProviderClient,
    context: android.content.Context,
    onLocationReceived: (DashboardViewModel.LocationData?) -> Unit
) {
    try {
        val cancellationTokenSource = CancellationTokenSource()
        fusedLocationClient.getCurrentLocation(
            Priority.PRIORITY_BALANCED_POWER_ACCURACY,
            cancellationTokenSource.token
        ).addOnSuccessListener { location ->
            if (location != null) {
                onLocationReceived(
                    DashboardViewModel.LocationData(
                        latitude = location.latitude,
                        longitude = location.longitude,
                        city = null // Geocoding can be added later
                    )
                )
            } else {
                onLocationReceived(null)
            }
        }.addOnFailureListener {
            onLocationReceived(null)
        }
    } catch (e: SecurityException) {
        onLocationReceived(null)
    }
}

@Composable
fun DashboardContent(
    data: DashboardData,
    locationAvailable: Boolean,
    uploadedReports: List<ReportTimelineItem> = emptyList(),
    onRequestLocation: () -> Unit
) {
    // Convert backend ReportSummary to UI ReportTimelineItem
    val backendReports = data.reports.map { report -> report.toTimelineItem() }
    // Prepend newly uploaded reports (not yet in backend response)
    val allReports = uploadedReports + backendReports
    Column(
        Modifier
            .fillMaxSize()
            .background(VitalisBgApp)
            .verticalScroll(rememberScrollState())
            .padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        // ── Patient Summary with Environment ──
        PatientSummaryCard(data, locationAvailable, onRequestLocation)

        // ── Active Alerts (using real data from backend) ──
        ActiveAlertsSection(data)

        // ── Report Timeline ──
        ReportTimeline(reports = allReports)
    }
}

/* ── Patient Summary ─────────────────────────────────── */

@Composable
private fun PatientSummaryCard(
    data: DashboardData,
    locationAvailable: Boolean,
    onRequestLocation: () -> Unit
) {
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
                InfoChip(label = "Patient ID", value = data.userId.take(8) + "…")
            }

            // Environment Data or Location Request
            if (data.environment != null) {
                // Show environment data
                Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                    data.environment.weatherCondition?.let { weather ->
                        InfoChip(label = "Weather", value = weather)
                    }
                    data.environment.temperatureCelsius?.let { temp ->
                        InfoChip(label = "Temp", value = "${temp.toInt()}°C")
                    }
                }

                // AQI Display
                data.environment.aqiLevel?.let { aqi ->
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Text("AQI", style = MaterialTheme.typography.labelSmall, color = VitalisTextMuted)
                        Surface(
                            shape = RoundedCornerShape(6.dp),
                            color = getAqiColor(aqi).copy(alpha = .12f),
                        ) {
                            Text(
                                "$aqi",
                                modifier = Modifier.padding(horizontal = 10.dp, vertical = 3.dp),
                                style = MaterialTheme.typography.labelSmall,
                                fontWeight = FontWeight.SemiBold,
                                color = getAqiColor(aqi),
                            )
                        }
                        Text(
                            getAqiLabel(aqi),
                            style = MaterialTheme.typography.labelSmall,
                            color = VitalisTextMuted,
                        )
                    }
                }

                data.environment.locationCity?.let { city ->
                    Text(
                        "📍 $city",
                        style = MaterialTheme.typography.labelSmall,
                        color = VitalisTextMuted,
                    )
                }
            } else {
                // Show location request card
                Surface(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(12.dp),
                    color = VitalisWarning.copy(alpha = 0.1f),
                ) {
                    Row(
                        Modifier
                            .padding(12.dp)
                            .fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Row(
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Icon(
                                Icons.Outlined.LocationOff,
                                contentDescription = "Location Off",
                                tint = VitalisWarning,
                                modifier = Modifier.size(20.dp)
                            )
                            Column {
                                Text(
                                    "Weather data unavailable",
                                    style = MaterialTheme.typography.labelMedium,
                                    color = VitalisTextPrimary,
                                    fontWeight = FontWeight.Medium
                                )
                                Text(
                                    "Enable location for AQI & weather",
                                    style = MaterialTheme.typography.labelSmall,
                                    color = VitalisTextMuted
                                )
                            }
                        }
                        TextButton(onClick = onRequestLocation) {
                            Text("Enable", color = VitalisPrimary)
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun getAqiColor(aqi: Int): Color = when {
    aqi <= 50 -> VitalisSuccess
    aqi <= 100 -> Color(0xFFFFD93D) // Yellow
    aqi <= 150 -> VitalisWarning
    aqi <= 200 -> Color(0xFFFF6B6B) // Red-Orange
    else -> VitalisDanger
}

private fun getAqiLabel(aqi: Int): String = when {
    aqi <= 50 -> "Good"
    aqi <= 100 -> "Moderate"
    aqi <= 150 -> "Unhealthy for Sensitive"
    aqi <= 200 -> "Unhealthy"
    aqi <= 300 -> "Very Unhealthy"
    else -> "Hazardous"
}

@Composable
private fun InfoChip(label: String, value: String) {
    Column {
        Text(label, style = MaterialTheme.typography.labelSmall, color = VitalisTextMuted)
        Text(value, style = MaterialTheme.typography.bodyMedium, color = VitalisTextPrimary, fontWeight = FontWeight.Medium)
    }
}

/* ── Active Alerts Section (using real backend data) ────────────────────────────── */

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
                color = if (data.activeAlertsCount > 0) VitalisDanger.copy(alpha = .12f) else VitalisSuccess.copy(alpha = .12f),
            ) {
                Text(
                    "${data.activeAlertsCount}",
                    modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
                    style = MaterialTheme.typography.labelSmall,
                    fontWeight = FontWeight.Bold,
                    color = if (data.activeAlertsCount > 0) VitalisDanger else VitalisSuccess,
                )
            }
        }

        if (data.alerts.isEmpty()) {
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(14.dp),
                colors = CardDefaults.cardColors(containerColor = Color.White),
                elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
            ) {
                Column(
                    Modifier.padding(16.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                ) {
                    Text(
                        "✓ No active alerts",
                        style = MaterialTheme.typography.bodyMedium,
                        color = VitalisSuccess,
                        fontWeight = FontWeight.Medium,
                    )
                    Text(
                        "Your health metrics are within normal range",
                        style = MaterialTheme.typography.labelSmall,
                        color = VitalisTextMuted,
                    )
                }
            }
        } else {
            // Show up to 3 alerts on dashboard, prioritized by severity
            data.alerts.take(3).forEach { alert ->
                AlertDashboardCard(alert)
            }

            if (data.alerts.size > 3) {
                Text(
                    "View all ${data.alerts.size} alerts →",
                    style = MaterialTheme.typography.labelSmall,
                    color = VitalisPrimary,
                    fontWeight = FontWeight.Medium,
                    modifier = Modifier.padding(start = 4.dp),
                )
            }
        }
    }
}

@Composable
private fun AlertDashboardCard(alert: DashboardAlert) {
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
                    alert.severity.replaceFirstChar { it.uppercase() } + " Priority",
                    style = MaterialTheme.typography.labelSmall,
                    color = VitalisTextMuted,
                )
                SeverityBadge(alert.severity)
            }
            Text(
                alert.reason,
                style = MaterialTheme.typography.bodyMedium,
                color = VitalisTextPrimary,
            )
        }
    }
}

// ─── Alerts Tab ──────────────────────────────────────────

@Composable
fun AlertsScreen(vm: AlertsViewModel, userId: String) {
    val state by vm.alertsState.collectAsState()

    when (val s = state) {
        is AlertsViewModel.UiState.Loading -> VitalisLoadingScreen(label = "Checking for alerts…")
        is AlertsViewModel.UiState.Error -> VitalisErrorScreen(
            message = s.message,
            onRetry = { vm.retry() },
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
                    if (alert.evidence.isNotEmpty()) {
                        Spacer(Modifier.height(8.dp))
                        alert.evidence.firstOrNull()?.let { ev ->
                            Text(
                                "Report: ${ev.reportId?.take(8) ?: "—"}…",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun SeverityBadge(severity: String) {
    val color = when (severity) {
        "high" -> Color(0xFFC0392B)
        "medium" -> Color(0xFFC27817)
        else -> Color(0xFF1E7D5A)
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

/**
 * Convert a backend [ReportSummary] to a UI [ReportTimelineItem].
 */
private fun ReportSummary.toTimelineItem(): ReportTimelineItem {
    // Map report_type string to ReportType enum
    // Available: BLOOD, HEART, LAB, EXAM
    val type = when (reportType.lowercase()) {
        "blood", "blood_work" -> ReportType.BLOOD
        "cardiac", "heart", "ecg", "ekg" -> ReportType.HEART
        "exam", "examination", "physical" -> ReportType.EXAM
        else -> ReportType.LAB  // imaging, radiology, specialist all fallback to LAB
    }

    // Build a highlight message from available data
    val highlight = when {
        labResultsCount > 0 -> "$labResultsCount lab result${if (labResultsCount != 1) "s" else ""} extracted"
        processingStatus == "completed" -> "Report processed successfully"
        processingStatus == "pending" -> "Processing in progress…"
        else -> "Uploaded report"
    }

    return ReportTimelineItem(
        reportId = reportId,
        reportName = reportName,
        uploadDate = uploadDate,
        reportType = type,
        riskLabel = riskLabel,
        riskLevel = riskLevel,
        highlight = highlight,
        extractionMethod = ExtractionMethod.STANDARD,
        sourceFilename = storagePath?.substringAfterLast('/'),
        pageNumber = null
    )
}
