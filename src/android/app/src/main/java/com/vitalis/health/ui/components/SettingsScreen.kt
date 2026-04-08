package com.vitalis.health.ui.components

import androidx.compose.animation.core.animateDpAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.automirrored.filled.Logout
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material.icons.filled.Mail
import androidx.compose.material.icons.filled.Palette
import androidx.compose.material.icons.filled.Person
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.vitalis.health.data.model.UserProfile
import com.vitalis.health.ui.AuthViewModel
import com.vitalis.health.ui.theme.LocalVitalisColors
import com.vitalis.health.ui.theme.VitalisDanger
import com.vitalis.health.ui.theme.VitalisDangerBg
import com.vitalis.health.ui.theme.VitalisPrimary
import com.vitalis.health.ui.theme.VitalisPrimaryLight
import java.time.LocalDate
import java.time.Period

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    viewModel: AuthViewModel,
    userId: String,
    onNavigateToProfileEdit: () -> Unit,
    onNavigateToLogin: () -> Unit,
    onNavigateBack: () -> Unit,
    isDarkThemeEnabled: Boolean = false,
    onDarkThemeChanged: (Boolean) -> Unit = {},
    modifier: Modifier = Modifier,
) {
    val colors = LocalVitalisColors.current
    val profileState by viewModel.profileState.collectAsState()
    val userProfile by viewModel.currentUserProfile.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }
    var showDeleteDialog by remember { mutableStateOf(false) }

    LaunchedEffect(userId) {
        viewModel.fetchUserProfile(userId)
    }

    LaunchedEffect(profileState) {
        when (profileState) {
            is AuthViewModel.ProfileUiState.Success -> {
                snackbarHostState.showSnackbar("Profile updated")
                viewModel.resetProfileState()
            }

            is AuthViewModel.ProfileUiState.Deleted -> {
                snackbarHostState.showSnackbar("Account deleted successfully")
                viewModel.resetProfileState()
                onNavigateToLogin()
            }

            is AuthViewModel.ProfileUiState.Error -> {
                val error = (profileState as AuthViewModel.ProfileUiState.Error).message
                snackbarHostState.showSnackbar(error)
                viewModel.resetProfileState()
            }

            else -> {
                // no-op
            }
        }
    }

    if (showDeleteDialog) {
        DeleteAccountDialog(
            onConfirm = {
                showDeleteDialog = false
                viewModel.deleteUser(userId)
            },
            onDismiss = { showDeleteDialog = false },
        )
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = "Profile & Settings",
                        color = colors.textPrimary,
                    )
                },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(
                            imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                            contentDescription = "Back",
                            tint = colors.textPrimary,
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface,
                    titleContentColor = colors.textPrimary,
                ),
            )
        },
        snackbarHost = { SnackbarHost(hostState = snackbarHostState) },
        modifier = modifier,
    ) { paddingValues ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .background(colors.bgApp),
        ) {
            if (profileState is AuthViewModel.ProfileUiState.Loading && userProfile == null) {
                CircularProgressIndicator(
                    color = VitalisPrimary,
                    modifier = Modifier.align(Alignment.Center),
                )
                return@Box
            }

            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .verticalScroll(rememberScrollState())
                    .padding(horizontal = 20.dp, vertical = 16.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp),
            ) {
                userProfile?.let {
                    ProfileHeroCard(
                        profile = it,
                        onEditProfile = onNavigateToProfileEdit,
                        onLogout = {
                            viewModel.logout()
                            onNavigateToLogin()
                        },
                    )
                } ?: run {
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                        shape = RoundedCornerShape(16.dp),
                    ) {
                        Column(
                            modifier = Modifier.padding(20.dp),
                            verticalArrangement = Arrangement.spacedBy(10.dp),
                        ) {
                            Text(
                                text = "Profile unavailable",
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.Bold,
                                color = colors.textPrimary,
                            )
                            Text(
                                text = "We couldn't load your profile right now.",
                                style = MaterialTheme.typography.bodyMedium,
                                color = colors.textSecondary,
                            )
                            OutlinedButton(
                                onClick = { viewModel.fetchUserProfile(userId, forceRefresh = true) },
                                border = ButtonDefaults.outlinedButtonBorder.copy(brush = Brush.verticalGradient(listOf(VitalisPrimary, VitalisPrimary))),
                            ) {
                                Text("Retry", color = VitalisPrimary)
                            }
                        }
                    }
                }

                SettingsSectionCard(title = "Preferences") {
                    SettingRow(
                        icon = Icons.Default.Palette,
                        title = "Dark Theme",
                        subtitle = "Enable low-contrast dark mode across the app.",
                        trailing = {
                            HtmlToggleSwitch(
                                checked = isDarkThemeEnabled,
                                onCheckedChange = onDarkThemeChanged,
                            )
                        },
                    )
                }

                userProfile?.let { profile ->
                    SettingsSectionCard(title = "Account") {
                        SettingRow(
                            icon = Icons.Default.Mail,
                            title = "Email",
                            subtitle = profile.email,
                        )
                        HorizontalDivider(color = colors.borderLight)
                        SettingRow(
                            icon = Icons.Default.Person,
                            title = "Demographics",
                            subtitle = profileDemographics(profile),
                        )
                        HorizontalDivider(color = colors.borderLight)
                        SettingRow(
                            icon = Icons.AutoMirrored.Filled.Logout,
                            title = "Log out",
                            subtitle = "Sign out from this device",
                            onClick = {
                                viewModel.logout()
                                onNavigateToLogin()
                            },
                        )
                    }
                }

                Text(
                    text = "Danger Zone",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold,
                    color = VitalisDanger,
                )

                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(containerColor = VitalisDangerBg),
                    shape = RoundedCornerShape(16.dp),
                ) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(10.dp),
                    ) {
                        Text(
                            text = "Delete Account",
                            style = MaterialTheme.typography.titleSmall,
                            fontWeight = FontWeight.Bold,
                            color = VitalisDanger,
                        )
                        Text(
                            text = "This action permanently removes your account and medical history from Vitalis.",
                            style = MaterialTheme.typography.bodySmall,
                            color = colors.textSecondary,
                        )
                        Button(
                            onClick = { showDeleteDialog = true },
                            enabled = profileState !is AuthViewModel.ProfileUiState.Loading,
                            colors = ButtonDefaults.buttonColors(
                                containerColor = VitalisDanger,
                                contentColor = Color.White,
                            ),
                            shape = RoundedCornerShape(12.dp),
                            modifier = Modifier.fillMaxWidth(),
                        ) {
                            Icon(
                                imageVector = Icons.Default.Delete,
                                contentDescription = null,
                                modifier = Modifier.size(18.dp),
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text("Delete My Account")
                        }
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))
            }
        }
    }
}

