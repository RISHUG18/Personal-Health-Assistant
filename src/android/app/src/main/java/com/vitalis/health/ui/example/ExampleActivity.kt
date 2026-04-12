package com.vitalis.health.ui.example

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.location.Address
import android.location.Geocoder
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.Crossfade
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.automirrored.filled.ArrowForward
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.Send
import androidx.compose.material.icons.automirrored.outlined.VolumeUp
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.outlined.CloudUpload
import androidx.compose.material.icons.outlined.Description
import androidx.compose.material.icons.outlined.Favorite
import androidx.compose.material.icons.outlined.Forum
import androidx.compose.material.icons.outlined.MonitorHeart
import androidx.compose.material.icons.outlined.Notifications
import androidx.compose.material.icons.outlined.Person
import androidx.compose.material.icons.outlined.SmartToy
import androidx.compose.material.icons.outlined.Refresh
import androidx.compose.material.icons.outlined.SpaceDashboard
import androidx.compose.material.icons.outlined.StopCircle
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.livedata.observeAsState
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.blur
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import androidx.lifecycle.ViewModelProvider
import com.google.android.gms.location.FusedLocationProviderClient
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import com.google.android.gms.tasks.CancellationTokenSource
import com.vitalis.health.VitalisApp
import com.vitalis.health.data.local.ThemePreferences
import com.vitalis.health.data.model.Alert
import com.vitalis.health.data.model.DashboardAlert
import com.vitalis.health.data.model.DashboardData
import com.vitalis.health.data.model.HealthSummary
import com.vitalis.health.ui.AlertsViewModel
import com.vitalis.health.ui.AssistantViewModel
import com.vitalis.health.ui.AuthViewModel
import com.vitalis.health.ui.DashboardViewModel
import com.vitalis.health.ui.ReportDetailViewModel
import com.vitalis.health.ui.ReportUploadViewModel
import com.vitalis.health.ui.VitalsViewModel
import com.vitalis.health.ui.VitalsViewModelFactory
import com.vitalis.health.ui.components.LoginScreen
import com.vitalis.health.ui.components.RegisterScreen
import com.vitalis.health.ui.components.ReportTimelineItem
import com.vitalis.health.ui.components.ReportType
import com.vitalis.health.ui.components.EnvironmentCard
import com.vitalis.health.ui.components.ExtractionMethod
import com.vitalis.health.ui.components.HealthSummaryCard
import com.vitalis.health.data.model.ReportSummary
import com.vitalis.health.ui.components.ChatScreen
import com.vitalis.health.ui.components.ProfileEditScreen
import com.vitalis.health.ui.components.ReportUploadScreen
import com.vitalis.health.ui.components.ReportDetailScreen
import com.vitalis.health.ui.components.SettingsScreen
import com.vitalis.health.ui.components.VoiceAssistantVisualState
import com.vitalis.health.ui.components.VitalsDashboardScreen
import com.vitalis.health.ui.components.VitalisEmptyScreen
import com.vitalis.health.ui.components.VitalisErrorScreen
import com.vitalis.health.ui.components.VitalisLoadingScreen
import com.vitalis.health.ui.theme.VitalisAccentWarm
import com.vitalis.health.ui.theme.VitalisDanger
import com.vitalis.health.ui.theme.VitalisPrimary
import com.vitalis.health.ui.theme.VitalisPrimaryDeeper
import com.vitalis.health.ui.theme.VitalisSuccess
import com.vitalis.health.ui.theme.LocalVitalisColors
import com.vitalis.health.ui.theme.ThemeViewModel
import com.vitalis.health.ui.theme.ThemeViewModelFactory
import com.vitalis.health.ui.theme.VitalisTheme
import com.vitalis.health.ui.theme.VitalisWarning
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow

/**
 * App navigation state for auth vs main flow
 */
enum class AppState {
    LOGIN,
    REGISTER,
    MAIN
}

private enum class AssistantInputMode {
    Voice,
    Text,
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
    private lateinit var reportDetailVm: ReportDetailViewModel
    private lateinit var authVm: AuthViewModel
    private lateinit var vitalsVm: VitalsViewModel
    private lateinit var themeVm: ThemeViewModel
    private lateinit var fusedLocationClient: FusedLocationProviderClient
    private val listeningState = MutableStateFlow(false)
    private val speakingState = MutableStateFlow(false)

    // Voice integration
    private lateinit var ttsHelper: com.vitalis.health.voice.TTSHelper
    private lateinit var sttHelper: com.vitalis.health.voice.SpeechRecognizerHelper

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        ttsHelper = com.vitalis.health.voice.TTSHelper(this)
        ttsHelper.initialize()
        
        sttHelper = com.vitalis.health.voice.SpeechRecognizerHelper(this)
        sttHelper.initialize()
        sttHelper.onListeningStateChanged = { isListening ->
            listeningState.value = isListening
        }
        sttHelper.onReady = {
            assistantVm.setVoiceCaptureError(null)
        }
        sttHelper.onError = { errorMessage ->
            listeningState.value = false
            assistantVm.setVoiceCaptureError(errorMessage)
        }

        sttHelper.onPartialResult = { partialText ->
            assistantVm.updatePartialTranscript(partialText)
        }
        
        sttHelper.onResult = { text ->
            assistantVm.updatePartialTranscript(text)
            assistantVm.setVoiceDraft(text)
        }

        // Initialize location client
        fusedLocationClient = LocationServices.getFusedLocationProviderClient(this)

        val app = application as VitalisApp
        val factory = app.viewModelFactory
        dashboardVm = ViewModelProvider(this, factory)[DashboardViewModel::class.java]
        alertsVm = ViewModelProvider(this, factory)[AlertsViewModel::class.java]
        assistantVm = ViewModelProvider(this, factory)[AssistantViewModel::class.java]
        uploadVm = ViewModelProvider(this, factory)[ReportUploadViewModel::class.java]
        reportDetailVm = ViewModelProvider(this, factory)[ReportDetailViewModel::class.java]
        authVm = ViewModelProvider(this, factory)[AuthViewModel::class.java]
        themeVm = ViewModelProvider(
            this,
            ThemeViewModelFactory(ThemePreferences(applicationContext))
        )[ThemeViewModel::class.java]
        
        // Listen to voice responses to speak them out loud
        assistantVm.voiceResponse.observe(this) { responseText ->
            if (!responseText.isNullOrEmpty()) {
                ttsHelper.speak(stripMarkdownForSpeech(responseText))
                assistantVm.clearVoiceResponse()
            }
        }
        ttsHelper.onSpeakingStateChanged = { isSpeaking ->
            speakingState.value = isSpeaking
        }

