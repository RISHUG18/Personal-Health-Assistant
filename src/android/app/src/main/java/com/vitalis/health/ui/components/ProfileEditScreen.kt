package com.vitalis.health.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Check
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
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
import androidx.compose.ui.focus.FocusDirection
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import com.vitalis.health.data.model.UserUpdateRequest
import com.vitalis.health.ui.AuthViewModel
import com.vitalis.health.ui.theme.VitalisPrimary
import com.vitalis.health.ui.theme.VitalisTextMuted

/**
 * Profile Edit Screen composable.
 *
 * Features:
 * - Text fields for editing user profile (name, phone, DOB, gender, location, health metrics)
 * - Save button that calls viewModel.updateUserProfile()
 * - Loading state with spinner
 * - Success/error handling with snackbar
 *
 * @param viewModel The [AuthViewModel] that handles profile operations.
 * @param userId The ID of the user whose profile is being edited.
 * @param currentProfile The current user profile data to pre-populate fields.
 * @param onNavigateBack Callback to navigate back after successful update or on back press.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ProfileEditScreen(
    viewModel: AuthViewModel,
    userId: String,
    currentProfile: com.vitalis.health.data.model.UserProfile?,
    onNavigateBack: () -> Unit,
    modifier: Modifier = Modifier
) {
    val profileState by viewModel.profileState.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }
    val focusManager = LocalFocusManager.current

    // Form state
    var fullName by remember { mutableStateOf(currentProfile?.fullName ?: "") }
    var phone by remember { mutableStateOf(currentProfile?.phone ?: "") }
    var dateOfBirth by remember { mutableStateOf(currentProfile?.dateOfBirth ?: "") }
    var gender by remember { mutableStateOf(currentProfile?.gender ?: "") }
    var city by remember { mutableStateOf(currentProfile?.city ?: "") }
    var state by remember { mutableStateOf(currentProfile?.state ?: "") }
    var country by remember { mutableStateOf(currentProfile?.country ?: "") }
    var bloodGroup by remember { mutableStateOf(currentProfile?.bloodGroup ?: "") }
    var heightCm by remember { mutableStateOf(currentProfile?.heightCm?.toString() ?: "") }
    var weightKg by remember { mutableStateOf(currentProfile?.weightKg?.toString() ?: "") }

    // Handle profile state changes
    LaunchedEffect(profileState) {
        when (profileState) {
            is AuthViewModel.ProfileUiState.Success -> {
                snackbarHostState.showSnackbar("Profile updated successfully!")
                viewModel.resetProfileState()
                onNavigateBack()
            }
            is AuthViewModel.ProfileUiState.Error -> {
                val errorMessage = (profileState as AuthViewModel.ProfileUiState.Error).message
                snackbarHostState.showSnackbar(errorMessage)
                viewModel.resetProfileState()
            }
            else -> { /* Idle or Loading - no action */ }
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Edit Profile") },
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
                    .padding(horizontal = 24.dp, vertical = 16.dp)
                    .imePadding(),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                // Personal Information Section
                Text(
                    text = "Personal Information",
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.onBackground
                )

                ProfileTextField(
                    label = "Full Name",
                    value = fullName,
                    onValueChange = { fullName = it },
                    placeholder = "Enter your full name",
                    enabled = profileState !is AuthViewModel.ProfileUiState.Loading,
                    imeAction = ImeAction.Next,
                    onNext = { focusManager.moveFocus(FocusDirection.Down) }
                )

                ProfileTextField(
                    label = "Phone",
                    value = phone,
                    onValueChange = { phone = it },
                    placeholder = "Enter phone number",
                    keyboardType = KeyboardType.Phone,
                    enabled = profileState !is AuthViewModel.ProfileUiState.Loading,
                    imeAction = ImeAction.Next,
                    onNext = { focusManager.moveFocus(FocusDirection.Down) }
                )

                ProfileTextField(
                    label = "Date of Birth",
                    value = dateOfBirth,
                    onValueChange = { dateOfBirth = it },
                    placeholder = "YYYY-MM-DD",
                    enabled = profileState !is AuthViewModel.ProfileUiState.Loading,
                    imeAction = ImeAction.Next,
                    onNext = { focusManager.moveFocus(FocusDirection.Down) }
                )

                ProfileTextField(
                    label = "Gender",
                    value = gender,
                    onValueChange = { gender = it },
                    placeholder = "Male, Female, Other",
                    enabled = profileState !is AuthViewModel.ProfileUiState.Loading,
                    imeAction = ImeAction.Next,
                    onNext = { focusManager.moveFocus(FocusDirection.Down) }
                )

                // Location Section
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = "Location",
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.onBackground
                )

                ProfileTextField(
                    label = "City",
                    value = city,
                    onValueChange = { city = it },
                    placeholder = "Enter city",
                    enabled = profileState !is AuthViewModel.ProfileUiState.Loading,
                    imeAction = ImeAction.Next,
                    onNext = { focusManager.moveFocus(FocusDirection.Down) }
                )

                ProfileTextField(
                    label = "State",
                    value = state,
                    onValueChange = { state = it },
                    placeholder = "Enter state",
                    enabled = profileState !is AuthViewModel.ProfileUiState.Loading,
                    imeAction = ImeAction.Next,
                    onNext = { focusManager.moveFocus(FocusDirection.Down) }
                )

                ProfileTextField(
                    label = "Country",
                    value = country,
                    onValueChange = { country = it },
                    placeholder = "Enter country",
                    enabled = profileState !is AuthViewModel.ProfileUiState.Loading,
                    imeAction = ImeAction.Next,
                    onNext = { focusManager.moveFocus(FocusDirection.Down) }
                )

                // Health Metrics Section
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = "Health Metrics",
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.onBackground
                )

                ProfileTextField(
                    label = "Blood Group",
                    value = bloodGroup,
                    onValueChange = { bloodGroup = it },
                    placeholder = "A+, B+, O-, etc.",
                    enabled = profileState !is AuthViewModel.ProfileUiState.Loading,
                    imeAction = ImeAction.Next,
                    onNext = { focusManager.moveFocus(FocusDirection.Down) }
                )

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        ProfileTextField(
                            label = "Height (cm)",
                            value = heightCm,
                            onValueChange = { heightCm = it },
                            placeholder = "170",
                            keyboardType = KeyboardType.Decimal,
                            enabled = profileState !is AuthViewModel.ProfileUiState.Loading,
                            imeAction = ImeAction.Next,
                            onNext = { focusManager.moveFocus(FocusDirection.Right) }
                        )
                    }

                    Column(modifier = Modifier.weight(1f)) {
                        ProfileTextField(
                            label = "Weight (kg)",
                            value = weightKg,
                            onValueChange = { weightKg = it },
                            placeholder = "70",
                            keyboardType = KeyboardType.Decimal,
                            enabled = profileState !is AuthViewModel.ProfileUiState.Loading,
                            imeAction = ImeAction.Done,
                            onNext = { focusManager.clearFocus() }
                        )
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))

                // Save Button
                Button(
                    onClick = {
                        focusManager.clearFocus()
                        val updateRequest = UserUpdateRequest(
                            fullName = fullName.trim().takeIf { it.isNotBlank() },
                            phone = phone.trim().takeIf { it.isNotBlank() },
                            dateOfBirth = dateOfBirth.trim().takeIf { it.isNotBlank() },
                            gender = gender.trim().takeIf { it.isNotBlank() },
                            city = city.trim().takeIf { it.isNotBlank() },
                            state = state.trim().takeIf { it.isNotBlank() },
                            country = country.trim().takeIf { it.isNotBlank() },
                            bloodGroup = bloodGroup.trim().takeIf { it.isNotBlank() },
                            heightCm = heightCm.trim().toDoubleOrNull(),
                            weightKg = weightKg.trim().toDoubleOrNull()
                        )
                        viewModel.updateUserProfile(userId, updateRequest)
                    },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(56.dp),
                    enabled = profileState !is AuthViewModel.ProfileUiState.Loading,
                    colors = ButtonDefaults.buttonColors(
                        containerColor = VitalisPrimary,
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
                            imageVector = Icons.Default.Check,
                            contentDescription = null,
                            modifier = Modifier.size(20.dp)
                        )
                        Text(
                            text = "Save Changes",
                            style = MaterialTheme.typography.bodyLarge,
                            modifier = Modifier.padding(start = 8.dp)
                        )
                    }
                }

                Spacer(modifier = Modifier.height(24.dp))
            }
        }
    }
}

