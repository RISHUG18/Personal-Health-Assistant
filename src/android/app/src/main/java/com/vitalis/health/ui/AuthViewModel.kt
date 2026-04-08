package com.vitalis.health.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.vitalis.health.data.local.TokenManager
import com.vitalis.health.data.model.AuthResponse
import com.vitalis.health.data.model.UserProfile
import com.vitalis.health.data.model.UserUpdateRequest
import com.vitalis.health.data.network.ApiResult
import com.vitalis.health.data.repository.HealthRepository
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.text.ParseException
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * ViewModel for Authentication screens (Login and Register).
 *
 * Manages:
 * - Form input state (email, password, name)
 * - UI state (Idle, Loading, Success, Error)
 * - API calls for login/register
 * - Token persistence on successful authentication
 * - User profile updates and account deletion
 *
 * Exposes [authState] as observable [StateFlow] that drives the UI.
 */
class AuthViewModel(
    private val repository: HealthRepository,
    private val tokenManager: TokenManager
) : ViewModel() {

    /**
     * Represents the possible states of the authentication flow.
     */
    sealed class AuthUiState {
        /** Initial state, no operation in progress. */
        data object Idle : AuthUiState()

        /** Authentication request is in progress. */
        data object Loading : AuthUiState()

        /** Authentication successful, contains user info. */
        data class Success(val authResponse: AuthResponse) : AuthUiState()

        /** Authentication failed with an error message. */
        data class Error(val message: String) : AuthUiState()
    }

    /**
     * Represents the possible states of user profile operations.
     */
    sealed class ProfileUiState {
        /** Initial state, no operation in progress. */
        data object Idle : ProfileUiState()

        /** Profile operation is in progress. */
        data object Loading : ProfileUiState()

        /** Profile operation successful. */
        data class Success(val userProfile: UserProfile) : ProfileUiState()

        /** Profile operation failed with an error message. */
        data class Error(val message: String) : ProfileUiState()

        /** Account deletion successful. */
        data object Deleted : ProfileUiState()
    }

    private val _authState = MutableStateFlow<AuthUiState>(AuthUiState.Idle)
    val authState: StateFlow<AuthUiState> = _authState.asStateFlow()

    private val _profileState = MutableStateFlow<ProfileUiState>(ProfileUiState.Idle)
    val profileState: StateFlow<ProfileUiState> = _profileState.asStateFlow()

    // Increments whenever auth session boundaries change (login/register/logout/delete).
    private val _sessionVersion = MutableStateFlow(0)
    val sessionVersion: StateFlow<Int> = _sessionVersion.asStateFlow()

    // ── Form Input State ──────────────────────────────────

    private val _email = MutableStateFlow("")
    val email: StateFlow<String> = _email.asStateFlow()

    private val _password = MutableStateFlow("")
    val password: StateFlow<String> = _password.asStateFlow()

    private val _fullName = MutableStateFlow("")
    val fullName: StateFlow<String> = _fullName.asStateFlow()

    private val _confirmPassword = MutableStateFlow("")
    val confirmPassword: StateFlow<String> = _confirmPassword.asStateFlow()

    private val _dateOfBirth = MutableStateFlow("")
    val dateOfBirth: StateFlow<String> = _dateOfBirth.asStateFlow()

    private val _gender = MutableStateFlow("Prefer not to say")
    val gender: StateFlow<String> = _gender.asStateFlow()

    private val _heightCm = MutableStateFlow("")
    val heightCm: StateFlow<String> = _heightCm.asStateFlow()

    private val _weightValue = MutableStateFlow("")
    val weightValue: StateFlow<String> = _weightValue.asStateFlow()

    private val _weightUnit = MutableStateFlow("kg")
    val weightUnit: StateFlow<String> = _weightUnit.asStateFlow()

    private val _currentUserProfile = MutableStateFlow<UserProfile?>(null)
    val currentUserProfile: StateFlow<UserProfile?> = _currentUserProfile.asStateFlow()
    private var profileFetchJob: Job? = null

    // ── Input Setters ─────────────────────────────────────

    fun updateEmail(value: String) {
        _email.value = value
    }

    fun updatePassword(value: String) {
        _password.value = value
    }

    fun updateFullName(value: String) {
        _fullName.value = value
    }

    fun updateConfirmPassword(value: String) {
        _confirmPassword.value = value
    }

    fun updateDateOfBirth(value: String) {
        _dateOfBirth.value = value
    }

    fun updateGender(value: String) {
        _gender.value = value
    }

    fun updateHeightCm(value: String) {
        _heightCm.value = value
    }

    fun updateWeightValue(value: String) {
        _weightValue.value = value
    }

    fun updateWeightUnit(value: String) {
        _weightUnit.value = value
    }

    // ── Authentication Actions ────────────────────────────

    /**
     * Attempt to log in with current email and password.
     */
    fun login() {
        val currentEmail = _email.value.trim()
        val currentPassword = _password.value

        // Basic validation
        if (currentEmail.isBlank()) {
            _authState.value = AuthUiState.Error("Please enter your email")
            return
        }
        if (currentPassword.isBlank()) {
            _authState.value = AuthUiState.Error("Please enter your password")
            return
        }
        if (!isValidEmail(currentEmail)) {
            _authState.value = AuthUiState.Error("Please enter a valid email address")
            return
        }

        _authState.value = AuthUiState.Loading

        viewModelScope.launch {
            when (val result = repository.login(currentEmail, currentPassword)) {
                is ApiResult.Success -> {
                    // Save tokens to TokenManager
                    tokenManager.saveAuthData(
                        accessToken = result.data.accessToken,
                        refreshToken = result.data.refreshToken,
                        userId = result.data.userId
                    )
                    _sessionVersion.value = _sessionVersion.value + 1
                    _authState.value = AuthUiState.Success(result.data)
                }
                is ApiResult.Error -> {
                    _authState.value = AuthUiState.Error(result.message)
                }
            }
        }
    }

    /**
     * Attempt to register with current email, password, and full name.
     */
    fun register() {
        val currentEmail = _email.value.trim()
        val currentPassword = _password.value
        val currentConfirmPassword = _confirmPassword.value
        val currentFullName = _fullName.value.trim()
        val currentDateOfBirth = _dateOfBirth.value.trim()
        val selectedGender = _gender.value
        val currentHeightCm = _heightCm.value.trim().toDoubleOrNull()
        val normalizedWeightKg = normalizeWeightToKg(_weightValue.value.trim(), _weightUnit.value)

        // Validation
        if (currentFullName.isBlank()) {
            _authState.value = AuthUiState.Error("Please enter your full name")
            return
        }
        if (currentEmail.isBlank()) {
            _authState.value = AuthUiState.Error("Please enter your email")
            return
        }
        if (!isValidEmail(currentEmail)) {
            _authState.value = AuthUiState.Error("Please enter a valid email address")
            return
        }
        if (currentPassword.isBlank()) {
            _authState.value = AuthUiState.Error("Please enter a password")
            return
        }
        if (currentPassword.length < 6) {
            _authState.value = AuthUiState.Error("Password must be at least 6 characters")
            return
        }
        if (currentPassword != currentConfirmPassword) {
            _authState.value = AuthUiState.Error("Passwords do not match")
            return
        }
        if (currentDateOfBirth.isBlank()) {
            _authState.value = AuthUiState.Error("Please select your date of birth")
            return
        }
        val dateParser = SimpleDateFormat("yyyy-MM-dd", Locale.US).apply {
            isLenient = false
        }
        val dob = try {
            dateParser.parse(currentDateOfBirth)
        } catch (_: ParseException) {
            _authState.value = AuthUiState.Error("Date of birth must be in YYYY-MM-DD format")
            return
        }
        if (dob == null || dateParser.format(dob) != currentDateOfBirth) {
            _authState.value = AuthUiState.Error("Date of birth must be in YYYY-MM-DD format")
            return
        }
        if (dob.after(Date())) {
            _authState.value = AuthUiState.Error("Date of birth cannot be in the future")
            return
        }

        _authState.value = AuthUiState.Loading

        viewModelScope.launch {
            when (val result = repository.register(
                email = currentEmail,
                password = currentPassword,
                fullName = currentFullName,
                dateOfBirth = currentDateOfBirth,
                gender = normalizeGenderForBackend(selectedGender),
                heightCm = currentHeightCm,
                weightKg = normalizedWeightKg,
            )) {
                is ApiResult.Success -> {
                    // Save tokens to TokenManager
                    tokenManager.saveAuthData(
                        accessToken = result.data.accessToken,
                        refreshToken = result.data.refreshToken,
                        userId = result.data.userId
                    )
                    _sessionVersion.value = _sessionVersion.value + 1
                    _authState.value = AuthUiState.Success(result.data)
                    fetchUserProfile(result.data.userId, forceRefresh = true)
                }
                is ApiResult.Error -> {
                    _authState.value = AuthUiState.Error(result.message)
                }
            }
        }
    }

    // ── User Profile Management ───────────────────────────

    /** Fetch and cache the current profile for [userId]. */
    fun fetchUserProfile(userId: String, forceRefresh: Boolean = false) {
        if (!forceRefresh && _currentUserProfile.value?.id == userId) {
            return
        }

        if (profileFetchJob?.isActive == true) {
            return // Prevent duplicate concurrent fetches
        }

        _profileState.value = ProfileUiState.Loading

        profileFetchJob = viewModelScope.launch {
            try {
                when (val result = repository.getUserProfile(userId)) {
                    is ApiResult.Success -> {
                        _currentUserProfile.value = result.data
                        _profileState.value = ProfileUiState.Idle
                    }
                    is ApiResult.Error -> {
                        _profileState.value = ProfileUiState.Error(result.message)
                    }
                }
            } finally {
                profileFetchJob = null
                if (_profileState.value is ProfileUiState.Loading) {
                    _profileState.value = ProfileUiState.Idle
                }
            }
        }
    }

    /**
     * Update the user profile for the given [userId].
     * [updateRequest] contains the fields to be updated.
     */
    fun updateUserProfile(userId: String, updateRequest: UserUpdateRequest) {
        _profileState.value = ProfileUiState.Loading

        viewModelScope.launch {
            when (val result = repository.updateUser(userId, updateRequest)) {
                is ApiResult.Success -> {
                    _currentUserProfile.value = result.data
                    _profileState.value = ProfileUiState.Success(result.data)
                }
                is ApiResult.Error -> {
                    _profileState.value = ProfileUiState.Error(result.message)
                }
            }
        }
    }

    /**
     * Delete the user account for the given [userId].
     * On success, clears all stored tokens/session data.
     */
    fun deleteUser(userId: String) {
        _profileState.value = ProfileUiState.Loading

        viewModelScope.launch {
            when (val result = repository.deleteUser(userId)) {
                is ApiResult.Success -> {
                    // Clear stored tokens/session data
                    tokenManager.clearAuthData()
                    _currentUserProfile.value = null
                    _sessionVersion.value = _sessionVersion.value + 1
                    _profileState.value = ProfileUiState.Deleted
                }
                is ApiResult.Error -> {
                    _profileState.value = ProfileUiState.Error(result.message)
                }
            }
        }
    }

    /**
     * Fetch a user profile by email address.
     * Useful for checking if a user exists or retrieving profile info.
     */
    fun getUserByEmail(email: String) {
        _profileState.value = ProfileUiState.Loading

        viewModelScope.launch {
            when (val result = repository.getUserByEmail(email)) {
                is ApiResult.Success -> {
                    _profileState.value = ProfileUiState.Success(result.data)
                }
                is ApiResult.Error -> {
                    _profileState.value = ProfileUiState.Error(result.message)
                }
            }
        }
    }

    /**
     * Reset profile state to Idle.
     */
    fun resetProfileState() {
        _profileState.value = ProfileUiState.Idle
    }

    /**
     * Clear the current error state and return to Idle.
     */
    fun clearError() {
        if (_authState.value is AuthUiState.Error) {
            _authState.value = AuthUiState.Idle
        }
    }

    /**
     * Reset the auth state to Idle (e.g., when navigating away from auth screens).
     */
    fun resetState() {
        _authState.value = AuthUiState.Idle
    }

    /**
     * Clear all form inputs.
     */
    fun clearForm() {
        _email.value = ""
        _password.value = ""
        _fullName.value = ""
        _confirmPassword.value = ""
        _dateOfBirth.value = ""
        _gender.value = "Prefer not to say"
        _heightCm.value = ""
        _weightValue.value = ""
        _weightUnit.value = "kg"
    }

    /**
     * Check if user is already logged in.
     */
    fun isLoggedIn(): Boolean = tokenManager.isLoggedIn

    /**
     * Get the stored user ID (if logged in).
     */
    fun getUserId(): String? = tokenManager.userId

    /**
     * Log out the user by clearing stored tokens.
     */
    fun logout() {
        profileFetchJob?.cancel()
        profileFetchJob = null
        tokenManager.clearAuthData()
        _currentUserProfile.value = null
        _sessionVersion.value = _sessionVersion.value + 1
        clearForm()
        _authState.value = AuthUiState.Idle
        _profileState.value = ProfileUiState.Idle
    }

    // ── Validation Helpers ────────────────────────────────

    private fun isValidEmail(email: String): Boolean {
        // Use a more permissive regex that accepts common email formats
        // including test emails with underscores
        val emailRegex = "^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$".toRegex()
        return emailRegex.matches(email)
    }

    private fun normalizeGenderForBackend(uiGender: String): String? {
        return when (uiGender.trim().lowercase()) {
            "male" -> "male"
            "female" -> "female"
            "other" -> "other"
            else -> null
        }
    }

    private fun normalizeWeightToKg(value: String, unit: String): Double? {
        val parsed = value.toDoubleOrNull() ?: return null
        return if (unit.equals("lbs", ignoreCase = true)) {
            parsed * 0.45359237
        } else {
            parsed
        }
    }
}
