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
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.outlined.DateRange
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.ExposedDropdownMenuDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
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
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import com.vitalis.health.data.model.UserProfile
import com.vitalis.health.data.model.UserUpdateRequest
import com.vitalis.health.ui.AuthViewModel
import com.vitalis.health.ui.theme.LocalVitalisColors
import com.vitalis.health.ui.theme.VitalisPrimary
import java.text.ParseException
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Date
import java.util.Locale
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ProfileEditScreen(
    viewModel: AuthViewModel,
    userId: String,
    currentProfile: UserProfile?,
    onNavigateBack: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val colors = LocalVitalisColors.current
    val profileState by viewModel.profileState.collectAsState()
    val cachedProfile by viewModel.currentUserProfile.collectAsState()
    val effectiveProfile = currentProfile ?: cachedProfile

    val snackbarHostState = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()
    val focusManager = LocalFocusManager.current
    val context = LocalContext.current

    var fullName by remember { mutableStateOf("") }
    var phone by remember { mutableStateOf("") }
    var dateOfBirth by remember { mutableStateOf("") }
    var gender by remember { mutableStateOf("Prefer not to say") }
    var city by remember { mutableStateOf("") }
    var state by remember { mutableStateOf("") }
    var country by remember { mutableStateOf("") }
    var bloodGroup by remember { mutableStateOf("") }
    var heightCm by remember { mutableStateOf("") }
    var weightKg by remember { mutableStateOf("") }
    var genderExpanded by remember { mutableStateOf(false) }

    LaunchedEffect(userId, effectiveProfile?.id) {
        if (effectiveProfile == null) {
            viewModel.fetchUserProfile(userId, forceRefresh = true)
        }
    }

    LaunchedEffect(effectiveProfile?.id) {
        effectiveProfile?.let { profile ->
            fullName = profile.fullName
            phone = profile.phone.orEmpty()
            dateOfBirth = profile.dateOfBirth.orEmpty()
            gender = when (profile.gender?.lowercase()) {
                "male" -> "Male"
                "female" -> "Female"
                "other" -> "Other"
                else -> "Prefer not to say"
            }
            city = profile.city.orEmpty()
            state = profile.state.orEmpty()
            country = profile.country.orEmpty()
            bloodGroup = profile.bloodGroup.orEmpty()
            heightCm = profile.heightCm?.toString().orEmpty()
            weightKg = profile.weightKg?.toString().orEmpty()
        }
    }

    LaunchedEffect(profileState) {
        when (profileState) {
            is AuthViewModel.ProfileUiState.Success -> {
                snackbarHostState.showSnackbar("Profile saved successfully")
                viewModel.resetProfileState()
                onNavigateBack()
            }

            is AuthViewModel.ProfileUiState.Error -> {
                val errorMessage = (profileState as AuthViewModel.ProfileUiState.Error).message
                snackbarHostState.showSnackbar(errorMessage)
                viewModel.resetProfileState()
            }

            else -> {
                // no-op
            }
        }
    }

    val isSaving = profileState is AuthViewModel.ProfileUiState.Loading

    val calendarSeed = remember { Calendar.getInstance() }
    val datePickerDialog = remember(context) {
        DatePickerDialog(
            context,
            { _, year, month, dayOfMonth ->
                dateOfBirth = String.format(Locale.US, "%04d-%02d-%02d", year, month + 1, dayOfMonth)
            },
            calendarSeed.get(Calendar.YEAR) - 25,
            calendarSeed.get(Calendar.MONTH),
            calendarSeed.get(Calendar.DAY_OF_MONTH),
        ).apply {
            datePicker.maxDate = System.currentTimeMillis()
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = "Edit Profile",
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
        snackbarHost = { SnackbarHost(snackbarHostState) },
        modifier = modifier,
    ) { paddingValues ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .background(colors.bgApp),
        ) {
            if (effectiveProfile == null && isSaving) {
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
                    .padding(horizontal = 20.dp, vertical = 16.dp)
                    .imePadding(),
                verticalArrangement = Arrangement.spacedBy(14.dp),
            ) {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                    shape = RoundedCornerShape(16.dp),
                ) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(4.dp),
                    ) {
                        Text(
                            text = "Update your health profile",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                            color = colors.textPrimary,
                        )
                        Text(
                            text = "Keep this information current to improve AI insights and clinician summaries.",
                            style = MaterialTheme.typography.bodySmall,
                            color = colors.textSecondary,
                        )
                    }
                }

                ProfileField(
                    label = "Full Name",
                    value = fullName,
                    onValueChange = { fullName = it },
                    placeholder = "Enter your full name",
                    enabled = !isSaving,
                    imeAction = ImeAction.Next,
                    onNext = { focusManager.moveFocus(androidx.compose.ui.focus.FocusDirection.Down) },
                )

                ProfileField(
                    label = "Phone",
                    value = phone,
                    onValueChange = { phone = it },
                    placeholder = "Enter phone number",
                    keyboardType = KeyboardType.Phone,
                    enabled = !isSaving,
                    imeAction = ImeAction.Next,
                    onNext = { focusManager.moveFocus(androidx.compose.ui.focus.FocusDirection.Down) },
                )

                Text(
                    text = "Date of Birth",
                    style = MaterialTheme.typography.labelMedium,
                    fontWeight = FontWeight.SemiBold,
                    color = colors.textPrimary,
                )
                OutlinedTextField(
                    value = dateOfBirth,
                    onValueChange = {},
                    readOnly = true,
                    singleLine = true,
                    placeholder = { Text("Select date of birth", color = colors.textMuted) },
                    trailingIcon = {
                        IconButton(onClick = { if (!isSaving) datePickerDialog.show() }) {
                            Icon(
                                imageVector = Icons.Outlined.DateRange,
                                contentDescription = "Select date of birth",
                                tint = colors.textMuted,
                            )
                        }
                    },
                    colors = profileFieldColors(),
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable(enabled = !isSaving) {
                            focusManager.clearFocus()
                            datePickerDialog.show()
                        },
                    enabled = !isSaving,
                )

                Text(
                    text = "Gender",
                    style = MaterialTheme.typography.labelMedium,
                    fontWeight = FontWeight.SemiBold,
                    color = colors.textPrimary,
                )
                ExposedDropdownMenuBox(
                    expanded = genderExpanded,
                    onExpandedChange = { if (!isSaving) genderExpanded = !genderExpanded },
                ) {
                    OutlinedTextField(
                        value = gender,
                        onValueChange = {},
                        readOnly = true,
                        singleLine = true,
                        trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = genderExpanded) },
                        colors = profileFieldColors(),
                        modifier = Modifier
                            .menuAnchor()
                            .fillMaxWidth(),
                        enabled = !isSaving,
                    )
                    DropdownMenu(
                        expanded = genderExpanded,
                        onDismissRequest = { genderExpanded = false },
                    ) {
                        listOf("Male", "Female", "Other", "Prefer not to say").forEach { option ->
                            DropdownMenuItem(
                                text = { Text(option) },
                                onClick = {
                                    gender = option
                                    genderExpanded = false
                                },
                            )
                        }
                    }
                }

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        ProfileField(
                            label = "Height (cm)",
                            value = heightCm,
                            onValueChange = { heightCm = it },
                            placeholder = "170",
                            keyboardType = KeyboardType.Decimal,
                            enabled = !isSaving,
                            imeAction = ImeAction.Next,
                            onNext = { focusManager.moveFocus(androidx.compose.ui.focus.FocusDirection.Right) },
                        )
                    }

                    Column(modifier = Modifier.weight(1f)) {
                        ProfileField(
                            label = "Weight (kg)",
                            value = weightKg,
                            onValueChange = { weightKg = it },
                            placeholder = "70",
                            keyboardType = KeyboardType.Decimal,
                            enabled = !isSaving,
                            imeAction = ImeAction.Next,
                            onNext = { focusManager.moveFocus(androidx.compose.ui.focus.FocusDirection.Down) },
                        )
                    }
                }

                ProfileField(
                    label = "Blood Group",
                    value = bloodGroup,
                    onValueChange = { bloodGroup = it.uppercase(Locale.US) },
                    placeholder = "A+, O-, AB+",
                    enabled = !isSaving,
                    imeAction = ImeAction.Next,
                    onNext = { focusManager.moveFocus(androidx.compose.ui.focus.FocusDirection.Down) },
                )

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        ProfileField(
                            label = "City",
                            value = city,
                            onValueChange = { city = it },
                            placeholder = "City",
                            enabled = !isSaving,
                            imeAction = ImeAction.Next,
                            onNext = { focusManager.moveFocus(androidx.compose.ui.focus.FocusDirection.Right) },
                        )
                    }
                    Column(modifier = Modifier.weight(1f)) {
                        ProfileField(
                            label = "State",
                            value = state,
                            onValueChange = { state = it },
                            placeholder = "State",
                            enabled = !isSaving,
                            imeAction = ImeAction.Next,
                            onNext = { focusManager.moveFocus(androidx.compose.ui.focus.FocusDirection.Down) },
                        )
                    }
                }

                ProfileField(
                    label = "Country",
                    value = country,
                    onValueChange = { country = it },
                    placeholder = "Country",
                    enabled = !isSaving,
                    imeAction = ImeAction.Done,
                    onNext = { focusManager.clearFocus() },
                )

                Spacer(modifier = Modifier.height(4.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    OutlinedButton(
                        onClick = onNavigateBack,
                        enabled = !isSaving,
                        shape = RoundedCornerShape(12.dp),
                        modifier = Modifier
                            .weight(1f)
                            .height(52.dp),
                    ) {
                        Text("Cancel")
                    }

                    Button(
                        onClick = {
                            focusManager.clearFocus()

                            val parsedDob = dateOfBirth.trim().takeIf { it.isNotBlank() }
                            if (parsedDob != null) {
                                val isFutureDob = try {
                                    val parser = SimpleDateFormat("yyyy-MM-dd", Locale.US).apply {
                                        isLenient = false
                                    }
                                    val parsedDate = parser.parse(parsedDob)
                                    parsedDate == null || parsedDate.after(Date())
                                } catch (_: ParseException) {
                                    true
                                }

                                if (isFutureDob) {
                                    scope.launch {
                                        snackbarHostState.showSnackbar("Date of birth cannot be in the future")
                                    }
                                    return@Button
                                }
                            }

                            val updateRequest = UserUpdateRequest(
                                fullName = fullName.trim().takeIf { it.isNotBlank() },
                                phone = phone.trim().takeIf { it.isNotBlank() },
                                dateOfBirth = parsedDob,
                                gender = when (gender.lowercase(Locale.US)) {
                                    "male" -> "male"
                                    "female" -> "female"
                                    "other" -> "other"
                                    else -> null
                                },
                                city = city.trim().takeIf { it.isNotBlank() },
                                state = state.trim().takeIf { it.isNotBlank() },
                                country = country.trim().takeIf { it.isNotBlank() },
                                bloodGroup = bloodGroup.trim().takeIf { it.isNotBlank() },
                                heightCm = heightCm.trim().toDoubleOrNull(),
                                weightKg = weightKg.trim().toDoubleOrNull(),
                            )
                            viewModel.updateUserProfile(userId, updateRequest)
                        },
                        enabled = !isSaving,
                        colors = ButtonDefaults.buttonColors(
                            containerColor = VitalisPrimary,
                            contentColor = Color.White,
                        ),
                        shape = RoundedCornerShape(12.dp),
                        modifier = Modifier
                            .weight(1f)
                            .height(52.dp),
                    ) {
                        if (isSaving) {
                            CircularProgressIndicator(
                                color = Color.White,
                                strokeWidth = 2.dp,
                                modifier = Modifier.size(20.dp),
                            )
                        } else {
                            Icon(
                                imageVector = Icons.Default.Check,
                                contentDescription = null,
                                modifier = Modifier.size(18.dp),
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text("Save")
                        }
                    }
                }

                Spacer(modifier = Modifier.height(18.dp))
            }
        }
    }
}

@Composable
private fun ProfileField(
    label: String,
    value: String,
    onValueChange: (String) -> Unit,
    placeholder: String,
    keyboardType: KeyboardType = KeyboardType.Text,
    imeAction: ImeAction = ImeAction.Next,
    enabled: Boolean = true,
    onNext: () -> Unit = {},
) {
    val colors = LocalVitalisColors.current
    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Text(
            text = label,
            style = MaterialTheme.typography.labelMedium,
            fontWeight = FontWeight.SemiBold,
            color = colors.textPrimary,
        )

        OutlinedTextField(
            value = value,
            onValueChange = onValueChange,
            placeholder = { Text(placeholder, color = colors.textMuted) },
            singleLine = true,
            keyboardOptions = KeyboardOptions(
                keyboardType = keyboardType,
                imeAction = imeAction,
            ),
            keyboardActions = KeyboardActions(
                onNext = { onNext() },
                onDone = { onNext() },
            ),
            colors = profileFieldColors(),
            shape = RoundedCornerShape(10.dp),
            modifier = Modifier.fillMaxWidth(),
            enabled = enabled,
        )
    }
}

@Composable
private fun profileFieldColors() = OutlinedTextFieldDefaults.colors(
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
