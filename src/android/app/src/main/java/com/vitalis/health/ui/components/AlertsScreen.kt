package com.vitalis.health.ui.components

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.expandVertically
import androidx.compose.animation.shrinkVertically
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
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.KeyboardArrowDown
import androidx.compose.material.icons.filled.KeyboardArrowUp
import androidx.compose.material.icons.outlined.Description
import androidx.compose.material.icons.outlined.ErrorOutline
import androidx.compose.material.icons.outlined.Info
import androidx.compose.material.icons.outlined.Notifications
import androidx.compose.material.icons.outlined.Warning
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.vitalis.health.data.model.Alert
import com.vitalis.health.data.model.AlertEvidence
import com.vitalis.health.ui.AlertsViewModel
import com.vitalis.health.ui.theme.VitalisBgApp
import com.vitalis.health.ui.theme.VitalisBgInput
import com.vitalis.health.ui.theme.VitalisBorderLight
import com.vitalis.health.ui.theme.VitalisDanger
import com.vitalis.health.ui.theme.VitalisDangerBg
import com.vitalis.health.ui.theme.VitalisPrimary
import com.vitalis.health.ui.theme.VitalisPrimaryLight
import com.vitalis.health.ui.theme.VitalisTextMuted
import com.vitalis.health.ui.theme.VitalisTextPrimary
import com.vitalis.health.ui.theme.VitalisTextSecondary
import com.vitalis.health.ui.theme.VitalisWarning
import com.vitalis.health.ui.theme.VitalisWarningBg
import com.vitalis.health.ui.theme.SectionHeaderStyle
import java.time.ZonedDateTime
import java.time.format.DateTimeFormatter
import java.time.format.DateTimeParseException

/**
 * Alerts screen displaying a list of health alerts sorted by severity.
 *
 * Features:
 * - Severity-colored left border for each alert (high/medium/low)
 * - Expandable evidence section showing source data
 * - Loading and error state handling
 * - Empty state when no alerts exist
 *
 * @param viewModel The [AlertsViewModel] that provides alert data.
 * @param modifier Optional modifier for the composable.
 */
@Composable
fun AlertsScreen(
    viewModel: AlertsViewModel,
    modifier: Modifier = Modifier
) {
    val uiState by viewModel.alertsState.collectAsState()

    Box(
        modifier = modifier
            .fillMaxSize()
            .background(VitalisBgApp)
    ) {
        when (val state = uiState) {
            is AlertsViewModel.UiState.Loading -> {
                VitalisLoadingScreen(label = "Loading alerts…")
            }
            is AlertsViewModel.UiState.Error -> {
                VitalisErrorScreen(
                    message = state.message,
                    title = "Failed to load alerts",
                    onRetry = { viewModel.retry() }
                )
            }
            is AlertsViewModel.UiState.Success -> {
                if (state.alerts.isEmpty()) {
                    VitalisEmptyScreen(
                        message = "No active alerts",
                        subtitle = "You're all caught up! Check back later.",
                        icon = Icons.Outlined.Notifications
                    )
                } else {
                    AlertsList(alerts = state.alerts)
                }
            }
        }
    }
}

@Composable
private fun AlertsList(
    alerts: List<Alert>,
    modifier: Modifier = Modifier
) {
    LazyColumn(
        modifier = modifier
            .fillMaxSize()
            .padding(horizontal = 16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        item {
            Spacer(modifier = Modifier.height(16.dp))

            // Header
            Text(
                text = "Health Alerts",
                style = MaterialTheme.typography.headlineSmall,
                fontWeight = FontWeight.Bold,
                color = VitalisTextPrimary
            )

            Spacer(modifier = Modifier.height(4.dp))

            Text(
                text = "${alerts.size} active alert${if (alerts.size != 1) "s" else ""}",
                style = MaterialTheme.typography.bodySmall,
                color = VitalisTextMuted
            )

            Spacer(modifier = Modifier.height(16.dp))
        }

        items(alerts, key = { it.id }) { alert ->
            AlertCard(alert = alert)
        }

        item {
            Spacer(modifier = Modifier.height(16.dp))
        }
    }
}

@Composable
private fun AlertCard(
    alert: Alert,
    modifier: Modifier = Modifier
) {
    var expanded by remember { mutableStateOf(false) }
    val hasEvidence = alert.evidence.isNotEmpty()

    val severityColor = when (alert.severity.lowercase()) {
        "high" -> VitalisDanger
        "medium" -> VitalisWarning
        "low" -> VitalisPrimary
        else -> VitalisTextMuted
    }

    val severityBgColor = when (alert.severity.lowercase()) {
        "high" -> VitalisDangerBg
        "medium" -> VitalisWarningBg
        "low" -> VitalisPrimaryLight
        else -> VitalisBgInput
    }

    val severityIcon = when (alert.severity.lowercase()) {
        "high" -> Icons.Outlined.ErrorOutline
        "medium" -> Icons.Outlined.Warning
        else -> Icons.Outlined.Info
    }

    Card(
        modifier = modifier
            .fillMaxWidth()
            .drawLeftBorder(severityColor, 3.dp.value)
            .then(
                if (hasEvidence) {
                    Modifier.clickable { expanded = !expanded }
                } else {
                    Modifier
                }
            ),
        shape = RoundedCornerShape(10.dp),
        colors = CardDefaults.cardColors(
            containerColor = severityBgColor
        ),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)
        ) {
            // Header row with severity icon and badge
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier.weight(1f)
                ) {
                    // Severity icon
                    Box(
                        modifier = Modifier
                            .size(36.dp)
                            .clip(RoundedCornerShape(8.dp))
                            .background(severityColor.copy(alpha = 0.1f)),
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(
                            imageVector = severityIcon,
                            contentDescription = null,
                            tint = severityColor,
                            modifier = Modifier.size(20.dp)
                        )
                    }

                    Spacer(modifier = Modifier.width(12.dp))

                    // Alert title
                    Text(
                        text = alert.title,
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.SemiBold,
                        color = MaterialTheme.colorScheme.onSurface,
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis,
                        modifier = Modifier.weight(1f)
                    )
                }

                // Severity badge
                SeverityBadge(severity = alert.severity, color = severityColor)
            }

            Spacer(modifier = Modifier.height(12.dp))

            // Alert message/reason
            Text(
                text = alert.message,
                style = MaterialTheme.typography.bodyMedium,
                color = VitalisTextSecondary,
                maxLines = if (expanded) Int.MAX_VALUE else 3,
                overflow = TextOverflow.Ellipsis
            )

            Spacer(modifier = Modifier.height(8.dp))

            // Timestamp
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = formatTimestamp(alert.createdAt),
                    style = MaterialTheme.typography.bodySmall,
                    color = VitalisTextMuted
                )

                // Expand/collapse indicator for evidence
                if (hasEvidence) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        modifier = Modifier
                            .clip(RoundedCornerShape(4.dp))
                            .background(VitalisBgInput)
                            .padding(horizontal = 8.dp, vertical = 4.dp)
                    ) {
                        Text(
                            text = if (expanded) "Hide evidence" else "View evidence",
                            style = MaterialTheme.typography.labelSmall,
                            color = VitalisTextSecondary
                        )
                        Spacer(modifier = Modifier.width(4.dp))
                        Icon(
                            imageVector = if (expanded) {
                                Icons.Filled.KeyboardArrowUp
                            } else {
                                Icons.Filled.KeyboardArrowDown
                            },
                            contentDescription = null,
                            tint = VitalisTextSecondary,
                            modifier = Modifier.size(16.dp)
                        )
                    }
                }
            }

            // Expandable evidence section
            AnimatedVisibility(
                visible = expanded && hasEvidence,
                enter = expandVertically(),
                exit = shrinkVertically()
            ) {
                Column {
                    Spacer(modifier = Modifier.height(12.dp))
                    EvidenceSection(evidence = alert.evidence)
                }
            }
        }
    }
}

