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
import com.vitalis.health.ui.theme.LocalVitalisColors
import com.vitalis.health.ui.theme.VitalisDanger
import com.vitalis.health.ui.theme.VitalisPrimary
import com.vitalis.health.ui.theme.VitalisWarning
import java.text.ParseException
import java.text.SimpleDateFormat
import java.util.Locale
import java.util.TimeZone

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
    val colors = LocalVitalisColors.current
    val uiState by viewModel.alertsState.collectAsState()

    Box(
        modifier = modifier
            .fillMaxSize()
            .background(colors.bgApp)
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
    val colors = LocalVitalisColors.current

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
                color = colors.textPrimary,
            )

            Spacer(modifier = Modifier.height(4.dp))

            Text(
                text = "${alerts.size} active alert${if (alerts.size != 1) "s" else ""}",
                style = MaterialTheme.typography.bodySmall,
                color = colors.textSecondary,
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
    val colors = LocalVitalisColors.current
    var expanded by remember { mutableStateOf(false) }
    val hasEvidence = alert.evidence.isNotEmpty()

    val severityColor = when (alert.severity.lowercase()) {
        "high" -> VitalisDanger
        "medium" -> VitalisWarning
        "low" -> VitalisPrimary
        else -> colors.textSecondary
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
            shape = RoundedCornerShape(8.dp),
        colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.surface,
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
                        color = colors.textPrimary,
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis,
                        modifier = Modifier.weight(1f)
                    )
                }

                // Severity badge
                SeverityBadge(severity = alert.severity)
            }

            Spacer(modifier = Modifier.height(12.dp))

            // Alert message/reason
            Text(
                text = alert.message,
                style = MaterialTheme.typography.bodyMedium,
                color = colors.textSecondary,
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
                    color = colors.textSecondary,
                )

                // Expand/collapse indicator for evidence
                if (hasEvidence) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        modifier = Modifier
                            .clip(RoundedCornerShape(4.dp))
                            .background(colors.bgInput)
                            .padding(horizontal = 8.dp, vertical = 4.dp)
                    ) {
                        Text(
                            text = if (expanded) "Hide evidence" else "View evidence",
                            style = MaterialTheme.typography.labelSmall,
                            color = colors.textSecondary,
                        )
                        Spacer(modifier = Modifier.width(4.dp))
                        Icon(
                            imageVector = if (expanded) {
                                Icons.Filled.KeyboardArrowUp
                            } else {
                                Icons.Filled.KeyboardArrowDown
                            },
                            contentDescription = null,
                            tint = colors.textSecondary,
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
    modifier: Modifier = Modifier
) {
    val colors = LocalVitalisColors.current
    val (badgeColor, badgeBg) = when (severity.lowercase(Locale.US)) {
        "high" -> VitalisDanger to colors.dangerBg
        "medium" -> VitalisWarning to colors.warningBg
        else -> VitalisPrimary to colors.primaryLight
    }

    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(8.dp),
        color = badgeBg,
    ) {
        Text(
            text = severity.replaceFirstChar { it.uppercase() },
            style = MaterialTheme.typography.labelSmall,
            fontWeight = FontWeight.SemiBold,
            color = badgeColor,
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
        )
    }
}

@Composable
private fun EvidenceSection(
    evidence: List<AlertEvidence>,
    modifier: Modifier = Modifier
) {
    val colors = LocalVitalisColors.current

    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(8.dp),
        color = colors.bgInput,
    ) {
        Column(
            modifier = Modifier.padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Text(
                text = "Evidence",
                style = MaterialTheme.typography.labelMedium,
                fontWeight = FontWeight.SemiBold,
                color = colors.textPrimary,
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
    val colors = LocalVitalisColors.current

    Row(
        modifier = modifier.fillMaxWidth(),
        verticalAlignment = Alignment.Top
    ) {
        Icon(
            imageVector = Icons.Outlined.Description,
            contentDescription = null,
            tint = colors.textSecondary,
            modifier = Modifier.size(16.dp)
        )

        Spacer(modifier = Modifier.width(8.dp))

        Column(modifier = Modifier.weight(1f)) {
            // Show report ID if available
            evidence.reportId?.let { reportId ->
                Text(
                    text = "Report: ${reportId.take(8)}…",
                    style = MaterialTheme.typography.bodySmall,
                    color = colors.textSecondary,
                )
            }

            // Show lab result ID if available
            evidence.labResultId?.let { labId ->
                Text(
                    text = "Lab Result: ${labId.take(8)}…",
                    style = MaterialTheme.typography.bodySmall,
                    color = colors.textSecondary,
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
                        color = colors.textSecondary,
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
    val inputPatterns = listOf(
        "yyyy-MM-dd'T'HH:mm:ss.SSSX",
        "yyyy-MM-dd'T'HH:mm:ssX",
        "yyyy-MM-dd'T'HH:mm:ss.SSS",
        "yyyy-MM-dd'T'HH:mm:ss",
    )
    val outputFormatter = SimpleDateFormat("MMM d, yyyy 'at' h:mm a", Locale.US)

    inputPatterns.forEach { pattern ->
        val parser = SimpleDateFormat(pattern, Locale.US).apply {
            isLenient = false
            timeZone = TimeZone.getTimeZone("UTC")
        }
        try {
            val parsed = parser.parse(isoTimestamp)
            if (parsed != null) {
                return outputFormatter.format(parsed)
            }
        } catch (_: ParseException) {
            // Try next parser pattern.
        }
    }

    return isoTimestamp
}