        // Use the application-level HealthConnectManager (survives Activity configuration changes)
        val vitalsFactory = VitalsViewModelFactory(
            app.repository,
            app.vitalsSyncPreferences,
            app.healthConnectManager,
        )
        vitalsVm = ViewModelProvider(this, vitalsFactory)[VitalsViewModel::class.java]

        setContent {
            val isDarkThemeEnabled by themeVm.isDarkThemeEnabled.collectAsState()
            val authSessionVersion by authVm.sessionVersion.collectAsState()
            val isListening by listeningState.collectAsState()
            val isSpeaking by speakingState.collectAsState()
            var appState by remember {
                mutableStateOf(
                    if (authVm.isLoggedIn()) AppState.MAIN else AppState.LOGIN
                )
            }

            LaunchedEffect(authSessionVersion) {
                if (!authVm.isLoggedIn()) {
                    ttsHelper.stop()
                    sttHelper.stopListening()
                    dashboardVm.clearCachedDashboard()
                    assistantVm.clearConversation()
                    listeningState.value = false
                    speakingState.value = false
                    appState = AppState.LOGIN
                }
            }

            VitalisTheme(darkTheme = isDarkThemeEnabled) {
                when (appState) {
                    AppState.LOGIN -> {
                        LoginScreen(
                            viewModel = authVm,
                            onLoginSuccess = { userId ->
                                dashboardVm.clearCachedDashboard()
                                assistantVm.clearConversation()
                                authVm.fetchUserProfile(userId, forceRefresh = true)
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
                                dashboardVm.clearCachedDashboard()
                                assistantVm.clearConversation()
                                authVm.fetchUserProfile(userId, forceRefresh = true)
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
                                authVm.fetchUserProfile(userId, forceRefresh = true)
                            }

                            MainScreen(
                                authVm = authVm,
                                dashboardVm = dashboardVm,
                                alertsVm = alertsVm,
                                assistantVm = assistantVm,
                                uploadVm = uploadVm,
                                reportDetailVm = reportDetailVm,
                                vitalsVm = vitalsVm,
                                userId = userId,
                                fusedLocationClient = fusedLocationClient,
                                isDarkThemeEnabled = isDarkThemeEnabled,
                                onDarkThemeEnabledChange = themeVm::setDarkThemeEnabled,
                                isListening = isListening,
                                isSpeaking = isSpeaking,
                                onStartVoiceInput = { sttHelper.startListening() },
                                onStopVoiceInput = { sttHelper.stopListening() },
                                onSpeakMessage = { message ->
                                    ttsHelper.speak(stripMarkdownForSpeech(message))
                                },
                                onStopSpeaking = {
                                    ttsHelper.stop()
                                },
                                onLogoutClick = {
                                    ttsHelper.stop()
                                    sttHelper.stopListening()
                                    authVm.logout()
                                    dashboardVm.clearCachedDashboard()
                                    assistantVm.clearConversation()
                                    appState = AppState.LOGIN
                                }
                            )
                        }
                    }
                }
            }
        }
    }

    override fun onDestroy() {
        ttsHelper.destroy()
        sttHelper.destroy()
        super.onDestroy()
    }

    private fun stripMarkdownForSpeech(text: String): String {
        return text.replace(Regex("\\*\\*(.+?)\\*\\*"), "$1")
    }
}

