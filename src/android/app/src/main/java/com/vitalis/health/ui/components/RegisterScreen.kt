package com.vitalis.health.ui.components

import android.app.DatePickerDialog
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
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material.icons.filled.VisibilityOff
import androidx.compose.material.icons.outlined.DateRange
import androidx.compose.material.icons.outlined.MonitorHeart
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.ExposedDropdownMenuDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Snackbar
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
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
import androidx.compose.ui.focus.FocusDirection
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardCapitalization
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import com.vitalis.health.ui.AuthViewModel
import com.vitalis.health.ui.theme.LocalVitalisColors
import com.vitalis.health.ui.theme.VitalisDanger
import com.vitalis.health.ui.theme.VitalisPrimary
import com.vitalis.health.ui.theme.VitalisPrimaryLight
import java.util.Calendar
import java.util.Locale

/**
 * Registration screen composable — styled to match sample.html .auth-screen
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RegisterScreen(
    viewModel: AuthViewModel,
    onRegisterSuccess: (userId: String) -> Unit,
    onNavigateToLogin: () -> Unit,
    modifier: Modifier = Modifier
) {
    val colors = LocalVitalisColors.current
    val authState by viewModel.authState.collectAsState()
    val email by viewModel.email.collectAsState()
    val password by viewModel.password.collectAsState()
    val fullName by viewModel.fullName.collectAsState()
    val confirmPassword by viewModel.confirmPassword.collectAsState()
    val dateOfBirth by viewModel.dateOfBirth.collectAsState()
    val gender by viewModel.gender.collectAsState()
    val heightCm by viewModel.heightCm.collectAsState()
    val weightValue by viewModel.weightValue.collectAsState()
    val weightUnit by viewModel.weightUnit.collectAsState()

    var passwordVisible by remember { mutableStateOf(false) }
    var confirmPasswordVisible by remember { mutableStateOf(false) }
    var genderExpanded by remember { mutableStateOf(false) }
    var weightUnitExpanded by remember { mutableStateOf(false) }

    val snackbarHostState = remember { SnackbarHostState() }
    val focusManager = LocalFocusManager.current
    val context = LocalContext.current

    val isLoading = authState is AuthViewModel.AuthUiState.Loading
    val datePickerSeed = remember { Calendar.getInstance() }

    val datePickerDialog = remember(context) {
        DatePickerDialog(
            context,
            { _, year, month, dayOfMonth ->
                val isoDate = String.format(Locale.US, "%04d-%02d-%02d", year, month + 1, dayOfMonth)
                viewModel.updateDateOfBirth(isoDate)
            },
            datePickerSeed.get(Calendar.YEAR) - 25,
            datePickerSeed.get(Calendar.MONTH),
            datePickerSeed.get(Calendar.DAY_OF_MONTH),
        ).apply {
            datePicker.maxDate = System.currentTimeMillis()
        }
    }

    LaunchedEffect(authState) {
        when (authState) {
            is AuthViewModel.AuthUiState.Success -> {
                val response = (authState as AuthViewModel.AuthUiState.Success).authResponse
                onRegisterSuccess(response.userId)
            }

            is AuthViewModel.AuthUiState.Error -> {
                val errorMessage = (authState as AuthViewModel.AuthUiState.Error).message
                snackbarHostState.showSnackbar(errorMessage)
                viewModel.clearError()
            }

            else -> {
                // no-op for idle/loading
            }
        }
    }

    Box(
        modifier = modifier
            .fillMaxSize()
            .background(colors.bgApp),
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 28.dp)
                .imePadding(),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center,
        ) {
            Spacer(modifier = Modifier.height(32.dp))

            Box(
                modifier = Modifier
                    .size(56.dp)
                    .clip(RoundedCornerShape(14.dp))
                    .background(VitalisPrimaryLight),
                contentAlignment = Alignment.Center,
            ) {
                Icon(
                    imageVector = Icons.Outlined.MonitorHeart,
                    contentDescription = "Vitalis",
                    tint = VitalisPrimary,
                    modifier = Modifier.size(28.dp),
                )
            }

            Spacer(modifier = Modifier.height(24.dp))

            Text(
                text = "Create Account",
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.Bold,
                color = colors.textPrimary,
            )

            Spacer(modifier = Modifier.height(6.dp))

            Text(
                text = "Join Vitalis to manage your health",
                style = MaterialTheme.typography.bodyMedium,
                color = colors.textSecondary,
            )

            Spacer(modifier = Modifier.height(32.dp))

            AuthFieldLabel("Full Name")
            OutlinedTextField(
                value = fullName,
                onValueChange = { viewModel.updateFullName(it) },
                placeholder = { Text("Enter your full name", color = colors.textMuted) },
                singleLine = true,
                keyboardOptions = KeyboardOptions(
                    capitalization = KeyboardCapitalization.Words,
                    keyboardType = KeyboardType.Text,
                    imeAction = ImeAction.Next,
                ),
                keyboardActions = KeyboardActions(onNext = { focusManager.moveFocus(FocusDirection.Down) }),
                colors = authTextFieldColors(),
                shape = RoundedCornerShape(6.dp),
                modifier = Modifier.fillMaxWidth(),
                enabled = !isLoading,
            )

            Spacer(modifier = Modifier.height(14.dp))

            AuthFieldLabel("Email")
            OutlinedTextField(
                value = email,
                onValueChange = { viewModel.updateEmail(it) },
                placeholder = { Text("Enter your email", color = colors.textMuted) },
                singleLine = true,
                keyboardOptions = KeyboardOptions(
                    keyboardType = KeyboardType.Email,
                    imeAction = ImeAction.Next,
                ),
                keyboardActions = KeyboardActions(onNext = { focusManager.moveFocus(FocusDirection.Down) }),
                colors = authTextFieldColors(),
                shape = RoundedCornerShape(6.dp),
                modifier = Modifier.fillMaxWidth(),
                enabled = !isLoading,
            )

            Spacer(modifier = Modifier.height(14.dp))

            AuthFieldLabel("Date of Birth")
            OutlinedTextField(
                value = dateOfBirth,
                onValueChange = {},
                placeholder = { Text("Select date of birth", color = colors.textMuted) },
                singleLine = true,
                readOnly = true,
                trailingIcon = {
                    IconButton(onClick = { if (!isLoading) datePickerDialog.show() }) {
                        Icon(
                            imageVector = Icons.Outlined.DateRange,
                            contentDescription = "Pick date of birth",
                            tint = colors.textMuted,
                        )
                    }
                },
                colors = authTextFieldColors(),
                shape = RoundedCornerShape(6.dp),
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable(enabled = !isLoading) {
                        focusManager.clearFocus()
                        datePickerDialog.show()
                    },
                enabled = !isLoading,
            )

            Spacer(modifier = Modifier.height(14.dp))

            AuthFieldLabel("Gender")
            ExposedDropdownMenuBox(
                expanded = genderExpanded,
                onExpandedChange = { if (!isLoading) genderExpanded = !genderExpanded },
            ) {
                OutlinedTextField(
                    value = gender,
                    onValueChange = {},
                    readOnly = true,
                    singleLine = true,
                    trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = genderExpanded) },
                    colors = authTextFieldColors(),
                    shape = RoundedCornerShape(6.dp),
                    modifier = Modifier
                        .menuAnchor()
                        .fillMaxWidth(),
                    enabled = !isLoading,
                )
                DropdownMenu(
                    expanded = genderExpanded,
                    onDismissRequest = { genderExpanded = false },
                ) {
                    listOf("Male", "Female", "Other", "Prefer not to say").forEach { option ->
                        DropdownMenuItem(
                            text = { Text(option) },
                            onClick = {
                                viewModel.updateGender(option)
                                genderExpanded = false
                            },
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(14.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp),
                verticalAlignment = Alignment.Top,
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    AuthFieldLabel("Height (cm)")
                    OutlinedTextField(
                        value = heightCm,
                        onValueChange = { viewModel.updateHeightCm(it) },
                        placeholder = { Text("e.g. 170", color = colors.textMuted) },
                        singleLine = true,
                        keyboardOptions = KeyboardOptions(
                            keyboardType = KeyboardType.Decimal,
                            imeAction = ImeAction.Next,
                        ),
                        keyboardActions = KeyboardActions(onNext = { focusManager.moveFocus(FocusDirection.Right) }),
                        colors = authTextFieldColors(),
                        shape = RoundedCornerShape(6.dp),
                        modifier = Modifier.fillMaxWidth(),
                        enabled = !isLoading,
                    )
                }

                Column(modifier = Modifier.weight(1f)) {
                    AuthFieldLabel("Weight")
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        OutlinedTextField(
                            value = weightValue,
                            onValueChange = { viewModel.updateWeightValue(it) },
                            placeholder = { Text("70", color = colors.textMuted) },
                            singleLine = true,
                            keyboardOptions = KeyboardOptions(
                                keyboardType = KeyboardType.Decimal,
                                imeAction = ImeAction.Next,
                            ),
                            keyboardActions = KeyboardActions(onNext = { focusManager.moveFocus(FocusDirection.Down) }),
                            colors = authTextFieldColors(),
                            shape = RoundedCornerShape(6.dp),
                            modifier = Modifier.weight(0.58f),
                            enabled = !isLoading,
                        )

                        ExposedDropdownMenuBox(
                            expanded = weightUnitExpanded,
                            onExpandedChange = { if (!isLoading) weightUnitExpanded = !weightUnitExpanded },
                            modifier = Modifier.weight(0.42f),
                        ) {
                            OutlinedTextField(
                                value = weightUnit,
                                onValueChange = {},
                                readOnly = true,
                                singleLine = true,
                                trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = weightUnitExpanded) },
                                colors = authTextFieldColors(),
                                shape = RoundedCornerShape(6.dp),
                                modifier = Modifier
                                    .menuAnchor()
                                    .fillMaxWidth(),
                                enabled = !isLoading,
                            )
                            DropdownMenu(
                                expanded = weightUnitExpanded,
                                onDismissRequest = { weightUnitExpanded = false },
                            ) {
                                listOf("kg", "lbs").forEach { option ->
                                    DropdownMenuItem(
                                        text = { Text(option) },
                                        onClick = {
                                            viewModel.updateWeightUnit(option)
                                            weightUnitExpanded = false
                                        },
                                    )
                                }
                            }
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(14.dp))

            AuthFieldLabel("Password")
            OutlinedTextField(
                value = password,
                onValueChange = { viewModel.updatePassword(it) },
                placeholder = { Text("Create a password", color = colors.textMuted) },
                singleLine = true,
                visualTransformation = if (passwordVisible) VisualTransformation.None else PasswordVisualTransformation(),
                trailingIcon = {
                    IconButton(onClick = { passwordVisible = !passwordVisible }) {
                        Icon(
                            imageVector = if (passwordVisible) Icons.Filled.VisibilityOff else Icons.Filled.Visibility,
                            contentDescription = if (passwordVisible) "Hide password" else "Show password",
                            tint = colors.textMuted,
                        )
                    }
                },
                keyboardOptions = KeyboardOptions(
                    keyboardType = KeyboardType.Password,
                    imeAction = ImeAction.Next,
                ),
                keyboardActions = KeyboardActions(onNext = { focusManager.moveFocus(FocusDirection.Down) }),
                colors = authTextFieldColors(),
                shape = RoundedCornerShape(6.dp),
                modifier = Modifier.fillMaxWidth(),
                enabled = !isLoading,
            )

            Spacer(modifier = Modifier.height(14.dp))

            AuthFieldLabel("Confirm Password")
            OutlinedTextField(
                value = confirmPassword,
                onValueChange = { viewModel.updateConfirmPassword(it) },
                placeholder = { Text("Confirm your password", color = colors.textMuted) },
                singleLine = true,
                visualTransformation = if (confirmPasswordVisible) VisualTransformation.None else PasswordVisualTransformation(),
                trailingIcon = {
                    IconButton(onClick = { confirmPasswordVisible = !confirmPasswordVisible }) {
                        Icon(
                            imageVector = if (confirmPasswordVisible) Icons.Filled.VisibilityOff else Icons.Filled.Visibility,
                            contentDescription = if (confirmPasswordVisible) "Hide password" else "Show password",
                            tint = colors.textMuted,
                        )
                    }
                },
                keyboardOptions = KeyboardOptions(
                    keyboardType = KeyboardType.Password,
                    imeAction = ImeAction.Done,
                ),
                keyboardActions = KeyboardActions(
                    onDone = {
                        focusManager.clearFocus()
                        viewModel.register()
                    },
                ),
                colors = authTextFieldColors(),
                shape = RoundedCornerShape(6.dp),
                modifier = Modifier.fillMaxWidth(),
                enabled = !isLoading,
            )

            Spacer(modifier = Modifier.height(6.dp))

            Text(
                text = "Password must be at least 6 characters",
                style = MaterialTheme.typography.bodySmall,
                color = colors.textMuted,
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(start = 4.dp),
            )

            Spacer(modifier = Modifier.height(22.dp))

            Button(
                onClick = {
                    focusManager.clearFocus()
                    viewModel.register()
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(50.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = VitalisPrimary,
                    disabledContainerColor = VitalisPrimary.copy(alpha = 0.5f),
                    contentColor = Color.White,
                ),
                shape = RoundedCornerShape(6.dp),
                enabled = !isLoading,
            ) {
                if (isLoading) {
                    CircularProgressIndicator(
                        color = Color.White,
                        strokeWidth = 2.dp,
                        modifier = Modifier.size(22.dp),
                    )
                } else {
                    Text(
                        text = "Create Account",
                        style = MaterialTheme.typography.labelLarge,
                        fontWeight = FontWeight.SemiBold,
                        color = Color.White,
                    )
                }
            }

            Spacer(modifier = Modifier.height(24.dp))

            TextButton(
                onClick = {
                    viewModel.clearForm()
                    viewModel.resetState()
                    onNavigateToLogin()
                },
                enabled = !isLoading,
            ) {
                Text(
                    text = "Already have an account? ",
                    style = MaterialTheme.typography.bodyMedium,
                    color = colors.textSecondary,
                )
                Text(
                    text = "Log in",
                    style = MaterialTheme.typography.bodyMedium,
                    fontWeight = FontWeight.SemiBold,
                    color = VitalisPrimary,
                )
            }

            Spacer(modifier = Modifier.height(32.dp))
        }

        SnackbarHost(
            hostState = snackbarHostState,
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .padding(16.dp),
        ) { data ->
            Snackbar(
                snackbarData = data,
                containerColor = VitalisDanger,
                contentColor = Color.White,
                shape = RoundedCornerShape(10.dp),
            )
        }
    }
}

@Composable
private fun AuthFieldLabel(text: String) {
    val colors = LocalVitalisColors.current
    Text(
        text = text,
        style = MaterialTheme.typography.labelMedium,
        fontWeight = FontWeight.SemiBold,
        color = colors.textPrimary,
        modifier = Modifier
            .fillMaxWidth()
            .padding(bottom = 6.dp),
    )
}

@Composable
private fun authTextFieldColors() = OutlinedTextFieldDefaults.colors(
    focusedContainerColor = LocalVitalisColors.current.bgInput,
    unfocusedContainerColor = LocalVitalisColors.current.bgInput,
    focusedBorderColor = VitalisPrimary,
    unfocusedBorderColor = MaterialTheme.colorScheme.outline,
    focusedTextColor = LocalVitalisColors.current.textPrimary,
    unfocusedTextColor = LocalVitalisColors.current.textPrimary,
    disabledTextColor = LocalVitalisColors.current.textMuted,
    cursorColor = LocalVitalisColors.current.textPrimary,
    focusedPlaceholderColor = LocalVitalisColors.current.textMuted,
    unfocusedPlaceholderColor = LocalVitalisColors.current.textMuted,
)