@Composable
private fun ProfileHeroCard(
    profile: UserProfile,
    onEditProfile: () -> Unit,
    onLogout: () -> Unit,
) {
    val colors = LocalVitalisColors.current
    val age = calculateAge(profile.dateOfBirth)
    val gender = profile.gender?.replaceFirstChar { it.uppercase() } ?: "Not specified"
    val identityLine = buildString {
        append("ID #")
        append(profile.id.take(8))
        if (age != null) {
            append(" • ")
            append(age)
            append("Y")
        }
        append(" • ")
        append(gender)
    }

    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.cardColors(containerColor = Color.Transparent),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .background(
                    brush = Brush.linearGradient(
                        colors = listOf(VitalisPrimary, colors.primaryDeeper),
                    ),
                )
                .padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(
                        modifier = Modifier
                            .size(66.dp)
                            .clip(RoundedCornerShape(18.dp))
                            .background(VitalisPrimaryLight),
                        contentAlignment = Alignment.Center,
                    ) {
                        Text(
                            text = profile.fullName
                                .split(" ")
                                .filter { it.isNotBlank() }
                                .take(2)
                                .joinToString("") { it.first().uppercase() },
                            style = MaterialTheme.typography.headlineSmall,
                            fontWeight = FontWeight.Bold,
                            color = colors.primaryDeeper,
                        )
                    }

                    Spacer(modifier = Modifier.width(12.dp))

                    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        Text(
                            text = profile.fullName,
                            style = MaterialTheme.typography.titleLarge,
                            fontWeight = FontWeight.Bold,
                            color = Color.White,
                        )
                        Text(
                            text = identityLine,
                            style = MaterialTheme.typography.labelMedium,
                            color = Color.White.copy(alpha = 0.88f),
                        )
                    }
                }
            }

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                OutlinedButton(
                    onClick = onEditProfile,
                    border = ButtonDefaults.outlinedButtonBorder,
                    colors = ButtonDefaults.outlinedButtonColors(
                        containerColor = Color.White.copy(alpha = 0.14f),
                        contentColor = Color.White,
                    ),
                    shape = RoundedCornerShape(12.dp),
                    modifier = Modifier.weight(1f),
                ) {
                    Icon(
                        imageVector = Icons.Default.Edit,
                        contentDescription = null,
                        modifier = Modifier.size(18.dp),
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("Edit Profile")
                }

                OutlinedButton(
                    onClick = onLogout,
                    border = ButtonDefaults.outlinedButtonBorder,
                    colors = ButtonDefaults.outlinedButtonColors(
                        containerColor = Color.White.copy(alpha = 0.08f),
                        contentColor = Color.White,
                    ),
                    shape = RoundedCornerShape(12.dp),
                    modifier = Modifier.weight(1f),
                ) {
                    Icon(
                        imageVector = Icons.AutoMirrored.Filled.Logout,
                        contentDescription = null,
                        modifier = Modifier.size(18.dp),
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("Log Out")
                }
            }
        }
    }
}

