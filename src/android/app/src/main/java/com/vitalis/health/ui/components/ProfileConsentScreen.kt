package com.vitalis.health.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Cloud
import androidx.compose.material.icons.outlined.Person
import androidx.compose.material.icons.outlined.Science
import androidx.compose.material.icons.outlined.Share
import androidx.compose.material.icons.outlined.Shield
import androidx.compose.material.icons.outlined.Visibility
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.vitalis.health.ui.theme.*

// ─── Data classes for settings items ─────────────────────────────────────────

private data class ToggleItem(
    val icon: ImageVector,
    val label: String,
    val subtitle: String? = null,
    val key: String,
)

// ─── Main Screen ─────────────────────────────────────────────────────────────

@Composable
fun ProfileConsentScreen(
    onLogoutClick: () -> Unit = {}
) {
    // Hoisted toggle states — not wired to a ViewModel
    var geminiEnabled by remember { mutableStateOf(false) }
    var shareAnonymizedData by remember { mutableStateOf(false) }
    var shareUsageAnalytics by remember { mutableStateOf(false) }
    var doctorSummaryAccess by remember { mutableStateOf(true) }
    var doctorLabAccess by remember { mutableStateOf(true) }
    var doctorAlertAccess by remember { mutableStateOf(false) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(VitalisBgApp)
            .verticalScroll(rememberScrollState()),
    ) {
        // ── Profile Header ───────────────────────────────────────────
        ProfileHeader(onLogoutClick = onLogoutClick)

        // ── Settings Groups ──────────────────────────────────────────
        Column(
            modifier = Modifier.padding(horizontal = 24.dp, vertical = 20.dp),
            verticalArrangement = Arrangement.spacedBy(24.dp),
        ) {
            // Data Processing
            SettingsGroup(title = "DATA PROCESSING") {
                SettingsToggleItem(
                    icon = Icons.Outlined.Cloud,
                    label = "Enable Cloud AI (Gemini) Extraction",
                    subtitle = "Uses Google Gemini for advanced AI parsing of lab reports. " +
                            "When disabled, standard local regex extraction is used.",
                    checked = geminiEnabled,
                    onCheckedChange = { geminiEnabled = it },
                )
                SettingsDivider()
                SettingsToggleItem(
                    icon = Icons.Outlined.Science,
                    label = "Auto-Extract Lab Results",
                    subtitle = "Automatically extract lab values after OCR completes.",
                    checked = true,
                    onCheckedChange = { /* read-only placeholder */ },
                )
            }

            // Data Sharing
            SettingsGroup(title = "DATA SHARING") {
                SettingsToggleItem(
                    icon = Icons.Outlined.Share,
                    label = "Share Anonymized Health Data",
                    subtitle = "Contribute de-identified data to improve platform analytics.",
                    checked = shareAnonymizedData,
                    onCheckedChange = { shareAnonymizedData = it },
                )
                SettingsDivider()
                SettingsToggleItem(
                    icon = Icons.Outlined.Visibility,
                    label = "Share Usage Analytics",
                    subtitle = "Help us improve by sharing non-clinical usage patterns.",
                    checked = shareUsageAnalytics,
                    onCheckedChange = { shareUsageAnalytics = it },
                )
            }

            // Doctor Access
            SettingsGroup(title = "DOCTOR ACCESS") {
                SettingsToggleItem(
                    icon = Icons.Outlined.Person,
                    label = "Clinical Summary Access",
                    subtitle = "Allow your provider to view AI-generated health summaries.",
                    checked = doctorSummaryAccess,
                    onCheckedChange = { doctorSummaryAccess = it },
                )
                SettingsDivider()
                SettingsToggleItem(
                    icon = Icons.Outlined.Science,
                    label = "Lab Results Access",
                    subtitle = "Allow your provider to view extracted lab results.",
                    checked = doctorLabAccess,
                    onCheckedChange = { doctorLabAccess = it },
                )
                SettingsDivider()
                SettingsToggleItem(
                    icon = Icons.Outlined.Shield,
                    label = "Alert & Risk Data Access",
                    subtitle = "Allow your provider to view alerts and risk assessments.",
                    checked = doctorAlertAccess,
                    onCheckedChange = { doctorAlertAccess = it },
                )
            }
        }
    }
}

// ─── Profile Header ──────────────────────────────────────────────────────────

