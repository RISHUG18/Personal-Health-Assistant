package com.vitalis.health

import android.app.Application
import com.google.android.gms.location.LocationServices
import com.vitalis.health.data.adapter.HealthApiAdapter
import com.vitalis.health.data.local.TokenManager
import com.vitalis.health.data.local.VitalsSyncPreferences
import com.vitalis.health.data.repository.HealthRepository
import com.vitalis.health.di.NetworkModule
import com.vitalis.health.healthconnect.HealthConnectManager
import com.vitalis.health.location.DefaultLocationTracker
import com.vitalis.health.location.LocationTracker
import com.vitalis.health.ui.ViewModelFactory

/**
 * Application-level singleton that wires up the dependency graph.
 *
 * Declare in AndroidManifest.xml:
 *   <application android:name=".VitalisApp" … />
 */
class VitalisApp : Application() {

    /** The single [TokenManager] instance for auth token persistence. */
    lateinit var tokenManager: TokenManager
        private set

    /** The single [HealthApiAdapter] instance for the entire app. */
    lateinit var apiAdapter: HealthApiAdapter
        private set

    /** The single [HealthRepository] instance for the entire app. */
    lateinit var repository: HealthRepository
        private set

    /** Persistent storage for wearable sync metadata (for example, last sync timestamp). */
    lateinit var vitalsSyncPreferences: VitalsSyncPreferences
        private set

    /** The single [LocationTracker] instance for GPS location. */
    lateinit var locationTracker: LocationTracker
        private set

    /**
     * The single [HealthConnectManager] instance for wearable data integration.
     * Uses Application context to survive Activity configuration changes.
     */
    lateinit var healthConnectManager: HealthConnectManager
        private set

    /** Factory that ViewModels can use: ViewModelProvider(this, app.viewModelFactory) */
    lateinit var viewModelFactory: ViewModelFactory
        private set

    override fun onCreate() {
        super.onCreate()

        tokenManager = TokenManager(this)

        val baseUrl = BuildConfig.BASE_URL          // from build.gradle
        apiAdapter = NetworkModule.provideAdapter(baseUrl, tokenManager)
        repository = HealthRepository(apiAdapter)
        vitalsSyncPreferences = VitalsSyncPreferences(this)

        // Initialize location tracking
        val fusedLocationClient = LocationServices.getFusedLocationProviderClient(this)
        locationTracker = DefaultLocationTracker(fusedLocationClient, this)

        // Initialize Health Connect with Application context (survives Activity lifecycle)
        healthConnectManager = HealthConnectManager(this)

        viewModelFactory = ViewModelFactory(repository, tokenManager, locationTracker)
    }
}