// ─── Compose UI ──────────────────────────────────────────

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MainScreen(
    authVm: AuthViewModel,
    dashboardVm: DashboardViewModel,
    alertsVm: AlertsViewModel,
    assistantVm: AssistantViewModel,
    uploadVm: ReportUploadViewModel,
    reportDetailVm: ReportDetailViewModel,
    vitalsVm: VitalsViewModel,
    userId: String,
    fusedLocationClient: FusedLocationProviderClient,
    isDarkThemeEnabled: Boolean,
    onDarkThemeEnabledChange: (Boolean) -> Unit,
    isListening: Boolean,
    isSpeaking: Boolean,
    onStartVoiceInput: () -> Unit = {},
    onStopVoiceInput: () -> Unit = {},
    onSpeakMessage: (String) -> Unit = {},
    onStopSpeaking: () -> Unit = {},
    onLogoutClick: () -> Unit = {}
) {
    val colors = LocalVitalisColors.current
    val context = LocalContext.current
    var selectedTab by remember { mutableIntStateOf(0) }
    var showProfileEdit by remember { mutableStateOf(false) }
    val currentProfile by authVm.currentUserProfile.collectAsStateWithLifecycle()
    val profileState by authVm.profileState.collectAsStateWithLifecycle()
    val assistantUiState by assistantVm.uiState.observeAsState(AssistantViewModel.UiState.Idle)
    val transcriptDraft by assistantVm.voiceDraft.collectAsState()
    val partialTranscript by assistantVm.partialTranscript.collectAsState()
    val voiceCaptureError by assistantVm.voiceCaptureError.collectAsState()
    val vitalsSummaryState by vitalsVm.summaryState.collectAsState()

    var showVoiceOverlay by remember { mutableStateOf(false) }
    var countdownSeconds by remember { mutableStateOf<Int?>(null) }
    var lastAutoSubmittedTranscript by remember { mutableStateOf("") }
    var inputMode by remember { mutableStateOf(AssistantInputMode.Text) }
    var hasSpeechCapturedDraft by remember { mutableStateOf(false) }
    var awaitingVoiceResponse by remember { mutableStateOf(false) }

    val openOverlayAndStartListening: () -> Unit = {
        showVoiceOverlay = true
        countdownSeconds = null
        lastAutoSubmittedTranscript = ""
        inputMode = AssistantInputMode.Voice
        hasSpeechCapturedDraft = false
        assistantVm.resetVoiceComposer()
        assistantVm.setVoiceCaptureError(null)
        onStartVoiceInput()
    }

    val audioPermissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        if (isGranted) {
            openOverlayAndStartListening()
        } else {
            assistantVm.setVoiceCaptureError("Microphone permission denied")
            Toast.makeText(context, "Microphone permission denied", Toast.LENGTH_SHORT).show()
        }
    }

    val requestMicAndStart: () -> Unit = {
        val hasMicPermission = ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.RECORD_AUDIO
        ) == PackageManager.PERMISSION_GRANTED

        if (hasMicPermission) {
            openOverlayAndStartListening()
        } else {
            audioPermissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
        }
    }

    LaunchedEffect(selectedTab) {
        if (selectedTab != 5) {
            showProfileEdit = false
        }
    }

    LaunchedEffect(selectedTab, userId, currentProfile?.id, profileState) {
        if (
            selectedTab == 5 &&
            currentProfile?.id != userId &&
            profileState is AuthViewModel.ProfileUiState.Idle
        ) {
            authVm.fetchUserProfile(userId, forceRefresh = true)
        }
    }

    LaunchedEffect(isListening, transcriptDraft) {
        if (isListening && transcriptDraft.isNotBlank()) {
            inputMode = AssistantInputMode.Voice
            hasSpeechCapturedDraft = true
        }
    }

    LaunchedEffect(assistantUiState, awaitingVoiceResponse) {
        if (!awaitingVoiceResponse) {
            return@LaunchedEffect
        }
        if (
            assistantUiState is AssistantViewModel.UiState.Success ||
            assistantUiState is AssistantViewModel.UiState.Error
        ) {
            showVoiceOverlay = false
            countdownSeconds = null
            awaitingVoiceResponse = false
            inputMode = AssistantInputMode.Text
            hasSpeechCapturedDraft = false
        }
    }

    // Track uploaded reports to prepend to timeline
    val uploadedReports = remember { mutableStateListOf<ReportTimelineItem>() }
    val deletedReportIds = remember { mutableStateListOf<String>() }

    // Track the report currently being viewed in detail
    val dashboardState by dashboardVm.dashboardState.collectAsState()
    val uploadState by uploadVm.uiState.observeAsState(ReportUploadViewModel.UiState.Idle)
    val deleteReportState by uploadVm.deleteReportState.observeAsState(ReportUploadViewModel.DeleteReportState.Idle)
    var viewingReportId by remember { mutableStateOf<String?>(null) }

    val backendReports = when (val state = dashboardState) {
        is DashboardViewModel.UiState.Success ->
            state.data.reports
                .map { report -> report.toTimelineItem() }
                .filterNot { item -> deletedReportIds.contains(item.reportId) }
        is DashboardViewModel.UiState.LocationPermissionRequired ->
            state.data?.reports
                ?.map { report -> report.toTimelineItem() }
                ?.filterNot { item -> deletedReportIds.contains(item.reportId) }
                ?: emptyList()
        else -> emptyList()
    }
    val recordsReports = (uploadedReports + backendReports)
        .filterNot { item -> deletedReportIds.contains(item.reportId) }
        .distinctBy { it.reportId }
    val isReportsLoading =
        dashboardState is DashboardViewModel.UiState.Loading && recordsReports.isEmpty()

    // When upload succeeds, build a timeline item and prepend it
    LaunchedEffect(uploadState) {
        if (uploadState is ReportUploadViewModel.UiState.Success) {
            val result = (uploadState as ReportUploadViewModel.UiState.Success).result
            val newItem = ReportTimelineItem(
                reportId = result.reportId,
                reportName = "Report ${result.reportId.take(8)}",
                uploadDate = "Just now",
                reportType = ReportType.LAB,
                riskLabel = "New",
                riskLevel = "normal",
                highlight = result.ocrTextPreview.take(80).ifEmpty { "Report processed" },
                extractionMethod = ExtractionMethod.STANDARD,
                sourceFilename = result.storagePath.substringAfterLast('/'),
                pageNumber = null,
            )
            // Prepend only if not already present
            if (uploadedReports.none { it.reportId == newItem.reportId }) {
                uploadedReports.add(0, newItem)
            }
        }
    }

    LaunchedEffect(deleteReportState) {
        when (val state = deleteReportState) {
            is ReportUploadViewModel.DeleteReportState.Success -> {
                deletedReportIds.add(state.reportId)
                uploadedReports.removeAll { it.reportId == state.reportId }
                if (viewingReportId == state.reportId) {
                    viewingReportId = null
                }
                dashboardVm.refreshDashboard()
                Toast.makeText(
                    context,
                    if (state.alertsDeleted > 0) {
                        "Report deleted. ${state.alertsDeleted} linked alerts removed."
                    } else {
                        "Report deleted successfully"
                    },
                    Toast.LENGTH_SHORT,
                ).show()
                uploadVm.resetDeleteReportState()
            }

            is ReportUploadViewModel.DeleteReportState.Error -> {
                Toast.makeText(context, state.message, Toast.LENGTH_LONG).show()
                uploadVm.resetDeleteReportState()
            }

            else -> {
                // no-op
            }
        }
    }

    LaunchedEffect(
        showVoiceOverlay,
        isListening,
        isSpeaking,
        transcriptDraft,
        assistantUiState,
        inputMode,
        hasSpeechCapturedDraft,
    ) {
        if (!showVoiceOverlay) {
            countdownSeconds = null
            return@LaunchedEffect
        }

        val candidate = transcriptDraft.trim()
        if (
            inputMode != AssistantInputMode.Voice ||
            !hasSpeechCapturedDraft ||
            isListening ||
            isSpeaking ||
            assistantUiState is AssistantViewModel.UiState.Loading ||
            candidate.isEmpty() ||
            candidate == lastAutoSubmittedTranscript
        ) {
            countdownSeconds = null
            return@LaunchedEffect
        }

        onStopVoiceInput()
        for (remaining in 3 downTo 1) {
            countdownSeconds = remaining
            delay(1000)
        }
        countdownSeconds = null
        lastAutoSubmittedTranscript = candidate
        awaitingVoiceResponse = true
        assistantVm.sendVoiceQuery(userId, candidate)
    }

    val overlayState = when {
        isListening -> VoiceAssistantVisualState.Listening
        countdownSeconds != null -> VoiceAssistantVisualState.Countdown
        awaitingVoiceResponse && assistantUiState is AssistantViewModel.UiState.Loading ->
            VoiceAssistantVisualState.Processing
        else -> VoiceAssistantVisualState.Idle
    }

    val overlayVisible =
        showVoiceOverlay &&
            (
                isListening ||
                    countdownSeconds != null ||
                    (awaitingVoiceResponse && assistantUiState is AssistantViewModel.UiState.Loading)
                )

    val liveTranscript = if (isListening) {
        partialTranscript.ifBlank { transcriptDraft }
    } else {
        transcriptDraft
    }

    val contextualChips = remember(vitalsSummaryState, currentProfile, uploadedReports.size) {
        val sleepHours = vitalsVm.getTotalSleepHours()
        val restingHeartRate = vitalsVm.getRestingHeartRate()
        listOf(
            if (uploadedReports.isNotEmpty()) {
                "Summarize my latest blood work"
            } else {
                "Summarize my recent health trends"
            },
            if ((sleepHours ?: 8.0) < 7.0) {
                "Why is my sleep score low?"
            } else {
                "How can I improve tonight's sleep quality?"
            },
            if (restingHeartRate != null) {
                "Explain my resting heart rate trend"
            } else {
                "What should I focus on for recovery this week?"
            },
        )
    }

    // If detail screen is open, show it instead of tabs
    val activeReportId = viewingReportId
    if (activeReportId != null) {
        val activeReportName = recordsReports
            .firstOrNull { it.reportId == activeReportId }
            ?.sourceFilename
            ?: recordsReports.firstOrNull { it.reportId == activeReportId }?.reportName

        ReportDetailScreen(
            reportId = activeReportId,
            originalReportName = activeReportName,
            viewModel = reportDetailVm,
            onBack = { viewingReportId = null },
        )
        return
    }

    Box(Modifier.fillMaxSize()) {
        Box(
            modifier = Modifier.fillMaxSize()
        ) {
            Scaffold(
                bottomBar = {
                    VitalisBottomNavBar(
                        selectedTab = selectedTab,
                        onTabSelected = { selectedTab = it },
                        onVoiceFabClick = {
                            selectedTab = 4
                        }
                    )
                }
            ) { padding ->
                Box(
                    Modifier
                        .padding(padding)
                        .fillMaxSize()
                        .background(colors.bgApp)
                ) {
                    when (selectedTab) {
                        0 -> DashboardScreen(
                            vm = dashboardVm,
                            userId = userId,
                            fusedLocationClient = fusedLocationClient,
                            onViewAllAlerts = {
                                selectedTab = 3
                            },
                        )
                        1 -> VitalsDashboardScreen(
                            viewModel = vitalsVm,
                            userId = userId
                        )
                        2 -> ReportUploadScreen(
                            viewModel = uploadVm,
                            userId = userId,
                            reports = recordsReports,
                            isReportsLoading = isReportsLoading,
                            onViewReport = { reportId ->
                                viewingReportId = reportId
                            },
                            onDeleteReport = { reportId ->
                                uploadVm.deleteReport(reportId)
                            },
                            onViewResult = {
                                val reportId =
                                    (uploadState as? ReportUploadViewModel.UiState.Success)
                                        ?.result
                                        ?.reportId
                                if (!reportId.isNullOrBlank()) {
                                    viewingReportId = reportId
                                }
                            },
                        )
                        3 -> com.vitalis.health.ui.components.AlertsScreen(viewModel = alertsVm)
                        4 -> ChatScreen(
                            vm = assistantVm,
                            userId = userId,
                            isListening = isListening,
                            isSpeaking = isSpeaking,
                            voiceOverlayVisible = overlayVisible,
                            voiceOverlayState = overlayState,
                            voiceTranscript = liveTranscript,
                            voiceCountdownSeconds = countdownSeconds,
                            voiceStatusMessage = voiceCaptureError,
                            voiceSuggestionChips = contextualChips,
                            onVoiceInput = requestMicAndStart,
                            onSpeakMessage = onSpeakMessage,
                            onStopSpeaking = onStopSpeaking,
                            onTextModeActivated = {
                                inputMode = AssistantInputMode.Text
                                hasSpeechCapturedDraft = false
                                countdownSeconds = null
                                showVoiceOverlay = false
                                awaitingVoiceResponse = false
                                onStopVoiceInput()
                            },
                            onOverlayDismiss = {
                                showVoiceOverlay = false
                                countdownSeconds = null
                                awaitingVoiceResponse = false
                                inputMode = AssistantInputMode.Text
                                hasSpeechCapturedDraft = false
                                onStopVoiceInput()
                            },
                            onOverlayStartListening = {
                                requestMicAndStart()
                            },
                            onOverlayStopListening = {
                                onStopVoiceInput()
                            },
                            onOverlaySendNow = {
                                val cleaned = transcriptDraft.trim()
                                if (cleaned.isNotEmpty()) {
                                    inputMode = AssistantInputMode.Voice
                                    countdownSeconds = null
                                    lastAutoSubmittedTranscript = cleaned
                                    awaitingVoiceResponse = true
                                    onStopVoiceInput()
                                    assistantVm.sendVoiceQuery(userId, cleaned)
                                }
                            },
                            onOverlaySuggestionSelected = { prompt ->
                                val cleaned = prompt.trim()
                                if (cleaned.isNotEmpty()) {
                                    inputMode = AssistantInputMode.Voice
                                    hasSpeechCapturedDraft = false
                                    countdownSeconds = null
                                    awaitingVoiceResponse = true
                                    onStopVoiceInput()
                                    assistantVm.resetVoiceComposer()
                                    assistantVm.setVoiceDraft(cleaned)
                                    lastAutoSubmittedTranscript = cleaned
                                    assistantVm.sendVoiceQuery(userId, cleaned)
                                }
                            },
                        )
                        5 -> {
                            val profileReady = currentProfile?.id == userId
                            val profileError = profileState as? AuthViewModel.ProfileUiState.Error

                            if (profileError != null) {
                                VitalisErrorScreen(
                                    message = profileError.message,
                                    onRetry = {
                                        authVm.fetchUserProfile(userId, forceRefresh = true)
                                    },
                                )
                            } else if (!profileReady) {
                                VitalisLoadingScreen(label = "Loading profile...")
                            } else if (showProfileEdit) {
                                ProfileEditScreen(
                                    viewModel = authVm,
                                    userId = userId,
                                    currentProfile = currentProfile,
                                    onNavigateBack = { showProfileEdit = false },
                                )
                            } else {
                                SettingsScreen(
                                    viewModel = authVm,
                                    userId = userId,
                                    onNavigateToProfileEdit = { showProfileEdit = true },
                                    onNavigateToLogin = onLogoutClick,
                                    onNavigateBack = { selectedTab = 0 },
                                    isDarkThemeEnabled = isDarkThemeEnabled,
                                    onDarkThemeChanged = onDarkThemeEnabledChange,
                                )
                            }
                        }
                    }
                }
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
    onViewAllAlerts: () -> Unit,
) {
    val context = LocalContext.current
    val state by vm.dashboardState.collectAsState()
    val latestSummary by vm.latestSummary.collectAsState()
    val isGeneratingSummary by vm.isGeneratingSummary.collectAsState()

    // Location permission launcher
    val locationPermissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        val fineLocationGranted = permissions[Manifest.permission.ACCESS_FINE_LOCATION] == true
        val coarseLocationGranted = permissions[Manifest.permission.ACCESS_COARSE_LOCATION] == true

        if (fineLocationGranted || coarseLocationGranted) {
            // Permission granted, fetch location
            fetchLocation(
                context = context.applicationContext,
                fusedLocationClient = fusedLocationClient,
            ) { location ->
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
        if (vm.hasCachedDashboard(userId)) {
            return@LaunchedEffect
        }

        val hasLocationPermission = ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.ACCESS_FINE_LOCATION
        ) == PackageManager.PERMISSION_GRANTED || ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.ACCESS_COARSE_LOCATION
        ) == PackageManager.PERMISSION_GRANTED

        if (hasLocationPermission) {
            // Fetch location and load dashboard
            fetchLocation(
                context = context.applicationContext,
                fusedLocationClient = fusedLocationClient,
            ) { location ->
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
            onRefresh = { vm.refreshDashboard() },
            onRequestLocation = {
                locationPermissionLauncher.launch(
                    arrayOf(
                        Manifest.permission.ACCESS_FINE_LOCATION,
                        Manifest.permission.ACCESS_COARSE_LOCATION
                    )
                )
            },
            latestSummary = latestSummary,
            isGeneratingSummary = isGeneratingSummary,
            onGenerateFreshSummary = { vm.generateNewSummary() },
            onViewAllAlerts = onViewAllAlerts,
        )
        is DashboardViewModel.UiState.LocationPermissionRequired -> {
            if (s.data != null) {
                DashboardContent(
                    data = s.data,
                    locationAvailable = false,
                    onRefresh = { vm.refreshDashboard() },
                    onRequestLocation = {
                        locationPermissionLauncher.launch(
                            arrayOf(
                                Manifest.permission.ACCESS_FINE_LOCATION,
                                Manifest.permission.ACCESS_COARSE_LOCATION
                            )
                        )
                    },
                    latestSummary = latestSummary,
                    isGeneratingSummary = isGeneratingSummary,
                    onGenerateFreshSummary = { vm.generateNewSummary() },
                    onViewAllAlerts = onViewAllAlerts,
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
    context: Context,
    fusedLocationClient: FusedLocationProviderClient,
    onLocationReceived: (DashboardViewModel.LocationData?) -> Unit
) {
    try {
        val cancellationTokenSource = CancellationTokenSource()
        fusedLocationClient.getCurrentLocation(
            Priority.PRIORITY_BALANCED_POWER_ACCURACY,
            cancellationTokenSource.token
        ).addOnSuccessListener { location ->
            if (location != null) {
                resolveCityName(
                    context = context,
                    latitude = location.latitude,
                    longitude = location.longitude,
                ) { cityName ->
                    onLocationReceived(
                        DashboardViewModel.LocationData(
                            latitude = location.latitude,
                            longitude = location.longitude,
                            city = cityName,
                        )
                    )
                }
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

private fun resolveCityName(
    context: Context,
    latitude: Double,
    longitude: Double,
    onCityResolved: (String?) -> Unit,
) {
    val coordinateFallback = String.format(java.util.Locale.US, "%.2f, %.2f", latitude, longitude)

    if (!Geocoder.isPresent()) {
        onCityResolved(coordinateFallback)
        return
    }

    val geocoder = Geocoder(context, java.util.Locale.getDefault())
    val mainHandler = Handler(Looper.getMainLooper())

    fun extractCityName(addresses: List<Address>?): String? {
        val firstAddress = addresses?.firstOrNull() ?: return null
        return (
            firstAddress.locality
                ?: firstAddress.subAdminArea
                ?: firstAddress.adminArea
            )?.takeIf { it.isNotBlank() }
    }

    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
        try {
            geocoder.getFromLocation(
                latitude,
                longitude,
                1,
                object : Geocoder.GeocodeListener {
                    override fun onGeocode(addresses: List<Address>) {
                        val resolved = extractCityName(addresses) ?: coordinateFallback
                        mainHandler.post { onCityResolved(resolved) }
                    }

                    override fun onError(errorMessage: String?) {
                        mainHandler.post { onCityResolved(coordinateFallback) }
                    }
                },
            )
        } catch (_: Exception) {
            onCityResolved(coordinateFallback)
        }
        return
    }

    Thread {
        val city = try {
            @Suppress("DEPRECATION")
            extractCityName(geocoder.getFromLocation(latitude, longitude, 1)) ?: coordinateFallback
        } catch (_: Exception) {
            coordinateFallback
        }
        mainHandler.post { onCityResolved(city) }
    }.start()
}

@Composable
fun DashboardContent(
    data: DashboardData,
    locationAvailable: Boolean,
    onRefresh: () -> Unit,
    onRequestLocation: () -> Unit,
    latestSummary: HealthSummary?,
    isGeneratingSummary: Boolean,
    onGenerateFreshSummary: () -> Unit,
    onViewAllAlerts: () -> Unit,
) {
    val colors = LocalVitalisColors.current

    Column(
        Modifier
            .fillMaxSize()
            .background(colors.bgApp)
            .verticalScroll(rememberScrollState())
            .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        DashboardHeaderCard(
            data = data,
            onRefresh = onRefresh,
        )

        EnvironmentCard(
            environmentData = data.environment,
            locationAvailable = locationAvailable,
            onRequestPermission = onRequestLocation,
        )

        HealthSummaryCard(
            summary = latestSummary,
            isGeneratingSummary = isGeneratingSummary,
            onGenerateFreshSummary = onGenerateFreshSummary,
        )

        // ── Active Alerts (using real data from backend) ──
        ActiveAlertsSection(
            data = data,
            onViewAllClick = onViewAllAlerts,
        )
    }
}

/* ── Patient Summary ─────────────────────────────────── */

@Composable
private fun DashboardHeaderCard(
    data: DashboardData,
    onRefresh: () -> Unit,
) {
    val colors = LocalVitalisColors.current
    var refreshPulseTick by remember { mutableIntStateOf(0) }
    val refreshRotation by animateFloatAsState(
        targetValue = refreshPulseTick * 360f,
        animationSpec = tween(durationMillis = 420, easing = LinearEasing),
        label = "home_refresh_rotation",
    )

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .shadow(
                elevation = 3.dp,
                shape = RoundedCornerShape(18.dp),
                ambientColor = VitalisPrimary.copy(alpha = 0.12f),
                spotColor = VitalisPrimary.copy(alpha = 0.12f)
            ),
        shape = RoundedCornerShape(18.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(18.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Top,
            ) {
                Column(
                    modifier = Modifier.weight(1f),
                    verticalArrangement = Arrangement.spacedBy(3.dp),
                ) {
                    Text(
                        text = data.greeting,
                        style = MaterialTheme.typography.headlineSmall,
                        color = colors.textPrimary,
                        fontWeight = FontWeight.Bold,
                    )
                    Text(
                        text = "Your care dashboard",
                        style = MaterialTheme.typography.bodySmall,
                        color = colors.textMuted,
                    )
                }

                Surface(
                    shape = CircleShape,
                    color = colors.bgApp,
                    tonalElevation = 0.dp,
                ) {
                    IconButton(
                        onClick = {
                            refreshPulseTick += 1
                            onRefresh()
                        },
                        modifier = Modifier.size(38.dp),
                    ) {
                        Icon(
                            imageVector = Icons.Outlined.Refresh,
                            contentDescription = "Refresh",
                            tint = VitalisPrimary,
                            modifier = Modifier
                                .size(20.dp)
                                .graphicsLayer(rotationZ = refreshRotation),
                        )
                    }
                }
            }

            Row(
                horizontalArrangement = Arrangement.spacedBy(10.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                HeaderBadge(
                    label = "Active Alerts",
                    value = data.activeAlertsCount.toString(),
                    isAlert = data.activeAlertsCount > 0,
                )
            }
        }
    }
}

@Composable
private fun HeaderBadge(
    label: String,
    value: String,
    isAlert: Boolean = false,
) {
    val colors = LocalVitalisColors.current
    val badgeBackground = when {
        isAlert -> VitalisDanger.copy(alpha = 0.12f)
        else -> colors.bgApp
    }
    val valueColor = when {
        isAlert -> VitalisDanger
        else -> colors.textPrimary
    }

    Surface(
        shape = RoundedCornerShape(999.dp),
        color = badgeBackground,
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 7.dp),
            horizontalArrangement = Arrangement.spacedBy(6.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                text = label,
                style = MaterialTheme.typography.labelSmall,
                color = colors.textMuted,
            )
            Text(
                text = value,
                style = MaterialTheme.typography.labelMedium,
                color = valueColor,
                fontWeight = FontWeight.SemiBold,
            )
        }
    }
}

/* ── Active Alerts Section (using real backend data) ────────────────────────────── */

@Composable
private fun ActiveAlertsSection(
    data: DashboardData,
    onViewAllClick: () -> Unit,
) {
    val colors = LocalVitalisColors.current

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
                color = colors.textPrimary,
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
                modifier = Modifier
                    .fillMaxWidth()
                    .shadow(
                        elevation = 1.dp,
                        shape = RoundedCornerShape(14.dp),
                        ambientColor = VitalisPrimary.copy(alpha = 0.06f),
                        spotColor = VitalisPrimary.copy(alpha = 0.06f)
                    ),
                shape = RoundedCornerShape(14.dp),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                elevation = CardDefaults.cardElevation(defaultElevation = 0.dp),
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
                        color = colors.textMuted,
                    )
                }
            }
        } else {
            // Show up to 3 alerts on dashboard, prioritized by severity
            data.alerts.take(3).forEach { alert ->
                AlertDashboardCard(alert)
            }

            if (data.alerts.size > 3) {
                Spacer(modifier = Modifier.height(6.dp))
                OutlinedButton(
                    onClick = onViewAllClick,
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(10.dp),
                    colors = ButtonDefaults.outlinedButtonColors(contentColor = VitalisPrimary),
                ) {
                    Text(
                        text = "View all ${data.alerts.size} alerts",
                        modifier = Modifier.weight(1f),
                        style = MaterialTheme.typography.labelLarge,
                        fontWeight = FontWeight.SemiBold,
                    )
                    Icon(
                        imageVector = Icons.AutoMirrored.Filled.ArrowForward,
                        contentDescription = "View all alerts",
                        modifier = Modifier.size(18.dp),
                    )
                }
            }
        }
    }
}

@Composable
private fun AlertDashboardCard(alert: DashboardAlert) {
    val colors = LocalVitalisColors.current

    val borderColor = when (alert.severity) {
        "high" -> VitalisDanger
        "medium" -> VitalisWarning
        else -> VitalisSuccess
    }

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .shadow(
                elevation = 1.dp,
                shape = RoundedCornerShape(14.dp),
                ambientColor = VitalisPrimary.copy(alpha = 0.06f),
                spotColor = VitalisPrimary.copy(alpha = 0.06f)
            ),
        shape = RoundedCornerShape(14.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp),
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
                    color = colors.textMuted,
                )
                SeverityBadge(alert.severity)
            }
            Text(
                alert.reason,
                style = MaterialTheme.typography.bodyMedium,
                color = colors.textPrimary,
            )
        }
    }
}

