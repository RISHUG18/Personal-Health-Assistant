package com.vitalis.health.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.AutoGraph
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.vitalis.health.data.model.HealthSummary
import com.vitalis.health.ui.theme.LocalVitalisColors
import com.vitalis.health.ui.theme.VitalisPrimary

@Composable
fun HealthSummaryCard(
    summary: HealthSummary?,
    isFetchingInitialSummary: Boolean,
    isGeneratingSummary: Boolean,
    onGenerateFreshSummary: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val colors = LocalVitalisColors.current
    val points = parseSummaryPoints(summary?.summaryContent)

    Card(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.45f),
        ),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                Icon(
                    imageVector = Icons.Outlined.AutoGraph,
                    contentDescription = null,
                    tint = VitalisPrimary,
                    modifier = Modifier.size(20.dp),
                )
                Text(
                    text = "Weekly Health Brief",
                    style = MaterialTheme.typography.titleMedium,
                    color = colors.textPrimary,
                    fontWeight = FontWeight.SemiBold,
                )
            }

            if (isFetchingInitialSummary) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(16.dp),
                        strokeWidth = 2.dp,
                        color = VitalisPrimary,
                    )
                    Text(
                        text = "Loading latest summary...",
                        style = MaterialTheme.typography.bodyMedium,
                        color = colors.textSecondary,
                    )
                }
            } else if (points.isEmpty()) {
                Text(
                    text = "No summary available yet. Generate a fresh brief to see this week's key health trends.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = colors.textSecondary,
                )
            } else {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    points.forEach { point ->
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            verticalAlignment = Alignment.Top,
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                        ) {
                            Box(
                                modifier = Modifier
                                    .padding(top = 6.dp)
                                    .size(6.dp)
                                    .background(color = VitalisPrimary, shape = CircleShape),
                            )
                            Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                                point.heading?.let { heading ->
                                    Text(
                                        text = heading,
                                        style = MaterialTheme.typography.labelLarge,
                                        color = VitalisPrimary,
                                        fontWeight = FontWeight.SemiBold,
                                    )
                                }

                                if (point.body.isNotBlank()) {
                                    Text(
                                        text = point.body,
                                        style = MaterialTheme.typography.bodyMedium,
                                        color = colors.textPrimary,
                                    )
                                }
                            }
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(2.dp))

            OutlinedButton(
                onClick = onGenerateFreshSummary,
                enabled = !isGeneratingSummary,
                modifier = Modifier.fillMaxWidth(),
            ) {
                if (isGeneratingSummary) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(16.dp),
                        strokeWidth = 2.dp,
                        color = VitalisPrimary,
                    )
                    Spacer(modifier = Modifier.size(8.dp))
                    Text("Generating...")
                } else {
                    Text("Generate Fresh Summary")
                }
            }
        }
    }
}

private data class SummaryPoint(
    val heading: String? = null,
    val body: String = "",
)

private fun parseSummaryPoints(content: String?): List<SummaryPoint> {
    if (content.isNullOrBlank()) return emptyList()

    val headingPattern = Regex("^\\*\\*(.+?)\\*\\*\\s*[:\\-]?\\s*(.*)$")

    val parsed = content
        .lineSequence()
        .map { it.trim() }
        .filter { it.isNotEmpty() }
        .map { line ->
            line
                .removePrefix("-")
                .removePrefix("*")
                .removePrefix("•")
                .replace(Regex("^[0-9]+[.)]\\s*"), "")
                .trim()
        }
        .filter { it.isNotEmpty() }
        .map { normalizedLine ->
            val match = headingPattern.find(normalizedLine)
            if (match != null) {
                val headingText = match.groupValues[1].trim().trimEnd(':')
                val bodyText = match.groupValues[2].trim()
                SummaryPoint(
                    heading = headingText.ifBlank { null },
                    body = bodyText,
                )
            } else {
                SummaryPoint(body = normalizedLine)
            }
        }
        .toList()

    return if (parsed.isNotEmpty()) {
        parsed
    } else {
        listOf(SummaryPoint(body = content.trim()))
    }
}
