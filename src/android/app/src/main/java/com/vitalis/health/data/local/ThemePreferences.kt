package com.vitalis.health.data.local

import android.content.Context
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Context.vitalisPreferencesDataStore by preferencesDataStore(name = "vitalis_preferences")

class ThemePreferences(private val context: Context) {

    private val darkThemeKey = booleanPreferencesKey("dark_theme_enabled")

    val isDarkThemeEnabled: Flow<Boolean> =
        context.vitalisPreferencesDataStore.data.map { preferences ->
            preferences[darkThemeKey] ?: false
        }

    suspend fun setDarkThemeEnabled(enabled: Boolean) {
        context.vitalisPreferencesDataStore.edit { preferences ->
            preferences[darkThemeKey] = enabled
        }
    }
}
