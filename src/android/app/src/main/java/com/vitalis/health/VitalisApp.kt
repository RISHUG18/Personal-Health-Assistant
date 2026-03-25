package com.vitalis.health

import android.app.Application
import com.vitalis.health.data.adapter.HealthApiAdapter
import com.vitalis.health.data.local.TokenManager
import com.vitalis.health.data.repository.HealthRepository
import com.vitalis.health.di.NetworkModule
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

    /** Factory that ViewModels can use: ViewModelProvider(this, app.viewModelFactory) */
    lateinit var viewModelFactory: ViewModelFactory
        private set

    override fun onCreate() {
        super.onCreate()

        tokenManager = TokenManager(this)

        val baseUrl = BuildConfig.BASE_URL          // from build.gradle
        apiAdapter = NetworkModule.provideAdapter(baseUrl, tokenManager)
        repository = HealthRepository(apiAdapter)
        viewModelFactory = ViewModelFactory(repository, tokenManager)
    }
}
