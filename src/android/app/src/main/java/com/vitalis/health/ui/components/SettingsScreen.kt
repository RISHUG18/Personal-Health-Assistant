package com.vitalis.health.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.automirrored.filled.Logout
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.vitalis.health.ui.AuthViewModel
import com.vitalis.health.ui.theme.VitalisDanger
import com.vitalis.health.ui.theme.VitalisPrimary
import com.vitalis.health.ui.theme.VitalisTextSecondary

/**
 * Settings Screen composable.
 *
 * Features:
 * - Edit Profile button
 * - Logout button
 * - Delete Account button with confirmation dialog
 * - Loading states and error handling
 *
 * @param viewModel The [AuthViewModel] that handles profile and auth operations.
 * @param userId The ID of the currently logged-in user.
 * @param onNavigateToProfileEdit Callback to navigate to profile edit screen.
 * @param onNavigateToLogin Callback to navigate to login screen (after logout or deletion).
 * @param onNavigateBack Callback to navigate back to previous screen.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    viewModel: AuthViewModel,
    userId: String,
    onNavigateToProfileEdit: () -> Unit,
    onNavigateToLogin: () -> Unit,
    onNavigateBack: () -> Unit,
    modifier: Modifier = Modifier
) {
    val profileState by viewModel.profileState.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }
    var showDeleteDialog by remember { mutableStateOf(false) }

    // Handle profile state changes (specifically for account deletion)
    LaunchedEffect(profileState) {
        when (profileState) {
            is AuthViewModel.ProfileUiState.Deleted -> {
                snackbarHostState.showSnackbar("Account deleted successfully")
                viewModel.resetProfileState()
                onNavigateToLogin()
            }
            is AuthViewModel.ProfileUiState.Error -> {
                val errorMessage = (profileState as AuthViewModel.ProfileUiState.Error).message
                snackbarHostState.showSnackbar(errorMessage)
                viewModel.resetProfileState()
            }
            else -> { /* Idle, Loading, or Success - no action */ }
        }
    }

    // Delete Account Confirmation Dialog
    if (showDeleteDialog) {
        DeleteAccountDialog(
            onConfirm = {
                showDeleteDialog = false
                viewModel.deleteUser(userId)
            },
            onDismiss = {
                showDeleteDialog = false
            }
        )
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Settings") },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(
                            imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                            contentDescription = "Back"
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface,
                    titleContentColor = MaterialTheme.colorScheme.onSurface
                )
            )
        },
        snackbarHost = { SnackbarHost(snackbarHostState) },
        modifier = modifier
    ) { paddingValues ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .background(MaterialTheme.colorScheme.background)
        ) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .verticalScroll(rememberScrollState())
                    .padding(horizontal = 24.dp, vertical = 16.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                // Account Section
                Text(
                    text = "Account",
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.onBackground
                )

                SettingsOption(
                    icon = Icons.Default.Edit,
                    title = "Edit Profile",
                    description = "Update your personal information",
                    onClick = onNavigateToProfileEdit,
                    enabled = profileState !is AuthViewModel.ProfileUiState.Loading
                )

                SettingsOption(
                    icon = Icons.AutoMirrored.Filled.Logout,
                    title = "Logout",
                    description = "Sign out of your account",
                    onClick = {
                        viewModel.logout()
                        onNavigateToLogin()
                    },
                    enabled = profileState !is AuthViewModel.ProfileUiState.Loading
                )

                Spacer(modifier = Modifier.height(16.dp))

                // Danger Zone Section
                Text(
                    text = "Danger Zone",
                    style = MaterialTheme.typography.titleMedium,
                    color = VitalisDanger
                )

                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(
                        containerColor = VitalisDanger.copy(alpha = 0.1f)
                    ),
                    shape = MaterialTheme.shapes.medium
                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        Text(
                            text = "Delete Account",
                            style = MaterialTheme.typography.titleSmall,
                            color = VitalisDanger
                        )

                        Text(
                            text = "Permanently delete your account and all associated data. This action cannot be undone.",
                            style = MaterialTheme.typography.bodyMedium,
                            color = VitalisTextSecondary
                        )

                        Button(
                            onClick = { showDeleteDialog = true },
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(48.dp),
                            enabled = profileState !is AuthViewModel.ProfileUiState.Loading,
                            colors = ButtonDefaults.buttonColors(
                                containerColor = VitalisDanger,
                                contentColor = Color.White
                            ),
                            shape = MaterialTheme.shapes.medium
                        ) {
                            if (profileState is AuthViewModel.ProfileUiState.Loading) {
                                CircularProgressIndicator(
                                    color = Color.White,
                                    modifier = Modifier.size(20.dp)
                                )
                            } else {
                                Icon(
                                    imageVector = Icons.Default.Delete,
                                    contentDescription = null,
                                    modifier = Modifier.size(20.dp)
                                )
                                Text(
                                    text = "Delete My Account",
                                    style = MaterialTheme.typography.bodyLarge,
                                    modifier = Modifier.padding(start = 8.dp)
                                )
                            }
                        }
                    }
                }

                Spacer(modifier = Modifier.height(24.dp))
            }
        }
    }
}

/**
 * Reusable settings option item.
 */
@Composable
private fun SettingsOption(
    icon: ImageVector,
    title: String,
    description: String,
    onClick: () -> Unit,
    enabled: Boolean = true
) {
    Card(
        onClick = onClick,
        modifier = Modifier.fillMaxWidth(),
        enabled = enabled,
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant
        ),
        shape = MaterialTheme.shapes.medium
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = VitalisPrimary,
                modifier = Modifier.size(24.dp)
            )

            Text(
                text = title,
                style = MaterialTheme.typography.titleSmall,
                color = MaterialTheme.colorScheme.onSurface
            )

            Text(
                text = description,
                style = MaterialTheme.typography.bodySmall,
                color = VitalisTextSecondary
            )
        }
    }
}

/**
 * Confirmation dialog for account deletion.
 */
@Composable
private fun DeleteAccountDialog(
    onConfirm: () -> Unit,
    onDismiss: () -> Unit
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        icon = {
            Icon(
                imageVector = Icons.Default.Delete,
                contentDescription = null,
                tint = VitalisDanger,
                modifier = Modifier.size(32.dp)
            )
        },
        title = {
            Text(
                text = "Delete Account?",
                style = MaterialTheme.typography.titleLarge,
                textAlign = TextAlign.Center
            )
        },
        text = {
            Text(
                text = "Are you sure you want to delete your account? This will permanently remove all your data including:\n\n• Profile information\n• Health records\n• Medical reports\n• Vitals data\n• All associated alerts\n\nThis action cannot be undone.",
                style = MaterialTheme.typography.bodyMedium,
                textAlign = TextAlign.Start
            )
        },
        confirmButton = {
            Button(
                onClick = onConfirm,
                colors = ButtonDefaults.buttonColors(
                    containerColor = VitalisDanger,
                    contentColor = Color.White
                )
            ) {
                Text("Delete Account")
            }
        },
        dismissButton = {
            OutlinedButton(onClick = onDismiss) {
                Text("Cancel")
            }
        },
        containerColor = MaterialTheme.colorScheme.surface,
        tonalElevation = 6.dp
    )
}