@Composable
private fun SettingsSectionCard(
    title: String,
    content: @Composable ColumnScope.() -> Unit,
) {
    val colors = LocalVitalisColors.current
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text(
            text = title,
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.SemiBold,
            color = colors.textPrimary,
        )
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(16.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        ) {
            Column(
                modifier = Modifier.fillMaxWidth(),
                content = content,
            )
        }
    }
}

@Composable
private fun SettingRow(
    icon: ImageVector,
    title: String,
    subtitle: String,
    onClick: (() -> Unit)? = null,
    trailing: @Composable (() -> Unit)? = null,
) {
    val colors = LocalVitalisColors.current
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .then(
                if (onClick != null) {
                    Modifier.clickable(onClick = onClick)
                } else {
                    Modifier
                },
            )
            .padding(horizontal = 14.dp, vertical = 14.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Box(
            modifier = Modifier
                .size(34.dp)
                .clip(RoundedCornerShape(10.dp))
                .background(colors.primaryLight),
            contentAlignment = Alignment.Center,
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = VitalisPrimary,
                modifier = Modifier.size(18.dp),
            )
        }

        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = title,
                style = MaterialTheme.typography.titleSmall,
                color = colors.textPrimary,
            )
            Text(
                text = subtitle,
                style = MaterialTheme.typography.bodySmall,
                color = colors.textSecondary,
            )
        }

        trailing?.invoke()
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
        label = "theme_toggle_thumb_offset",
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
            },
    ) {
        Box(
            modifier = Modifier
                .padding(top = 2.dp)
                .padding(start = thumbOffset)
                .size(20.dp)
                .clip(CircleShape)
                .background(Color.White),
        )
    }
}

@Composable
private fun DeleteAccountDialog(
    onConfirm: () -> Unit,
    onDismiss: () -> Unit,
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = {
            Text(
                text = "Delete Account?",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
            )
        },
        text = {
            Text(
                text = "This action is irreversible and will permanently remove all your data.",
                style = MaterialTheme.typography.bodyMedium,
            )
        },
        confirmButton = {
            Button(
                onClick = onConfirm,
                colors = ButtonDefaults.buttonColors(containerColor = VitalisDanger),
            ) {
                Text("Delete", color = Color.White)
            }
        },
        dismissButton = {
            OutlinedButton(onClick = onDismiss) {
                Text("Cancel")
            }
        },
        shape = RoundedCornerShape(16.dp),
    )
}

private fun calculateAge(dateOfBirth: String?): Int? {
    if (dateOfBirth.isNullOrBlank()) return null
    return try {
        val dob = LocalDate.parse(dateOfBirth)
        if (dob.isAfter(LocalDate.now())) return null
        Period.between(dob, LocalDate.now()).years
    } catch (_: Exception) {
        null
    }
}

private fun profileDemographics(profile: UserProfile): String {
    val parts = mutableListOf<String>()
    calculateAge(profile.dateOfBirth)?.let { parts.add("${it}Y") }
    profile.gender?.replaceFirstChar { it.uppercase() }?.let { parts.add(it) }
    profile.heightCm?.let { parts.add("${it.toInt()} cm") }
    profile.weightKg?.let { parts.add("${it.toInt()} kg") }
    return if (parts.isEmpty()) "No demographics saved" else parts.joinToString(" • ")
}
