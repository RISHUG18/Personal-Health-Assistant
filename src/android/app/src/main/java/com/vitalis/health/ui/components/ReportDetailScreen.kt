package com.vitalis.health.ui.components

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.expandVertically
import androidx.compose.animation.shrinkVertically
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.ArrowBack
import androidx.compose.material.icons.outlined.Description
import androidx.compose.material.icons.outlined.ExpandLess
import androidx.compose.material.icons.outlined.ExpandMore
import androidx.compose.material.icons.outlined.Science
import androidx.compose.material.icons.outlined.SmartToy
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.vitalis.health.data.model.GeminiExtractionLog
import com.vitalis.health.data.model.ProcessReportResponse
import com.vitalis.health.data.model.RegexExtractionResult
import com.vitalis.health.ui.theme.*

/**
 * Report detail screen showing the full results of a processed report:
 * - Report metadata (report ID, storage path, public URL)
 * - OCR text with confidence score (collapsible)
 * - Regex extraction results
 * - Gemini extraction results (if available)
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ReportDetailScreen(
    result: ProcessReportResponse,
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier
            .fillMaxSize()
            .background(VitalisBgApp)
    ) {
        // ── Top bar ──
        TopAppBar(
            title = { Text("Report Details", fontWeight = FontWeight.Bold) },
            navigationIcon = {
                IconButton(onClick = onBack) {
                    Icon(Icons.Outlined.ArrowBack, contentDescription = "Back")
                }
            },
            colors = TopAppBarDefaults.topAppBarColors(
                containerColor = Color.White,
            ),
        )

        Column(
            Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            // ── Report Metadata Card ──
            SectionCard(title = "Report Info") {
                MetadataRow("Report ID", result.reportId)
                MetadataRow("Storage Path", result.storagePath)
                MetadataRow("Public URL", result.publicUrl)
            }

            // ── OCR Results Card ──
            OcrResultCard(
                confidence = result.ocrConfidence,
                textPreview = result.ocrTextPreview,
            )

            // ── Regex Extraction Card ──
            RegexExtractionCard(result.regexExtraction)

            // ── Gemini Extraction Card ──
            if (result.geminiExtraction != null || result.geminiError != null) {
                GeminiExtractionCard(
                    extraction = result.geminiExtraction,
                    error = result.geminiError,
                )
            }

            Spacer(Modifier.height(16.dp))
        }
    }
}

// ─── OCR Results with collapsible raw text ──────────────────────────────────

@Composable
private fun OcrResultCard(confidence: Double, textPreview: String) {
    var expanded by remember { mutableStateOf(false) }
    val confidencePercent = (confidence * 100).toInt()
    val confidenceColor = when {
        confidencePercent >= 80 -> VitalisSuccess
        confidencePercent >= 50 -> VitalisWarning
        else -> VitalisDanger
    }

    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(14.dp),
        colors = CardDefaults.cardColors(containerColor = Color.White),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
    ) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Row(
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Icon(
                        Icons.Outlined.Description,
                        contentDescription = null,
                        tint = VitalisPrimary,
                        modifier = Modifier.size(20.dp),
                    )
                    Text(
                        "OCR Results",
                        style = MaterialTheme.typography.titleSmall,
                        fontWeight = FontWeight.Bold,
                        color = VitalisTextPrimary,
                    )
                }
                // Confidence badge
                Surface(
                    shape = RoundedCornerShape(4.dp),
                    color = confidenceColor.copy(alpha = 0.12f),
                ) {
                    Text(
                        "$confidencePercent% confidence",
                        modifier = Modifier.padding(horizontal = 10.dp, vertical = 3.dp),
                        style = MaterialTheme.typography.labelSmall,
                        fontWeight = FontWeight.Bold,
                        color = confidenceColor,
                    )
                }
            }

            // Confidence progress bar
            @Suppress("DEPRECATION")
            LinearProgressIndicator(
                progress = confidence.toFloat().coerceIn(0f, 1f),
                modifier = Modifier
                    .fillMaxWidth()
                    .height(6.dp)
                    .clip(RoundedCornerShape(3.dp)),
                color = confidenceColor,
                trackColor = confidenceColor.copy(alpha = 0.12f),
            )

            // Collapsible OCR text
            Row(
                Modifier
                    .fillMaxWidth()
                    .clickable { expanded = !expanded },
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    "Raw OCR Text",
                    style = MaterialTheme.typography.labelMedium,
                    color = VitalisTextMuted,
                )
                Icon(
                    if (expanded) Icons.Outlined.ExpandLess else Icons.Outlined.ExpandMore,
                    contentDescription = if (expanded) "Collapse" else "Expand",
                    tint = VitalisTextMuted,
                    modifier = Modifier.size(20.dp),
                )
            }

            AnimatedVisibility(
                visible = expanded,
                enter = expandVertically(),
                exit = shrinkVertically(),
            ) {
                Surface(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(6.dp),
                    color = VitalisBgApp,
                ) {
                    Text(
                        text = textPreview.ifEmpty { "(no OCR text available)" },
                        modifier = Modifier.padding(12.dp),
                        style = MaterialTheme.typography.bodySmall.copy(
                            fontFamily = FontFamily.Monospace,
                            lineHeight = 18.sp,
                        ),
                        color = VitalisTextSecondary,
                    )
                }
            }
        }
    }
}

// ─── Regex Extraction Card ──────────────────────────────────────────────────

@Composable
private fun RegexExtractionCard(extraction: RegexExtractionResult) {
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
                        color = VitalisPrimary,
                        topLeft = Offset.Zero,
                        size = Size(3.dp.toPx(), size.height),
                    )
                }
                .padding(start = 6.dp)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Row(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Icon(
                    Icons.Outlined.Science,
                    contentDescription = null,
                    tint = VitalisPrimary,
                    modifier = Modifier.size(20.dp),
                )
                Text(
                    "Standard Extraction (Regex)",
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.Bold,
                    color = VitalisTextPrimary,
                )
            }

            MetadataRow("Tests Inserted", "${extraction.inserted}")

            extraction.error?.let { err ->
                Surface(
                    shape = RoundedCornerShape(6.dp),
                    color = VitalisDanger.copy(alpha = 0.08f),
                ) {
                    Text(
                        "Error: $err",
                        modifier = Modifier.padding(8.dp),
                        style = MaterialTheme.typography.bodySmall,
                        color = VitalisDanger,
                    )
                }
            }
        }
    }
}

// ─── Gemini Extraction Card ─────────────────────────────────────────────────

@Composable
private fun GeminiExtractionCard(
    extraction: GeminiExtractionLog?,
    error: String?,
) {
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
                        color = Color(0xFF2D8BC9),
                        topLeft = Offset.Zero,
                        size = Size(3.dp.toPx(), size.height),
                    )
                }
                .padding(start = 6.dp)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Row(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Icon(
                    Icons.Outlined.SmartToy,
                    contentDescription = null,
                    tint = Color(0xFF2D8BC9),
                    modifier = Modifier.size(20.dp),
                )
                Text(
                    "AI Extraction (Gemini)",
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.Bold,
                    color = VitalisTextPrimary,
                )
            }

            if (extraction != null) {
                MetadataRow("Total Tests Found", "${extraction.totalTestsFound}")
                MetadataRow("Tests Inserted", "${extraction.testsInserted}")
                MetadataRow("Tests Skipped", "${extraction.testsSkipped}")

                if (extraction.skippedDetails.isNotEmpty()) {
                    var showSkipped by remember { mutableStateOf(false) }
                    Text(
                        "${if (showSkipped) "Hide" else "Show"} skipped details (${extraction.skippedDetails.size})",
                        modifier = Modifier.clickable { showSkipped = !showSkipped },
                        style = MaterialTheme.typography.labelSmall,
                        color = VitalisPrimary,
                    )
                    AnimatedVisibility(
                        visible = showSkipped,
                        enter = expandVertically(),
                        exit = shrinkVertically(),
                    ) {
                        Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                            extraction.skippedDetails.forEach { detail ->
                                Text(
                                    "• $detail",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = VitalisTextMuted,
                                )
                            }
                        }
                    }
                }

                if (extraction.warnings.isNotEmpty()) {
                    extraction.warnings.forEach { warning ->
                        Surface(
                            shape = RoundedCornerShape(6.dp),
                            color = VitalisWarning.copy(alpha = 0.08f),
                        ) {
                            Text(
                                "⚠ $warning",
                                modifier = Modifier.padding(8.dp),
                                style = MaterialTheme.typography.bodySmall,
                                color = VitalisWarning,
                            )
                        }
                    }
                }

                if (extraction.errors.isNotEmpty()) {
                    extraction.errors.forEach { err ->
                        Surface(
                            shape = RoundedCornerShape(6.dp),
                            color = VitalisDanger.copy(alpha = 0.08f),
                        ) {
                            Text(
                                "Error: $err",
                                modifier = Modifier.padding(8.dp),
                                style = MaterialTheme.typography.bodySmall,
                                color = VitalisDanger,
                            )
                        }
                    }
                }
            }

            error?.let { err ->
                Surface(
                    shape = RoundedCornerShape(6.dp),
                    color = VitalisDanger.copy(alpha = 0.08f),
                ) {
                    Text(
                        "Gemini Error: $err",
                        modifier = Modifier.padding(8.dp),
                        style = MaterialTheme.typography.bodySmall,
                        color = VitalisDanger,
                    )
                }
            }
        }
    }
}

// ─── Shared helpers ─────────────────────────────────────────────────────────

@Composable
private fun SectionCard(
    title: String,
    content: @Composable ColumnScope.() -> Unit,
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(14.dp),
        colors = CardDefaults.cardColors(containerColor = Color.White),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
    ) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(
                title,
                style = MaterialTheme.typography.titleSmall,
                fontWeight = FontWeight.Bold,
                color = VitalisTextPrimary,
            )
            content()
        }
    }
}

@Composable
private fun MetadataRow(label: String, value: String) {
    Row(
        Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
    ) {
        Text(
            label,
            style = MaterialTheme.typography.bodySmall,
            color = VitalisTextMuted,
        )
        Text(
            value,
            style = MaterialTheme.typography.bodySmall,
            fontWeight = FontWeight.Medium,
            color = VitalisTextPrimary,
        )
    }
}