@Composable
private fun ProfileHeader(
    onLogoutClick: () -> Unit = {}
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(VitalisBgCard)
            .border(width = 0.dp, color = Color.Transparent) // clearance
            .padding(vertical = 36.dp, horizontal = 24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        // Avatar (76 dp, rounded 20 dp, primary bg, white initials)
        Box(
            modifier = Modifier
                .size(76.dp)
                .clip(RoundedCornerShape(20.dp))
                .background(VitalisPrimary),
            contentAlignment = Alignment.Center,
        ) {
            Text(
                text = "TG",
                color = Color.White,
                fontSize = 28.sp,
                fontWeight = FontWeight.Bold,
            )
        }

        Spacer(Modifier.height(14.dp))

        // Name
        Text(
            text = "Tanush Garg",
            fontSize = 22.sp,
            fontWeight = FontWeight.Bold,
            color = VitalisTextPrimary,
        )

        Spacer(Modifier.height(4.dp))

        // Demographics (IBM Plex Mono style)
        Text(
            text = "ID #849201 · 25Y · Male",
            fontSize = 13.sp,
            color = VitalisTextMuted,
            fontFamily = FontFamily.Monospace,
            letterSpacing = 0.3.sp,
        )

        Spacer(Modifier.height(18.dp))

        // Manage Account button
        OutlinedButton(
            onClick = { /* placeholder */ },
            shape = RoundedCornerShape(6.dp),
            border = androidx.compose.foundation.BorderStroke(1.5.dp, VitalisBorder),
            colors = ButtonDefaults.outlinedButtonColors(
                containerColor = VitalisBgApp,
                contentColor = VitalisTextSecondary,
            ),
            contentPadding = PaddingValues(horizontal = 22.dp, vertical = 9.dp),
        ) {
            Text(
                text = "Manage Account",
                fontSize = 13.sp,
                fontWeight = FontWeight.SemiBold,
            )
        }

        Spacer(Modifier.height(12.dp))

        // Log Out button — styled with VitalisDanger
        OutlinedButton(
            onClick = onLogoutClick,
            shape = RoundedCornerShape(6.dp),
            border = androidx.compose.foundation.BorderStroke(1.5.dp, VitalisDanger),
            colors = ButtonDefaults.outlinedButtonColors(
                containerColor = Color.Transparent,
                contentColor = VitalisDanger,
            ),
            contentPadding = PaddingValues(horizontal = 22.dp, vertical = 9.dp),
        ) {
            Text(
                text = "Log Out",
                fontSize = 13.sp,
                fontWeight = FontWeight.SemiBold,
            )
        }
    }

    // Bottom border matching HTML
    HorizontalDivider(color = Color(0xFFE8EEEB), thickness = 1.dp)
}

// ─── Settings Group ──────────────────────────────────────────────────────────

@Composable
private fun SettingsGroup(
    title: String,
    content: @Composable ColumnScope.() -> Unit,
) {
    Column {
        // Group title — 11 sp, uppercase, muted, 0.8 sp letter spacing
        Text(
            text = title,
            fontSize = 11.sp,
            fontWeight = FontWeight.Bold,
            color = VitalisTextMuted,
            letterSpacing = 0.8.sp,
            modifier = Modifier.padding(start = 2.dp, bottom = 8.dp),
        )

        // Grouped card with shared rounded corners (radius-md = 10 dp)
        Surface(
            shape = RoundedCornerShape(10.dp),
            color = VitalisBgCard,
            border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFFE8EEEB)),
        ) {
            Column(content = content)
        }
    }
}

// ─── Settings Toggle Item ────────────────────────────────────────────────────

@Composable
private fun SettingsToggleItem(
    icon: ImageVector,
    label: String,
    subtitle: String? = null,
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 14.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        // Icon box (30 dp, bg-app, 8 dp radius)
        Box(
            modifier = Modifier
                .size(30.dp)
                .clip(RoundedCornerShape(8.dp))
                .background(VitalisBgApp),
            contentAlignment = Alignment.Center,
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                modifier = Modifier.size(16.dp),
                tint = VitalisTextSecondary,
            )
        }

        Spacer(Modifier.width(14.dp))

        // Label + optional subtitle
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = label,
                fontSize = 14.sp,
                fontWeight = FontWeight.Medium,
                color = VitalisTextPrimary,
            )
            if (subtitle != null) {
                Spacer(Modifier.height(2.dp))
                Text(
                    text = subtitle,
                    fontSize = 12.sp,
                    color = VitalisTextMuted,
                    lineHeight = 16.sp,
                )
            }
        }

        Spacer(Modifier.width(8.dp))

        // Toggle — Material 3 Switch styled to match the HTML toggle
        Switch(
            checked = checked,
            onCheckedChange = onCheckedChange,
            colors = SwitchDefaults.colors(
                checkedThumbColor = Color.White,
                checkedTrackColor = VitalisPrimary,
                uncheckedThumbColor = Color.White,
                uncheckedTrackColor = VitalisBorder,
                uncheckedBorderColor = Color.Transparent,
            ),
        )
    }
}

// ─── Divider between grouped items ───────────────────────────────────────────

@Composable
private fun SettingsDivider() {
    HorizontalDivider(
        color = Color(0xFFE8EEEB),
        thickness = 1.dp,
        modifier = Modifier.padding(horizontal = 16.dp),
    )
}
