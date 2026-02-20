package com.vitalis.health.ui.example

import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.livedata.observeAsState
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.ViewModelProvider
import com.vitalis.health.VitalisApp
import com.vitalis.health.data.model.Alert
import com.vitalis.health.data.model.DashboardData
import com.vitalis.health.ui.AlertsViewModel
import com.vitalis.health.ui.AssistantViewModel
import com.vitalis.health.ui.DashboardViewModel

/**
 * Example Activity demonstrating full integration:
 *   UI → ViewModel → Repository → API Adapter → Backend
 *
 * Shows three tabs: Dashboard, Alerts, AI Chat
 */
class ExampleActivity : ComponentActivity() {

    private lateinit var dashboardVm: DashboardViewModel
    private lateinit var alertsVm: AlertsViewModel
    private lateinit var assistantVm: AssistantViewModel

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val factory = (application as VitalisApp).viewModelFactory
        dashboardVm = ViewModelProvider(this, factory)[DashboardViewModel::class.java]
        alertsVm = ViewModelProvider(this, factory)[AlertsViewModel::class.java]
        assistantVm = ViewModelProvider(this, factory)[AssistantViewModel::class.java]

        // Kick off data loads
        val userId = "patient_001"
        dashboardVm.loadDashboard(userId)
        alertsVm.loadAlerts(userId)

        setContent {
            MaterialTheme {
                MainScreen(
                    dashboardVm = dashboardVm,
                    alertsVm = alertsVm,
                    assistantVm = assistantVm,
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
    userId: String
) {
    var selectedTab by remember { mutableIntStateOf(0) }
    val tabs = listOf("Dashboard", "Alerts", "Assistant")

    Scaffold(
        bottomBar = {
            NavigationBar {
                tabs.forEachIndexed { index, title ->
                    NavigationBarItem(
                        selected = selectedTab == index,
                        onClick = { selectedTab = index },
                        label = { Text(title) },
                        icon = {}
                    )
                }
            }
        }
    ) { padding ->
        Box(Modifier.padding(padding)) {
            when (selectedTab) {
                0 -> DashboardScreen(dashboardVm)
                1 -> AlertsScreen(alertsVm)
                2 -> AssistantScreen(assistantVm, userId)
            }
        }
    }
}

// ─── Dashboard Tab ───────────────────────────────────────

@Composable
fun DashboardScreen(vm: DashboardViewModel) {
    val state by vm.dashboardState.observeAsState()

    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        when (val s = state) {
            is DashboardViewModel.UiState.Loading -> CircularProgressIndicator()
            is DashboardViewModel.UiState.Error   -> ErrorText(s.message)
            is DashboardViewModel.UiState.Success -> DashboardContent(s.data)
            null -> Text("Idle")
        }
    }
}

@Composable
fun DashboardContent(data: DashboardData) {
    Column(
        Modifier
            .fillMaxSize()
            .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Text(data.greeting, style = MaterialTheme.typography.headlineMedium)
        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(16.dp)) {
                Text("Wellbeing Score", fontWeight = FontWeight.Bold)
                Text(
                    "${data.wellbeingScore}/100",
                    style = MaterialTheme.typography.displaySmall,
                    color = MaterialTheme.colorScheme.primary
                )
                Text("Trend: ${data.wellbeingTrend}")
            }
        }
        data.environment?.let { env ->
            Card(Modifier.fillMaxWidth()) {
                Row(Modifier.padding(16.dp), horizontalArrangement = Arrangement.spacedBy(24.dp)) {
                    env.aqi?.let { Text("AQI: $it") }
                    env.weather?.let { Text("Weather: $it") }
                }
            }
        }
        Text("Active alerts: ${data.activeAlertsCount}")
    }
}

// ─── Alerts Tab ──────────────────────────────────────────

@Composable
fun AlertsScreen(vm: AlertsViewModel) {
    val state by vm.alertsState.observeAsState()

    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        when (val s = state) {
            is AlertsViewModel.UiState.Loading -> CircularProgressIndicator()
            is AlertsViewModel.UiState.Error   -> ErrorText(s.message)
            is AlertsViewModel.UiState.Success -> AlertsList(s.alerts)
            null -> Text("Idle")
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
                                msg.citations.forEach { c ->
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

            // Loading indicator
            if (uiState is AssistantViewModel.UiState.Loading) {
                item {
                    CircularProgressIndicator(Modifier.padding(8.dp))
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

// ─── Shared ──────────────────────────────────────────────

@Composable
fun ErrorText(message: String) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text("Something went wrong", fontWeight = FontWeight.Bold, color = Color(0xFFC0392B))
        Spacer(Modifier.height(4.dp))
        Text(message, style = MaterialTheme.typography.bodySmall)
    }
}