// ─── Alerts Tab ──────────────────────────────────────────

@Composable
fun AlertsScreen(vm: AlertsViewModel) {
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
fun AssistantScreen(
    vm: AssistantViewModel,
    userId: String,
    isListening: Boolean,
    isSpeaking: Boolean,
    voiceDraftText: String,
    onVoiceInput: () -> Unit,
    onSpeakMessage: (String) -> Unit,
    onStopSpeaking: () -> Unit,
    onTextModeActivated: () -> Unit,
) {
    val chatHistory by vm.chatHistory.observeAsState(emptyList())
    val uiState by vm.uiState.observeAsState(AssistantViewModel.UiState.Idle)
    var queryText by remember { mutableStateOf("") }
    val colors = LocalVitalisColors.current
    val listState = rememberLazyListState()
    val latestAssistantIndex = remember(chatHistory) { chatHistory.indexOfLast { !it.isUser } }
    val transientItemCount = if (
        uiState is AssistantViewModel.UiState.Loading ||
        uiState is AssistantViewModel.UiState.Error
    ) {
        1
    } else {
        0
    }
    val hasTypedQuery = queryText.trim().isNotEmpty()
    val isLoading = uiState is AssistantViewModel.UiState.Loading

    LaunchedEffect(chatHistory.size, transientItemCount) {
        val targetIndex = chatHistory.size + transientItemCount - 1
        if (targetIndex >= 0) {
            listState.animateScrollToItem(targetIndex)
        }
    }

    LaunchedEffect(voiceDraftText) {
        val cleanedDraft = voiceDraftText.trim()
        if (cleanedDraft.isNotEmpty() && queryText.isBlank()) {
            queryText = cleanedDraft
        }
    }

    val listeningPulseTransition = rememberInfiniteTransition(label = "assistant_input_pulse")
    val listeningPulseScale by listeningPulseTransition.animateFloat(
        initialValue = 1f,
        targetValue = 1.22f,
        animationSpec = infiniteRepeatable(
            animation = tween(durationMillis = 850, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse,
        ),
        label = "listening_pulse_scale",
    )
    val listeningPulseAlpha by listeningPulseTransition.animateFloat(
        initialValue = 0.28f,
        targetValue = 0.08f,
        animationSpec = infiniteRepeatable(
            animation = tween(durationMillis = 850, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse,
        ),
        label = "listening_pulse_alpha",
    )

    val actionContainerColor = when {
        hasTypedQuery -> VitalisPrimary
        isListening -> colors.accent
        else -> colors.bgInput
    }

    val sendTypedQuery: () -> Unit = {
        val cleaned = queryText.trim()
        if (cleaned.isNotEmpty()) {
            onTextModeActivated()
            vm.sendQuery(userId, cleaned)
            queryText = ""
        }
    }

    Column(
        Modifier
            .fillMaxSize()
            .background(colors.bgApp)
    ) {
        LazyColumn(
            state = listState,
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth(),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            itemsIndexed(chatHistory) { index, msg ->
                val isActiveAssistantBubble = !msg.isUser && index == latestAssistantIndex
                val bubbleColor = if (msg.isUser) {
                    colors.primaryLight
                } else {
                    MaterialTheme.colorScheme.surface
                }
                val bubbleBorder = if (msg.isUser) {
                    VitalisPrimary.copy(alpha = 0.28f)
                } else {
                    colors.borderLight
                }
                val bubbleShape = if (msg.isUser) {
                    RoundedCornerShape(topStart = 16.dp, topEnd = 16.dp, bottomStart = 16.dp, bottomEnd = 6.dp)
                } else {
                    RoundedCornerShape(topStart = 16.dp, topEnd = 16.dp, bottomStart = 6.dp, bottomEnd = 16.dp)
                }

                Row(
                    Modifier.fillMaxWidth(),
                    horizontalArrangement = if (msg.isUser) Arrangement.End else Arrangement.Start
                ) {
                    Surface(
                        modifier = Modifier.fillMaxWidth(0.9f),
                        shape = bubbleShape,
                        color = bubbleColor,
                        border = BorderStroke(1.dp, bubbleBorder),
                        tonalElevation = 0.dp,
                    ) {
                        Column(Modifier.padding(12.dp)) {
                            Text(
                                text = if (msg.isUser) "You" else "Coach",
                                style = MaterialTheme.typography.labelSmall,
                                color = colors.textMuted,
                            )
                            Spacer(Modifier.height(4.dp))
                            Text(
                                text = parseMarkdownBold(msg.text),
                                color = colors.textPrimary,
                                style = MaterialTheme.typography.bodyMedium,
                            )

                            if (msg.citations.isNotEmpty()) {
                                Spacer(Modifier.height(6.dp))
                                for (c in msg.citations) {
                                    Text(
                                        "[${c.sourceFile} p.${c.page}] ${c.snippet}",
                                        style = MaterialTheme.typography.bodySmall,
                                        color = colors.textMuted,
                                    )
                                }
                            }

                            if (!msg.isUser) {
                                Spacer(Modifier.height(6.dp))
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.End,
                                ) {
                                    if (isSpeaking && isActiveAssistantBubble) {
                                        AssistChip(
                                            onClick = onStopSpeaking,
                                            label = {
                                                Text(
                                                    text = "Stop TTS",
                                                    style = MaterialTheme.typography.labelMedium,
                                                    fontWeight = FontWeight.SemiBold,
                                                )
                                            },
                                            leadingIcon = {
                                                Icon(
                                                    imageVector = Icons.Outlined.StopCircle,
                                                    contentDescription = "Stop TTS",
                                                    modifier = Modifier.size(16.dp),
                                                )
                                            },
                                            colors = AssistChipDefaults.assistChipColors(
                                                containerColor = colors.dangerBg,
                                                labelColor = VitalisDanger,
                                                leadingIconContentColor = VitalisDanger,
                                            ),
                                        )
                                    } else {
                                        IconButton(
                                            onClick = { onSpeakMessage(msg.text) },
                                            modifier = Modifier.size(30.dp),
                                        ) {
                                            Icon(
                                                imageVector = Icons.AutoMirrored.Outlined.VolumeUp,
                                                contentDescription = "Read message",
                                                tint = colors.textMuted,
                                                modifier = Modifier.size(18.dp),
                                            )
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            if (uiState is AssistantViewModel.UiState.Loading) {
                item {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.Start,
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        CircularProgressIndicator(
                            modifier = Modifier
                                .padding(8.dp)
                                .size(24.dp),
                            strokeWidth = 2.dp,
                            color = MaterialTheme.colorScheme.primary,
                        )
                        Text(
                            "Processing...",
                            style = MaterialTheme.typography.bodySmall,
                            color = colors.textMuted,
                        )
                    }
                }
            }

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

        Row(
            Modifier
                .fillMaxWidth()
                .background(MaterialTheme.colorScheme.surface)
                .padding(12.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            OutlinedTextField(
                value = queryText,
                onValueChange = {
                    queryText = it
                    onTextModeActivated()
                },
                modifier = Modifier
                    .weight(1f)
                    .onFocusChanged { state ->
                        if (state.isFocused) {
                            onTextModeActivated()
                        }
                    },
                placeholder = {
                    Text(
                        "Ask a health question…",
                        color = colors.textMuted,
                    )
                },
                textStyle = MaterialTheme.typography.bodyMedium.copy(color = colors.textPrimary),
                singleLine = true,
                shape = RoundedCornerShape(999.dp),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = VitalisPrimary,
                    unfocusedBorderColor = colors.borderLight,
                    focusedContainerColor = MaterialTheme.colorScheme.surface,
                    unfocusedContainerColor = MaterialTheme.colorScheme.surface,
                ),
            )

            Box(
                modifier = Modifier.size(52.dp),
                contentAlignment = Alignment.Center,
            ) {
                if (isListening && !hasTypedQuery) {
                    Box(
                        modifier = Modifier
                            .size(52.dp)
                            .graphicsLayer(
                                scaleX = listeningPulseScale,
                                scaleY = listeningPulseScale,
                                alpha = listeningPulseAlpha,
                            )
                            .clip(CircleShape)
                            .background(colors.accent),
                    )
                }

                Surface(
                    shape = CircleShape,
                    color = actionContainerColor,
                    tonalElevation = if (hasTypedQuery) 2.dp else 0.dp,
                    modifier = Modifier
                        .size(44.dp)
                        .border(1.dp, colors.borderLight, CircleShape),
                ) {
                    IconButton(
                        enabled = !isLoading,
                        onClick = {
                            if (hasTypedQuery) {
                                sendTypedQuery()
                            } else {
                                onVoiceInput()
                            }
                        },
                    ) {
                        Crossfade(
                            targetState = hasTypedQuery,
                            animationSpec = tween(durationMillis = 180),
                            label = "assistant_action_icon",
                        ) { showSend ->
                            Icon(
                                imageVector = if (showSend) {
                                    Icons.AutoMirrored.Filled.Send
                                } else {
                                    Icons.Filled.Mic
                                },
                                contentDescription = if (showSend) "Send" else "Voice input",
                                tint = if (showSend) {
                                    Color.White
                                } else {
                                    colors.textSecondary
                                },
                            )
                        }
                    }
                }
            }
        }

        AnimatedVisibility(
            visible = isListening,
            enter = fadeIn(),
            exit = fadeOut(),
        ) {
            ListeningWaveformIndicator()
        }
    }
}

@Composable
private fun ListeningWaveformIndicator() {
    val transition = rememberInfiniteTransition(label = "listening_bars")
    val bar1 by transition.animateFloat(
        initialValue = 0.25f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(durationMillis = 420, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse,
        ),
        label = "bar_1",
    )
    val bar2 by transition.animateFloat(
        initialValue = 0.4f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(durationMillis = 500, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse,
        ),
        label = "bar_2",
    )
    val bar3 by transition.animateFloat(
        initialValue = 0.3f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(durationMillis = 560, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse,
        ),
        label = "bar_3",
    )
    val bar4 by transition.animateFloat(
        initialValue = 0.35f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(durationMillis = 460, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse,
        ),
        label = "bar_4",
    )

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(bottom = 10.dp),
        horizontalArrangement = Arrangement.Center,
        verticalAlignment = Alignment.Bottom,
    ) {
        ListeningWaveBar(bar1)
        Spacer(Modifier.width(4.dp))
        ListeningWaveBar(bar2)
        Spacer(Modifier.width(4.dp))
        ListeningWaveBar(bar3)
        Spacer(Modifier.width(4.dp))
        ListeningWaveBar(bar4)
    }
}

@Composable
private fun ListeningWaveBar(level: Float) {
    Box(
        modifier = Modifier
            .width(4.dp)
            .height((8 + (24 * level)).dp)
            .clip(RoundedCornerShape(999.dp))
            .background(VitalisPrimary.copy(alpha = 0.7f))
    )
}

private fun parseMarkdownBold(text: String): AnnotatedString {
    if (!text.contains("**")) return AnnotatedString(text)

    val boldRegex = Regex("\\*\\*(.+?)\\*\\*")
    return buildAnnotatedString {
        var cursor = 0
        boldRegex.findAll(text).forEach { match ->
            val start = match.range.first
            val endExclusive = match.range.last + 1

            if (start > cursor) {
                append(text.substring(cursor, start))
            }

            withStyle(SpanStyle(fontWeight = FontWeight.Bold)) {
                append(match.groupValues[1])
            }
            cursor = endExclusive
        }

        if (cursor < text.length) {
            append(text.substring(cursor))
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
        sourceFilename = reportName, // Use report_name from backend (already contains source_file_name)
        pageNumber = null
    )
}

// ─── Custom Bottom Navigation (matches sample.html) ─────────────────────────

@Composable
fun VitalisBottomNavBar(
    selectedTab: Int,
    onTabSelected: (Int) -> Unit,
    onVoiceFabClick: () -> Unit
) {
    val colors = LocalVitalisColors.current

    val infiniteTransition = rememberInfiniteTransition(label = "fab_pulse")
    val pulseScale by infiniteTransition.animateFloat(
        initialValue = 0.90f,
        targetValue = 1.12f,
        animationSpec = infiniteRepeatable(
            animation = tween(1200, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "pulse_scale"
    )
    val pulseAlpha by infiniteTransition.animateFloat(
        initialValue = 0.55f,
        targetValue = 0.15f,
        animationSpec = infiniteRepeatable(
            animation = tween(1200, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "pulse_alpha"
    )

    Box(
        modifier = Modifier
            .fillMaxWidth()
            .height(86.dp)
    ) {
        // White background bar
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .height(76.dp)
                .align(Alignment.BottomCenter),
            color = MaterialTheme.colorScheme.surface,
            shadowElevation = 8.dp,
        ) {
            Row(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(horizontal = 8.dp),
                horizontalArrangement = Arrangement.SpaceAround,
                verticalAlignment = Alignment.CenterVertically
            ) {
                // Home (tab 0 = Dashboard)
                NavItem(
                    icon = Icons.Outlined.SpaceDashboard,
                    label = "Home",
                    isSelected = selectedTab == 0,
                    onClick = { onTabSelected(0) }
                )
                // Health (tab 1 = Vitals)
                NavItem(
                    icon = Icons.Outlined.MonitorHeart,
                    label = "Health",
                    isSelected = selectedTab == 1,
                    onClick = { onTabSelected(1) }
                )

                // Spacer for FAB
                Spacer(modifier = Modifier.width(64.dp))

                // Records (tab 2 = Upload)
                NavItem(
                    icon = Icons.Outlined.Description,
                    label = "Records",
                    isSelected = selectedTab == 2,
                    onClick = { onTabSelected(2) }
                )
                // Profile (tab 5)
                NavItem(
                    icon = Icons.Outlined.Person,
                    label = "Profile",
                    isSelected = selectedTab == 5,
                    onClick = { onTabSelected(5) }
                )
            }
        }

        // Center Voice FAB (overlapping the bar)
        Box(
            modifier = Modifier
                .align(Alignment.TopCenter)
                .offset(y = (-4).dp),
            contentAlignment = Alignment.Center
        ) {
            // Pulse ring
            Box(
                modifier = Modifier
                    .size(68.dp)
                    .graphicsLayer(
                        scaleX = pulseScale,
                        scaleY = pulseScale,
                        alpha = pulseAlpha
                    )
                    .clip(CircleShape)
                    .background(VitalisPrimary.copy(alpha = 0.18f))
            )

            // FAB button
            Box(
                modifier = Modifier
                    .size(58.dp)
                    .shadow(
                        elevation = 12.dp,
                        shape = CircleShape,
                        ambientColor = VitalisPrimaryDeeper.copy(alpha = 0.38f),
                        spotColor = VitalisPrimaryDeeper.copy(alpha = 0.38f)
                    )
                    .clip(CircleShape)
                    .background(
                        Brush.linearGradient(
                            colors = listOf(VitalisAccentWarm, VitalisPrimaryDeeper),
                            start = Offset(0f, 0f),
                            end = Offset(Float.POSITIVE_INFINITY, Float.POSITIVE_INFINITY)
                        )
                    )
                    .clickable(
                        interactionSource = remember { MutableInteractionSource() },
                        indication = null,
                        onClick = onVoiceFabClick
                    ),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Outlined.SmartToy,
                    contentDescription = "AI Coach",
                    tint = Color.White,
                    modifier = Modifier.size(26.dp)
                )
            }

            // Label below FAB
            Text(
                text = "Voice",
                style = MaterialTheme.typography.labelSmall.copy(
                    fontSize = 10.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 0.2.sp
                ),
                color = colors.textMuted,
                modifier = Modifier
                    .align(Alignment.BottomCenter)
                    .offset(y = 44.dp)
            )
        }
    }
}

@Composable
private fun NavItem(
    icon: ImageVector,
    label: String,
    isSelected: Boolean,
    onClick: () -> Unit
) {
    val colors = LocalVitalisColors.current
    val color = if (isSelected) VitalisPrimary else colors.textMuted

    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
        modifier = Modifier
            .clickable(
                interactionSource = remember { MutableInteractionSource() },
                indication = null,
                onClick = onClick
            )
            .padding(horizontal = 12.dp, vertical = 6.dp)
    ) {
        Icon(
            imageVector = icon,
            contentDescription = label,
            tint = color,
            modifier = Modifier.size(22.dp)
        )
        Spacer(modifier = Modifier.height(4.dp))
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall.copy(
                fontSize = 10.sp,
                fontWeight = FontWeight.SemiBold,
                letterSpacing = 0.2.sp
            ),
            color = color
        )
    }
}
