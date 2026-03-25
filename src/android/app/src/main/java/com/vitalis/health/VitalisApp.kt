package com.vitalis.health

import android.app.Application
import com.google.android.gms.location.LocationServices
import com.vitalis.health.data.adapter.HealthApiAdapter
import com.vitalis.health.data.local.TokenManager
import com.vitalis.health.data.repository.HealthRepository
import com.vitalis.health.di.NetworkModule
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

    /** The single [LocationTracker] instance for GPS location. */
    lateinit var locationTracker: LocationTracker
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

        // Initialize location tracking
        val fusedLocationClient = LocationServices.getFusedLocationProviderClient(this)
        locationTracker = DefaultLocationTracker(fusedLocationClient, this)

        viewModelFactory = ViewModelFactory(repository, tokenManager)
    }
}
