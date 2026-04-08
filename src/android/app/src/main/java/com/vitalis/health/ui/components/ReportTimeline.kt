package com.vitalis.health.ui.components

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.expandVertically
import androidx.compose.animation.shrinkVertically
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Bloodtype
import androidx.compose.material.icons.outlined.FavoriteBorder
import androidx.compose.material.icons.outlined.Science
import androidx.compose.material.icons.outlined.TaskAlt
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.vitalis.health.ui.theme.*

// ─── Report type enum for icon / colour mapping ─────────────────────────────

enum class ReportType(
    val label: String,
    val icon: ImageVector,
    val iconTint: Color,
    val iconBg: Color,
) {
    BLOOD(
        label = "Blood Work",
        icon = Icons.Outlined.Bloodtype,
        iconTint = Color(0xFFD94F4F),
        iconBg = Color(0xFFFDF0F0),
    ),
    HEART(
        label = "Cardiac",
        icon = Icons.Outlined.FavoriteBorder,
        iconTint = Color(0xFFC0392B),
        iconBg = Color(0xFFFDE8E8),
    ),
    LAB(
        label = "Lab Panel",
        icon = Icons.Outlined.Science,
        iconTint = Color(0xFF2D8BC9),
        iconBg = Color(0xFFEDF5FC),
    ),
    EXAM(
        label = "Examination",
        icon = Icons.Outlined.TaskAlt,
        iconTint = VitalisPrimary,
        iconBg = VitalisPrimaryLight,
    ),
}

enum class ExtractionMethod { AI, STANDARD }

// ─── Placeholder data model for timeline items ──────────────────────────────

data class ReportTimelineItem(
    val reportId: String,
    val reportName: String,
    val uploadDate: String,
    val reportType: ReportType,
    val riskLabel: String,
    val riskLevel: String,          // "normal" | "mild" | "high"
    val highlight: String,
    val extractionMethod: ExtractionMethod,
    val sourceFilename: String?,
    val pageNumber: Int?,
)

val PLACEHOLDER_REPORTS = listOf(
    ReportTimelineItem(
        reportId = "rep_001",
        reportName = "Hematology Panel",
        uploadDate = "Feb 08, 2026",
        reportType = ReportType.BLOOD,
        riskLabel = "Review",
        riskLevel = "mild",
        highlight = "Vitamin D insufficiency detected — supplement recommended",
        extractionMethod = ExtractionMethod.AI,
        sourceFilename = "blood_report_feb08.pdf",
        pageNumber = 3,
    ),
    ReportTimelineItem(
        reportId = "rep_002",
        reportName = "ECG Report",
        uploadDate = "Jan 25, 2026",
        reportType = ReportType.HEART,
        riskLabel = "Normal",
        riskLevel = "normal",
        highlight = "Sinus rhythm normal. No arrhythmia detected.",
        extractionMethod = ExtractionMethod.STANDARD,
        sourceFilename = "ecg_jan25.pdf",
        pageNumber = 1,
    ),
    ReportTimelineItem(
        reportId = "rep_003",
        reportName = "Metabolic Panel",
        uploadDate = "Jan 10, 2026",
        reportType = ReportType.LAB,
        riskLabel = "Normal",
        riskLevel = "normal",
        highlight = "Lipid profile within optimal range",
        extractionMethod = ExtractionMethod.AI,
        sourceFilename = "metabolic_jan10.pdf",
        pageNumber = 2,
    ),
    ReportTimelineItem(
        reportId = "rep_004",
        reportName = "Physical Examination",
        uploadDate = "Dec 15, 2025",
        reportType = ReportType.EXAM,
        riskLabel = "Cleared",
        riskLevel = "normal",
        highlight = "General health status: Excellent",
        extractionMethod = ExtractionMethod.STANDARD,
        sourceFilename = "physical_dec15.pdf",
        pageNumber = 1,
    ),
)

// ─── Composables ─────────────────────────────────────────────────────────────

@Composable
fun ReportTimeline(
    reports: List<ReportTimelineItem> = PLACEHOLDER_REPORTS,
    onViewReport: (String) -> Unit = {},
    modifier: Modifier = Modifier,
) {
    val colors = LocalVitalisColors.current

    Column(
        modifier
            .fillMaxWidth()
            .background(colors.bgApp)
    ) {
        // Section header — matches .section-header
        Text(
            "Report History",
            style = MaterialTheme.typography.labelMedium,
            fontWeight = FontWeight.Bold,
            color = colors.textMuted,
            letterSpacing = 0.8.sp,
            modifier = Modifier.padding(bottom = 12.dp),
        )

        reports.forEach { report ->
            TimelineItemCard(
                item = report,
                onViewReport = onViewReport,
            )
            Spacer(Modifier.height(10.dp))
        }
    }
}

