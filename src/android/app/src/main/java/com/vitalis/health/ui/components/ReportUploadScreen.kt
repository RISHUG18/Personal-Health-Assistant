package com.vitalis.health.ui.components

import android.net.Uri
import android.widget.Toast
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.CloudUpload
import androidx.compose.material.icons.outlined.Description
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.livedata.observeAsState
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.vitalis.health.ui.ReportUploadViewModel
import com.vitalis.health.ui.theme.*

/**
 * Upload screen replicating the sample.html dropzone design.
 *
 * Flow: pick file → validate type → upload/process → show result or navigate to detail.
 */
@Composable
fun ReportUploadScreen(
    viewModel: ReportUploadViewModel,
    userId: String,
    onViewResult: () -> Unit,
    reports: List<ReportTimelineItem> = emptyList(),
    isReportsLoading: Boolean = false,
    onViewReport: (String) -> Unit = {},
    onDeleteReport: (String) -> Unit = {},
    modifier: Modifier = Modifier,
) {
    val uiState by viewModel.uiState.observeAsState(ReportUploadViewModel.UiState.Idle)
    val colors = LocalVitalisColors.current
    val context = LocalContext.current

    // Track selected file
    var selectedUri by remember { mutableStateOf<Uri?>(null) }
    var selectedFileName by remember { mutableStateOf<String?>(null) }
    var selectedFileBytes by remember { mutableStateOf<ByteArray?>(null) }
    var fileValidationError by remember { mutableStateOf<String?>(null) }

    fun isAllowedFileType(uri: Uri): Boolean {
        val mimeType = context.contentResolver.getType(uri)?.lowercase()
        return mimeType in setOf("application/pdf", "image/jpeg", "image/png")
    }

    // Document picker launcher — accepts PDF and images
    val filePicker = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent()
    ) { uri: Uri? ->
        val selected = uri ?: return@rememberLauncherForActivityResult

        if (!isAllowedFileType(selected)) {
            selectedUri = null
            selectedFileName = null
            selectedFileBytes = null
            fileValidationError = "Error: Invalid file type. Please upload a PDF or an image."
            Toast.makeText(
                context,
                "Error: Invalid file type. Please upload a PDF or an image.",
                Toast.LENGTH_LONG,
            ).show()
            return@rememberLauncherForActivityResult
        }

        fileValidationError = null
        selectedUri = selected

        // Resolve filename from content resolver
        val cursor = context.contentResolver.query(selected, null, null, null, null)
        selectedFileName = cursor?.use { c ->
            val nameIndex = c.getColumnIndex(android.provider.OpenableColumns.DISPLAY_NAME)
            c.moveToFirst()
            if (nameIndex >= 0) c.getString(nameIndex) else "report.pdf"
        } ?: "report.pdf"

        // Read bytes
        selectedFileBytes = context.contentResolver.openInputStream(selected)?.use { stream ->
            stream.readBytes()
        }

        if (selectedFileBytes == null) {
            fileValidationError = "Unable to read the selected file. Please try another file."
            Toast.makeText(
                context,
                "Unable to read the selected file. Please try another file.",
                Toast.LENGTH_LONG,
            ).show()
            selectedUri = null
            selectedFileName = null
            selectedFileBytes = null
        }
    }

    when (uiState) {
        is ReportUploadViewModel.UiState.Uploading ->
            VitalisLoadingScreen(label = "Uploading report…")

        is ReportUploadViewModel.UiState.Processing -> {
            val processingState = uiState as ReportUploadViewModel.UiState.Processing
            val statusLabel = when (processingState.status) {
                "pending" -> "Queued for processing…"
                "ocr_complete" -> "OCR complete, extracting lab results…"
                else -> "Processing report…"
            }
            VitalisLoadingScreen(label = statusLabel)
        }

        is ReportUploadViewModel.UiState.Error -> {
            val msg = (uiState as ReportUploadViewModel.UiState.Error).message
            VitalisErrorScreen(
                message = msg,
                title = "Upload failed",
                onRetry = { viewModel.reset() },
            )
        }

        is ReportUploadViewModel.UiState.Success -> {
            // Show brief success then navigate to detail
            UploadSuccessScreen(
                result = (uiState as ReportUploadViewModel.UiState.Success).result,
                onViewDetails = onViewResult,
                onUploadAnother = {
                    selectedUri = null
                    selectedFileName = null
                    selectedFileBytes = null
                    viewModel.reset()
                },
            )
        }

        is ReportUploadViewModel.UiState.Idle -> {
            Column(
                modifier
                    .fillMaxSize()
                    .background(colors.bgApp)
                    .verticalScroll(rememberScrollState())
                    .padding(20.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp),
            ) {
                // ── Section header ──
                Text(
                    "Upload Report",
                    style = MaterialTheme.typography.headlineSmall,
                    fontWeight = FontWeight.Bold,
                    color = colors.textPrimary,
                )
                Text(
                    "Upload a medical report for AI-powered analysis",
                    style = MaterialTheme.typography.bodyMedium,
                    color = colors.textMuted,
                )

                // ── Dropzone area — matches sample.html .upload-button ──
                Surface(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable { filePicker.launch("*/*") },
                    shape = RoundedCornerShape(6.dp),
                    color = VitalisPrimaryLight,
                    border = BorderStroke(1.5.dp, VitalisPrimaryMuted),
                ) {
                    Column(
                        Modifier.padding(vertical = 28.dp, horizontal = 16.dp),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        Icon(
                            Icons.Outlined.CloudUpload,
                            contentDescription = "Upload",
                            tint = VitalisPrimary,
                            modifier = Modifier.size(32.dp),
                        )
                        Text(
                            "Tap to select a medical record",
                            style = MaterialTheme.typography.bodyMedium,
                            fontWeight = FontWeight.SemiBold,
                            color = VitalisPrimary,
                        )
                        Text(
                            "PDF, PNG, JPG supported",
                            style = MaterialTheme.typography.bodySmall,
                            color = colors.textMuted,
                        )
                    }
                }

                fileValidationError?.let { errorMessage ->
                    Text(
                        text = errorMessage,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.error,
                        modifier = Modifier.padding(horizontal = 2.dp),
                    )
                }

                // ── Selected file indicator ──
                if (selectedFileName != null) {
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(10.dp),
                        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
                    ) {
                        Row(
                            Modifier.padding(14.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(12.dp),
                        ) {
                            Box(
                                Modifier
                                    .size(38.dp)
                                    .clip(RoundedCornerShape(10.dp))
                                    .background(VitalisPrimaryLight),
                                contentAlignment = Alignment.Center,
                            ) {
                                Icon(
                                    Icons.Outlined.Description,
                                    contentDescription = null,
                                    tint = VitalisPrimary,
                                    modifier = Modifier.size(18.dp),
                                )
                            }
                            Column(Modifier.weight(1f)) {
                                Text(
                                    selectedFileName ?: "",
                                    style = MaterialTheme.typography.bodyMedium,
                                    fontWeight = FontWeight.SemiBold,
                                    color = colors.textPrimary,
                                    maxLines = 1,
                                    overflow = TextOverflow.Ellipsis,
                                )
                                selectedFileBytes?.let { bytes ->
                                    Text(
                                        "${bytes.size / 1024} KB",
                                        style = MaterialTheme.typography.bodySmall,
                                        color = colors.textMuted,
                                    )
                                }
                            }
                            TextButton(onClick = {
                                selectedUri = null
                                selectedFileName = null
                                selectedFileBytes = null
                                fileValidationError = null
                            }) {
                                Text("Remove", color = VitalisDanger)
                            }
                        }
                    }
                }

                // ── Upload button ──
                Button(
                    onClick = {
                        val bytes = selectedFileBytes
                        val name = selectedFileName
                        if (bytes != null && name != null) {
                            viewModel.uploadAndProcess(userId, name, bytes)
                        }
                    },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(52.dp),
                    enabled = selectedFileBytes != null,
                    shape = RoundedCornerShape(10.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = MaterialTheme.colorScheme.primary,
                        contentColor = MaterialTheme.colorScheme.onPrimary,
                        disabledContainerColor = MaterialTheme.colorScheme.surfaceVariant,
                        disabledContentColor = MaterialTheme.colorScheme.onSurfaceVariant,
                    ),
                ) {
                    Text(
                        "Process Report",
                        fontWeight = FontWeight.SemiBold,
                        fontSize = 15.sp,
                    )
                }

                Spacer(Modifier.height(8.dp))

                ReportTimeline(
                    reports = reports,
                    isLoading = isReportsLoading,
                    onViewReport = onViewReport,
                    onDeleteReport = onDeleteReport,
                )

                if (reports.isEmpty() && !isReportsLoading) {
                    Surface(
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(8.dp),
                        color = MaterialTheme.colorScheme.surfaceVariant,
                    ) {
                        Text(
                            text = "No reports yet. Process your first report to see it here.",
                            style = MaterialTheme.typography.bodySmall,
                            color = colors.textSecondary,
                            modifier = Modifier.padding(12.dp),
                        )
                    }
                }

                Spacer(Modifier.height(4.dp))
            }
        }
    }
}