/**
 * Reusable text field component for profile editing.
 */
@Composable
private fun ProfileTextField(
    label: String,
    value: String,
    onValueChange: (String) -> Unit,
    placeholder: String,
    keyboardType: KeyboardType = KeyboardType.Text,
    imeAction: ImeAction = ImeAction.Next,
    enabled: Boolean = true,
    onNext: () -> Unit = {}
) {
    Column {
        Text(
            text = label,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onBackground,
            modifier = Modifier.padding(bottom = 6.dp)
        )

        OutlinedTextField(
            value = value,
            onValueChange = onValueChange,
            placeholder = {
                Text(
                    text = placeholder,
                    color = VitalisTextMuted
                )
            },
            singleLine = true,
            keyboardOptions = KeyboardOptions(
                keyboardType = keyboardType,
                imeAction = imeAction
            ),
            keyboardActions = KeyboardActions(
                onNext = { onNext() },
                onDone = { onNext() }
            ),
            colors = OutlinedTextFieldDefaults.colors(
                focusedContainerColor = MaterialTheme.colorScheme.surfaceVariant,
                unfocusedContainerColor = MaterialTheme.colorScheme.surfaceVariant,
                focusedBorderColor = VitalisPrimary,
                unfocusedBorderColor = Color.Transparent
            ),
            shape = MaterialTheme.shapes.medium,
            modifier = Modifier.fillMaxWidth(),
            enabled = enabled
        )
    }
}
