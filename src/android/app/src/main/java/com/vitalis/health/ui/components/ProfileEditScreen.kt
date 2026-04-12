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
import androidx.compose.foundation.layout.navigationBarsPadding
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
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.lifecycle.compose.collectAsStateWithLifecycle
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
    val profileState by viewModel.profileState.collectAsStateWithLifecycle()
    val cachedProfile by viewModel.currentUserProfile.collectAsStateWithLifecycle()
    val effectiveProfile = when {
        cachedProfile?.id == userId -> cachedProfile
        currentProfile?.id == userId -> currentProfile
        else -> null
    }

    val snackbarHostState = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()
    val focusManager = LocalFocusManager.current
    val context = LocalContext.current

    var isSubmitting by remember(userId) { mutableStateOf(false) }
    var isFormDirty by remember(userId) { mutableStateOf(false) }
    var lastBoundProfileHash by remember(userId) { mutableStateOf<Int?>(null) }

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

    LaunchedEffect(userId) {
        isSubmitting = false
        isFormDirty = false
        lastBoundProfileHash = null
        viewModel.resetProfileState()
        viewModel.fetchUserProfile(
            userId = userId,
            forceRefresh = currentProfile?.id == userId,
        )
    }

    LaunchedEffect(effectiveProfile) {
        effectiveProfile?.let { profile ->
            val incomingHash = profile.hashCode()
            val shouldRebindForm =
                lastBoundProfileHash == null || (!isFormDirty && lastBoundProfileHash != incomingHash)

            if (shouldRebindForm) {
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
                isFormDirty = false
                lastBoundProfileHash = incomingHash
            }
        }
    }

    LaunchedEffect(profileState) {
        when (profileState) {
            is AuthViewModel.ProfileUiState.Success -> {
                isSubmitting = false
                snackbarHostState.showSnackbar("Profile saved successfully")
                viewModel.resetProfileState()
                onNavigateBack()
            }

            is AuthViewModel.ProfileUiState.Error -> {
                isSubmitting = false
                val errorMessage = (profileState as AuthViewModel.ProfileUiState.Error).message
                snackbarHostState.showSnackbar(errorMessage)
                viewModel.resetProfileState()
            }

            else -> {
                if (profileState !is AuthViewModel.ProfileUiState.Loading) {
                    isSubmitting = false
                }
            }
        }
    }

    val isSaving = isSubmitting

    val calendarSeed = remember { Calendar.getInstance() }
    val datePickerDialog = remember(context) {
        DatePickerDialog(
            context,
            { _, year, month, dayOfMonth ->
                isFormDirty = true
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
            if (effectiveProfile == null) {
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
                    .imePadding()
                    .navigationBarsPadding()
                    .padding(horizontal = 20.dp, vertical = 16.dp),
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
                    onValueChange = {
                        isFormDirty = true
                        fullName = it
                    },
                    placeholder = "Enter your full name",
                    enabled = !isSaving,
                    imeAction = ImeAction.Next,
                    onNext = { focusManager.moveFocus(androidx.compose.ui.focus.FocusDirection.Down) },
                )

                ProfileField(
                    label = "Phone",
                    value = phone,
                    onValueChange = {
                        isFormDirty = true
                        phone = sanitizePhoneInput(it)
                    },
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
                    onExpandedChange = { expanded ->
                        if (!isSaving) {
                            focusManager.clearFocus(force = true)
                            genderExpanded = expanded
                        }
                    },
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
                                    isFormDirty = true
                                    gender = option
                                    focusManager.clearFocus(force = true)
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
                            onValueChange = {
                                isFormDirty = true
                                heightCm = sanitizeDecimalInput(it)
                            },
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
                            onValueChange = {
                                isFormDirty = true
                                weightKg = sanitizeDecimalInput(it)
                            },
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
                    onValueChange = {
                        isFormDirty = true
                        bloodGroup = sanitizeBloodGroupInput(it)
                    },
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
                            onValueChange = {
                                isFormDirty = true
                                city = it
                            },
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
                            onValueChange = {
                                isFormDirty = true
                                state = it
                            },
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
                    onValueChange = {
                        isFormDirty = true
                        country = it
                    },
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
                                    parsedDate == null ||
                                        parser.format(parsedDate) != parsedDob ||
                                        parsedDate.after(Date())
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

                            val (normalizedPhone, phoneError) = validatePhoneForPayload(phone)
                            if (phoneError != null) {
                                scope.launch {
                                    snackbarHostState.showSnackbar(phoneError)
                                }
                                return@Button
                            }

                            val (validatedHeightCm, heightError) = parseOptionalBoundedNumber(
                                rawValue = heightCm,
                                fieldLabel = "Height",
                                min = 30.0,
                                max = 300.0,
                            )
                            if (heightError != null) {
                                scope.launch {
                                    snackbarHostState.showSnackbar(heightError)
                                }
                                return@Button
                            }

                            val (validatedWeightKg, weightError) = parseOptionalBoundedNumber(
                                rawValue = weightKg,
                                fieldLabel = "Weight",
                                min = 1.0,
                                max = 500.0,
                            )
                            if (weightError != null) {
                                scope.launch {
                                    snackbarHostState.showSnackbar(weightError)
                                }
                                return@Button
                            }

                            val normalizedBloodGroup = bloodGroup.trim().takeIf { it.isNotBlank() }
                            if (normalizedBloodGroup != null) {
                                val validBloodGroups = listOf("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-")
                                if (normalizedBloodGroup !in validBloodGroups) {
                                    scope.launch {
                                        snackbarHostState.showSnackbar("Please enter a valid blood group (e.g., A+, O-)")
                                    }
                                    return@Button
                                }
                            }

                            isSubmitting = true

                            val updateRequest = UserUpdateRequest(
                                fullName = fullName.trim().takeIf { it.isNotBlank() },
                                phone = normalizedPhone,
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
                                bloodGroup = normalizedBloodGroup,
                                heightCm = validatedHeightCm,
                                weightKg = validatedWeightKg,
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

private fun sanitizePhoneInput(input: String): String {
    return input
        .filter { it.isDigit() || it == '+' || it == '-' || it == '(' || it == ')' || it == ' ' }
        .take(20)
}

private fun sanitizeDecimalInput(input: String): String {
    val result = StringBuilder()
    var seenDot = false
    input.forEach { char ->
        when {
            char.isDigit() -> result.append(char)
            char == '.' && !seenDot -> {
                seenDot = true
                result.append(char)
            }
        }
    }
    return result.toString().take(8)
}

private fun sanitizeBloodGroupInput(input: String): String {
    return input
        .uppercase(Locale.US)
        .filter { it in "ABO+-" }
        .take(3)
}

private fun validatePhoneForPayload(rawPhone: String): Pair<String?, String?> {
    val normalized = rawPhone.trim().replace(Regex("\\s+"), " ")
    if (normalized.isBlank()) {
        return null to null
    }
    if (normalized.length > 20) {
        return null to "Phone number must be 20 characters or fewer"
    }
    val digitCount = normalized.count { it.isDigit() }
    if (digitCount !in 6..15) {
        return null to "Please enter a valid phone number"
    }
    return normalized to null
}

private fun parseOptionalBoundedNumber(
    rawValue: String,
    fieldLabel: String,
    min: Double,
    max: Double,
): Pair<Double?, String?> {
    val normalized = rawValue.trim()
    if (normalized.isEmpty()) {
        return null to null
    }

    val parsed = normalized.toDoubleOrNull()
        ?: return null to "$fieldLabel must be a valid number"

    if (parsed.isNaN() || parsed.isInfinite()) {
        return null to "$fieldLabel must be a valid number"
    }
    if (parsed <= 0.0) {
        return null to "$fieldLabel must be greater than 0"
    }
    if (parsed < min || parsed > max) {
        return null to "$fieldLabel must be between ${min.toInt()} and ${max.toInt()}"
    }
    return parsed to null
}
