package com.vitalis.health.ui.components

import androidx.compose.animation.core.animateDpAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Cloud
import androidx.compose.material.icons.outlined.Language
import androidx.compose.material.icons.outlined.Person
import androidx.compose.material.icons.outlined.Science
import androidx.compose.material.icons.outlined.Share
import androidx.compose.material.icons.outlined.Shield
import androidx.compose.material.icons.outlined.Visibility
import androidx.compose.material.icons.outlined.DarkMode
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.runtime.saveable.rememberSaveable
import com.vitalis.health.ui.theme.LocalVitalisColors
import com.vitalis.health.ui.theme.VitalisDanger
import com.vitalis.health.ui.theme.VitalisPrimary
import com.vitalis.health.ui.theme.VitalisTextMuted

// ─── Main Screen ─────────────────────────────────────────────────────────────

@Composable
fun ProfileConsentScreen(
    onLogoutClick: () -> Unit = {},
    isDarkThemeEnabled: Boolean = false,
    onDarkThemeChanged: (Boolean) -> Unit = {},
) {
    val colors = LocalVitalisColors.current

    var geminiEnabled by rememberSaveable { mutableStateOf(false) }
    var shareAnonymizedData by rememberSaveable { mutableStateOf(false) }
    var shareUsageAnalytics by rememberSaveable { mutableStateOf(false) }
    var doctorSummaryAccess by rememberSaveable { mutableStateOf(true) }
    var doctorLabAccess by rememberSaveable { mutableStateOf(true) }
    var doctorAlertAccess by rememberSaveable { mutableStateOf(false) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(colors.bgApp)
            .verticalScroll(rememberScrollState()),
    ) {
        ProfileHeader(onLogoutClick = onLogoutClick)

        Column(
            modifier = Modifier.padding(horizontal = 24.dp, vertical = 20.dp),
            verticalArrangement = Arrangement.spacedBy(24.dp),
        ) {
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

            SettingsGroup(title = "SYSTEM") {
                SettingsToggleItem(
                    icon = Icons.Outlined.DarkMode,
                    label = "Dark Theme",
                    subtitle = "Enable low-contrast dark mode across the app.",
                    checked = isDarkThemeEnabled,
                    onCheckedChange = onDarkThemeChanged,
                )
                SettingsDivider()
                SettingsActionItem(
                    icon = Icons.Outlined.Language,
                    label = "Language",
                    value = "English",
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
    val colors = LocalVitalisColors.current

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(MaterialTheme.colorScheme.surface)
            .padding(vertical = 36.dp, horizontal = 24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Box(
            modifier = Modifier
                .size(76.dp)
                .clip(RoundedCornerShape(20.dp))
                .background(MaterialTheme.colorScheme.primary),
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
            color = MaterialTheme.colorScheme.onSurface,
        )

        Spacer(Modifier.height(4.dp))

        // Demographics (IBM Plex Mono style)
        Text(
            text = "ID #849201 · 25Y · Male",
            fontSize = 13.sp,
            color = colors.textMuted,
            style = MaterialTheme.typography.bodySmall,
            letterSpacing = 0.3.sp,
        )

        Spacer(Modifier.height(18.dp))

        // Manage Account button
        OutlinedButton(
            onClick = { /* placeholder */ },
            shape = RoundedCornerShape(6.dp),
            border = BorderStroke(1.5.dp, MaterialTheme.colorScheme.outline),
            colors = ButtonDefaults.outlinedButtonColors(
                containerColor = colors.bgApp,
                contentColor = colors.textSecondary,
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
            border = BorderStroke(1.5.dp, VitalisDanger),
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

    HorizontalDivider(color = colors.borderLight, thickness = 1.dp)
}

// ─── Settings Group ──────────────────────────────────────────────────────────

@Composable
private fun SettingsGroup(
    title: String,
    content: @Composable ColumnScope.() -> Unit,
) {
    val colors = LocalVitalisColors.current

    Column {
        Text(
            text = title,
            fontSize = 11.sp,
            fontWeight = FontWeight.Bold,
            color = colors.textMuted,
            letterSpacing = 0.8.sp,
            modifier = Modifier.padding(start = 2.dp, bottom = 8.dp),
        )

        Surface(
            shape = RoundedCornerShape(10.dp),
            color = MaterialTheme.colorScheme.surface,
            border = BorderStroke(1.dp, colors.borderLight),
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
    val colors = LocalVitalisColors.current

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 14.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Box(
            modifier = Modifier
                .size(30.dp)
                .clip(RoundedCornerShape(8.dp))
                .background(colors.bgApp),
            contentAlignment = Alignment.Center,
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                modifier = Modifier.size(16.dp),
                tint = colors.textSecondary,
            )
        }

        Spacer(Modifier.width(14.dp))

        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = label,
                fontSize = 14.sp,
                fontWeight = FontWeight.Medium,
                color = MaterialTheme.colorScheme.onSurface,
            )
            if (subtitle != null) {
                Spacer(Modifier.height(2.dp))
                Text(
                    text = subtitle,
                    fontSize = 12.sp,
                    color = colors.textMuted,
                    lineHeight = 16.sp,
                )
            }
        }

        Spacer(Modifier.width(8.dp))

        HtmlToggleSwitch(
            checked = checked,
            onCheckedChange = onCheckedChange,
        )
    }
}

@Composable
private fun SettingsActionItem(
    icon: ImageVector,
    label: String,
    value: String,
) {
    val colors = LocalVitalisColors.current

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 14.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Box(
            modifier = Modifier
                .size(30.dp)
                .clip(RoundedCornerShape(8.dp))
                .background(colors.bgApp),
            contentAlignment = Alignment.Center,
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                modifier = Modifier.size(16.dp),
                tint = colors.textSecondary,
            )
        }

        Spacer(Modifier.width(14.dp))

        Text(
            text = label,
            fontSize = 14.sp,
            fontWeight = FontWeight.Medium,
            color = MaterialTheme.colorScheme.onSurface,
            modifier = Modifier.weight(1f)
        )

        Text(
            text = value,
            fontSize = 13.sp,
            color = colors.textMuted,
        )
        Spacer(Modifier.width(8.dp))
        Text(
            text = ">",
            fontSize = 14.sp,
            fontWeight = FontWeight.SemiBold,
            color = colors.textMuted,
        )
    }
}

@Composable
private fun HtmlToggleSwitch(
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit,
    modifier: Modifier = Modifier,
) {
    val thumbOffset by animateDpAsState(
        targetValue = if (checked) 20.dp else 2.dp,
        animationSpec = tween(durationMillis = 180),
        label = "toggle_thumb_offset"
    )

    Box(
        modifier = modifier
            .width(42.dp)
            .height(24.dp)
            .clip(RoundedCornerShape(12.dp))
            .background(if (checked) VitalisPrimary else MaterialTheme.colorScheme.outline)
            .clickable(
                interactionSource = remember { MutableInteractionSource() },
                indication = null,
            ) {
                onCheckedChange(!checked)
            }
    ) {
        Box(
            modifier = Modifier
                .offset(x = thumbOffset, y = 2.dp)
                .size(20.dp)
                .clip(RoundedCornerShape(10.dp))
                .background(Color.White)
        )
    }
}

// ─── Divider between grouped items ───────────────────────────────────────────

@Composable
private fun SettingsDivider() {
    val colors = LocalVitalisColors.current

    HorizontalDivider(
        color = colors.borderLight,
        thickness = 1.dp,
        modifier = Modifier.padding(horizontal = 16.dp),
    )
}
