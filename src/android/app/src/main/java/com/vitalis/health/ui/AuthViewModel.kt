package com.vitalis.health.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.vitalis.health.data.local.TokenManager
import com.vitalis.health.data.model.AuthResponse
import com.vitalis.health.data.network.ApiResult
import com.vitalis.health.data.repository.HealthRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/**
 * ViewModel for Authentication screens (Login and Register).
 *
 * Manages:
 * - Form input state (email, password, name)
 * - UI state (Idle, Loading, Success, Error)
 * - API calls for login/register
 * - Token persistence on successful authentication
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

    private val _authState = MutableStateFlow<AuthUiState>(AuthUiState.Idle)
    val authState: StateFlow<AuthUiState> = _authState.asStateFlow()

    // ── Form Input State ──────────────────────────────────

    private val _email = MutableStateFlow("")
    val email: StateFlow<String> = _email.asStateFlow()

    private val _password = MutableStateFlow("")
    val password: StateFlow<String> = _password.asStateFlow()

    private val _fullName = MutableStateFlow("")
    val fullName: StateFlow<String> = _fullName.asStateFlow()

    private val _confirmPassword = MutableStateFlow("")
    val confirmPassword: StateFlow<String> = _confirmPassword.asStateFlow()

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

        _authState.value = AuthUiState.Loading

        viewModelScope.launch {
            when (val result = repository.register(
                email = currentEmail,
                password = currentPassword,
                fullName = currentFullName
            )) {
                is ApiResult.Success -> {
                    // Save tokens to TokenManager
                    tokenManager.saveAuthData(
                        accessToken = result.data.accessToken,
                        refreshToken = result.data.refreshToken,
                        userId = result.data.userId
                    )
                    _authState.value = AuthUiState.Success(result.data)
                }
                is ApiResult.Error -> {
                    _authState.value = AuthUiState.Error(result.message)
                }
            }
        }
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
        tokenManager.clearAuthData()
        clearForm()
        _authState.value = AuthUiState.Idle
    }

    // ── Validation Helpers ────────────────────────────────

    private fun isValidEmail(email: String): Boolean {
        return android.util.Patterns.EMAIL_ADDRESS.matcher(email).matches()
    }
}