@Composable
private fun SeverityBadge(
    severity: String,
    color: Color,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(4.dp),
        color = color.copy(alpha = 0.15f)
    ) {
        Text(
            text = severity.replaceFirstChar { it.uppercase() },
            style = MaterialTheme.typography.labelSmall,
            fontWeight = FontWeight.SemiBold,
            color = color,
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
        )
    }
}

@Composable
private fun EvidenceSection(
    evidence: List<AlertEvidence>,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(8.dp),
        color = VitalisBgInput
    ) {
        Column(
            modifier = Modifier.padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Text(
                text = "Evidence",
                style = MaterialTheme.typography.labelMedium,
                fontWeight = FontWeight.SemiBold,
                color = MaterialTheme.colorScheme.onSurface
            )

            evidence.forEach { item ->
                EvidenceItem(evidence = item)
            }
        }
    }
}

@Composable
private fun EvidenceItem(
    evidence: AlertEvidence,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier.fillMaxWidth(),
        verticalAlignment = Alignment.Top
    ) {
        Icon(
            imageVector = Icons.Outlined.Description,
            contentDescription = null,
            tint = VitalisTextMuted,
            modifier = Modifier.size(16.dp)
        )

        Spacer(modifier = Modifier.width(8.dp))

        Column(modifier = Modifier.weight(1f)) {
            // Show report ID if available
            evidence.reportId?.let { reportId ->
                Text(
                    text = "Report: ${reportId.take(8)}…",
                    style = MaterialTheme.typography.bodySmall,
                    color = VitalisTextSecondary
                )
            }

            // Show lab result ID if available
            evidence.labResultId?.let { labId ->
                Text(
                    text = "Lab Result: ${labId.take(8)}…",
                    style = MaterialTheme.typography.bodySmall,
                    color = VitalisTextSecondary
                )
            }

            // Show OCR text snippet if available
            evidence.ocrTextSnippet?.let { snippet ->
                Spacer(modifier = Modifier.height(4.dp))
                Surface(
                    shape = RoundedCornerShape(4.dp),
                    color = MaterialTheme.colorScheme.surface
                ) {
                    Text(
                        text = "\"$snippet\"",
                        style = MaterialTheme.typography.bodySmall,
                        color = VitalisTextMuted,
                        modifier = Modifier.padding(8.dp),
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis
                    )
                }
            }
        }
    }
}

/**
 * Modifier to draw a colored left border on a composable.
 */
private fun Modifier.drawLeftBorder(color: Color, width: Float): Modifier = this.drawBehind {
    drawLine(
        color = color,
        start = Offset(0f, 0f),
        end = Offset(0f, size.height),
        strokeWidth = width * density
    )
}

/**
 * Format ISO timestamp to a human-readable format.
 */
private fun formatTimestamp(isoTimestamp: String): String {
    return try {
        val zonedDateTime = ZonedDateTime.parse(isoTimestamp)
        val formatter = DateTimeFormatter.ofPattern("MMM d, yyyy 'at' h:mm a")
        zonedDateTime.format(formatter)
    } catch (e: DateTimeParseException) {
        // Fallback: try parsing without timezone
        try {
            val localDateTime = java.time.LocalDateTime.parse(isoTimestamp.substringBefore("Z"))
            val formatter = DateTimeFormatter.ofPattern("MMM d, yyyy 'at' h:mm a")
            localDateTime.format(formatter)
        } catch (e2: Exception) {
            isoTimestamp // Return original if all parsing fails
        }
    }
}