@Composable
private fun TimelineItemCard(
    item: ReportTimelineItem,
    onViewReport: (String) -> Unit,
) {
    val colors = LocalVitalisColors.current
    var expanded by remember { mutableStateOf(false) }

    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .clickable { expanded = !expanded },
        shape = MaterialTheme.shapes.medium,     // 14 dp — matches --radius-md
        color = MaterialTheme.colorScheme.surface,
        border = BorderStroke(1.dp, VitalisBorder),
        shadowElevation = 1.dp,
    ) {
        Column(Modifier.padding(16.dp)) {
            // ── Header row: icon | info | badge ──────────────────────────
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(14.dp),
            ) {
                // Type icon — 38 dp box matching .timeline-icon
                Box(
                    Modifier
                        .size(38.dp)
                        .clip(RoundedCornerShape(10.dp))
                        .background(item.reportType.iconBg),
                    contentAlignment = Alignment.Center,
                ) {
                    Icon(
                        item.reportType.icon,
                        contentDescription = item.reportType.label,
                        tint = item.reportType.iconTint,
                        modifier = Modifier.size(18.dp),
                    )
                }

                // Title + date
                Column(Modifier.weight(1f)) {
                    Text(
                        item.reportName,
                        style = MaterialTheme.typography.bodyMedium,
                        fontWeight = FontWeight.Bold,
                        color = colors.textPrimary,
                    )
                    Text(
                        item.uploadDate,
                        style = MaterialTheme.typography.bodySmall,
                        color = colors.textMuted,
                    )
                }

                // Risk badge
                RiskBadge(item.riskLabel, item.riskLevel)
            }

            Spacer(Modifier.height(10.dp))

            // ── Extraction method chip ───────────────────────────────────
            ExtractionChip(item.extractionMethod)

            Spacer(Modifier.height(10.dp))

            // ── Highlight — matches .timeline-highlight ──────────────────
            Surface(
                shape = RoundedCornerShape(topStart = 0.dp, bottomStart = 0.dp, topEnd = 10.dp, bottomEnd = 10.dp),
                color = colors.bgApp,
                modifier = Modifier
                    .fillMaxWidth()
                    .drawLeftBorder(VitalisBorder, 2.dp),
            ) {
                Text(
                    item.highlight,
                    style = MaterialTheme.typography.bodySmall,
                    color = colors.textSecondary,
                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 8.dp),
                    lineHeight = 18.sp,
                )
            }

            // ── Expandable citation metadata ─────────────────────────────
            AnimatedVisibility(
                visible = expanded,
                enter = expandVertically(),
                exit = shrinkVertically(),
            ) {
                Column(
                    modifier = Modifier.padding(top = 10.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    item.sourceFilename?.let { fname ->
                        Text(
                            "File: $fname",
                            style = MaterialTheme.typography.bodySmall,
                            color = colors.textSecondary,
                        )
                    }
                    item.pageNumber?.let { pg ->
                        Text(
                            "Page: $pg",
                            style = MaterialTheme.typography.bodySmall,
                            color = colors.textSecondary,
                        )
                    }

                    TextButton(
                        onClick = { onViewReport(item.reportId) },
                        contentPadding = PaddingValues(horizontal = 0.dp),
                    ) {
                        Text(
                            text = "View Report",
                            style = MaterialTheme.typography.labelLarge,
                            fontWeight = FontWeight.SemiBold,
                        )
                    }
                }
            }
        }
    }
}

// ─── Small helper composables ────────────────────────────────────────────────

@Composable
private fun RiskBadge(label: String, level: String) {
    val colors = LocalVitalisColors.current

    val (bg, fg) = when (level) {
        "mild" -> colors.warningBg to VitalisWarning
        "high" -> colors.dangerBg to VitalisDanger
        else   -> colors.successBg to VitalisSuccess
    }
    Surface(shape = RoundedCornerShape(4.dp), color = bg) {
        Text(
            label.uppercase(),
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 3.dp),
            style = MaterialTheme.typography.labelSmall,
            fontWeight = FontWeight.Bold,
            color = fg,
            letterSpacing = 0.5.sp,
        )
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun ExtractionChip(method: ExtractionMethod) {
    val colors = LocalVitalisColors.current

    val (label, containerColor, labelColor) = when (method) {
        ExtractionMethod.AI -> Triple(
            "AI Extraction",
            colors.primaryLight,
            VitalisPrimary,
        )
        ExtractionMethod.STANDARD -> Triple(
            "Standard Extraction",
            colors.primaryLight,
            VitalisPrimary,
        )
    }
    AssistChip(
        onClick = {},
        label = {
            Text(
                label,
                style = MaterialTheme.typography.labelSmall,
                fontWeight = FontWeight.SemiBold,
            )
        },
        colors = AssistChipDefaults.assistChipColors(
            containerColor = containerColor,
            labelColor = labelColor,
        ),
        border = null,
        modifier = Modifier.height(28.dp),
    )
}

// ─── Modifier extension: left border (matches .timeline-highlight CSS) ───────

private fun Modifier.drawLeftBorder(color: Color, width: Dp) =
    this.drawBehind {
        drawRect(
            color = color,
            topLeft = Offset.Zero,
            size = Size(width.toPx(), size.height),
        )
    }