// ─── Success screen after upload completes ───────────────────────────────────

@Composable
private fun UploadSuccessScreen(
    result: com.vitalis.health.data.model.ProcessReportResponse,
    onViewDetails: () -> Unit,
    onUploadAnother: () -> Unit,
) {
    val colors = LocalVitalisColors.current

    Column(
        Modifier
            .fillMaxSize()
            .background(colors.bgApp)
            .verticalScroll(rememberScrollState())
            .padding(20.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Spacer(Modifier.height(32.dp))

        // Success icon
        Surface(
            modifier = Modifier.size(64.dp),
            shape = RoundedCornerShape(16.dp),
            color = VitalisSuccessBg,
        ) {
            Box(contentAlignment = Alignment.Center) {
                Text("✓", fontSize = 28.sp, color = VitalisSuccess, fontWeight = FontWeight.Bold)
            }
        }

        Text(
            "Report Processed Successfully",
            style = MaterialTheme.typography.titleLarge,
            fontWeight = FontWeight.Bold,
            color = colors.textPrimary,
            textAlign = TextAlign.Center,
        )

        // Quick stats card
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(14.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
            elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
        ) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                StatRow("Report ID", result.reportId.take(8) + "…")
                if (result.ocrConfidence > 0) {
                    StatRow("OCR Confidence", "${(result.ocrConfidence * 100).toInt()}%")
                }
                if (result.ocrTextPreview.isNotEmpty()) {
                    StatRow("Status", result.ocrTextPreview)
                }
                // Regex extraction stats (may not be present in async response)
                if (result.regexExtraction.inserted > 0) {
                    StatRow(
                        "Regex Extraction",
                        "${result.regexExtraction.inserted} tests inserted"
                    )
                }
                // AI extraction stats (may not be present in async response)
                result.geminiExtraction?.let { gem ->
                    StatRow(
                        "AI Extraction",
                        "${gem.testsInserted} inserted, ${gem.testsSkipped} skipped"
                    )
                }
                result.geminiError?.let { err ->
                    StatRow("AI Extraction Error", err)
                }
            }
        }

        // Action buttons
        Button(
            onClick = onViewDetails,
            modifier = Modifier
                .fillMaxWidth()
                .height(48.dp),
            shape = RoundedCornerShape(10.dp),
            colors = ButtonDefaults.buttonColors(
                containerColor = MaterialTheme.colorScheme.primary,
                contentColor = MaterialTheme.colorScheme.onPrimary,
            ),
        ) {
            Text("View Report", fontWeight = FontWeight.SemiBold)
        }

        OutlinedButton(
            onClick = onUploadAnother,
            modifier = Modifier
                .fillMaxWidth()
                .height(48.dp),
            shape = RoundedCornerShape(10.dp),
            border = BorderStroke(1.dp, MaterialTheme.colorScheme.outline),
        ) {
            Text("Upload Another", color = MaterialTheme.colorScheme.onSurface)
        }
    }
}

@Composable
private fun StatRow(label: String, value: String) {
    val colors = LocalVitalisColors.current

    Row(
        Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
    ) {
        Text(
            label,
            style = MaterialTheme.typography.bodySmall,
            color = colors.textMuted,
        )
        Text(
            value,
            style = MaterialTheme.typography.bodySmall,
            fontWeight = FontWeight.SemiBold,
            color = colors.textPrimary,
        )
    }
}
