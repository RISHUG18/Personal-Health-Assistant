package com.vitalis.health.data.local

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.longPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.first

private val Context.vitalsSyncDataStore by preferencesDataStore(name = "vitalis_sync_preferences")

class VitalsSyncPreferences(context: Context) {

    private val appContext = context.applicationContext

    private fun lastSyncKey(userId: String) =
        longPreferencesKey("last_sync_timestamp_${userId.replace("-", "_")}")

    suspend fun getLastSyncTimestampMillis(userId: String): Long? {
        if (userId.isBlank()) return null
        val prefs = appContext.vitalsSyncDataStore.data.first()
        return prefs[lastSyncKey(userId)]
    }

    suspend fun setLastSyncTimestampMillis(userId: String, timestampMillis: Long) {
        if (userId.isBlank()) return
        appContext.vitalsSyncDataStore.edit { prefs ->
            prefs[lastSyncKey(userId)] = timestampMillis
        }
    }
}
