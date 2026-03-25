package com.vitalis.health.data.local

import android.content.Context
import android.content.SharedPreferences
import androidx.core.content.edit

/**
 * Manages authentication tokens and user session data.
 *
 * Uses SharedPreferences for persistence. In production, consider using
 * EncryptedSharedPreferences for enhanced security.
 *
 * Injection: This should be instantiated in [VitalisApp] and passed to
 * [VitalisInterceptor] (for adding auth headers) and [AuthViewModel]
 * (for storing tokens after login/register).
 */
class TokenManager(context: Context) {

    private val prefs: SharedPreferences = context.getSharedPreferences(
        PREFS_NAME,
        Context.MODE_PRIVATE
    )

    // ── Access Token ──────────────────────────────────────────

    var accessToken: String?
        get() = prefs.getString(KEY_ACCESS_TOKEN, null)
        set(value) = prefs.edit { putString(KEY_ACCESS_TOKEN, value) }

    // ── Refresh Token ─────────────────────────────────────────

    var refreshToken: String?
        get() = prefs.getString(KEY_REFRESH_TOKEN, null)
        set(value) = prefs.edit { putString(KEY_REFRESH_TOKEN, value) }

    // ── User ID ───────────────────────────────────────────────

    var userId: String?
        get() = prefs.getString(KEY_USER_ID, null)
        set(value) = prefs.edit { putString(KEY_USER_ID, value) }

    // ── Convenience ───────────────────────────────────────────

    /** Returns true if the user has a valid access token stored. */
    val isLoggedIn: Boolean
        get() = !accessToken.isNullOrBlank()

    /**
     * Saves all auth data from a successful login or register response.
     */
    fun saveAuthData(accessToken: String, refreshToken: String, userId: String) {
        prefs.edit {
            putString(KEY_ACCESS_TOKEN, accessToken)
            putString(KEY_REFRESH_TOKEN, refreshToken)
            putString(KEY_USER_ID, userId)
        }
    }

    /**
     * Clears all stored auth data (logout).
     */
    fun clearAuthData() {
        prefs.edit {
            remove(KEY_ACCESS_TOKEN)
            remove(KEY_REFRESH_TOKEN)
            remove(KEY_USER_ID)
        }
    }

    companion object {
        private const val PREFS_NAME = "vitalis_auth_prefs"
        private const val KEY_ACCESS_TOKEN = "access_token"
        private const val KEY_REFRESH_TOKEN = "refresh_token"
        private const val KEY_USER_ID = "user_id"
    }
}
