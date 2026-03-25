package com.vitalis.health.location

import android.Manifest
import android.app.Application
import android.content.Context
import android.content.pm.PackageManager
import android.location.Location
import android.location.LocationManager
import android.os.Looper
import androidx.core.content.ContextCompat
import com.google.android.gms.location.FusedLocationProviderClient
import com.google.android.gms.location.LocationCallback
import com.google.android.gms.location.LocationRequest
import com.google.android.gms.location.LocationResult
import com.google.android.gms.location.Priority
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlin.coroutines.resume

/**
 * Default implementation of [LocationTracker] using Google Play Services
 * [FusedLocationProviderClient].
 *
 * This implementation:
 * - Checks for location permissions before requesting
 * - Verifies GPS/Network providers are enabled
 * - Tries to get the last known location first (fast path)
 * - Falls back to requesting a fresh location if needed
 * - Uses coroutines for async operations
 *
 * @param locationClient The [FusedLocationProviderClient] instance
 * @param application The application context for permission checks
 */
class DefaultLocationTracker(
    private val locationClient: FusedLocationProviderClient,
    private val application: Application
) : LocationTracker {

    override suspend fun getCurrentLocation(): Location? {
        // Check if location permissions are granted
        val hasCoarsePermission = ContextCompat.checkSelfPermission(
            application,
            Manifest.permission.ACCESS_COARSE_LOCATION
        ) == PackageManager.PERMISSION_GRANTED

        val hasFinePermission = ContextCompat.checkSelfPermission(
            application,
            Manifest.permission.ACCESS_FINE_LOCATION
        ) == PackageManager.PERMISSION_GRANTED

        if (!hasCoarsePermission && !hasFinePermission) {
            return null
        }

        // Check if location services are enabled
        val locationManager = application.getSystemService(
            Context.LOCATION_SERVICE
        ) as LocationManager

        val isGpsEnabled = locationManager.isProviderEnabled(LocationManager.GPS_PROVIDER)
        val isNetworkEnabled = locationManager.isProviderEnabled(LocationManager.NETWORK_PROVIDER)

        if (!isGpsEnabled && !isNetworkEnabled) {
            return null
        }

        // Try to get last known location first (fast path)
        return try {
            getLastKnownLocation() ?: requestCurrentLocation()
        } catch (e: SecurityException) {
            // Permission was revoked between check and request
            null
        } catch (e: Exception) {
            // Any other error - return null
            null
        }
    }

    /**
     * Attempts to get the last known location from the fused provider.
     * This is usually fast but may be null if no location has been cached.
     */
    @Suppress("MissingPermission")
    private suspend fun getLastKnownLocation(): Location? {
        return suspendCancellableCoroutine { cont ->
            locationClient.lastLocation
                .addOnSuccessListener { location ->
                    // location can be null if no cached location exists
                    cont.resume(location)
                }
                .addOnFailureListener {
                    cont.resume(null)
                }
                .addOnCanceledListener {
                    cont.resume(null)
                }
        }
    }

    /**
     * Requests a fresh location update from the fused provider.
     * Used when no cached location is available.
     */
    @Suppress("MissingPermission")
    private suspend fun requestCurrentLocation(): Location? {
        return suspendCancellableCoroutine { cont ->
            val locationRequest = LocationRequest.Builder(
                Priority.PRIORITY_HIGH_ACCURACY,
                LOCATION_UPDATE_INTERVAL_MS
            )
                .setWaitForAccurateLocation(false)
                .setMinUpdateIntervalMillis(LOCATION_MIN_UPDATE_INTERVAL_MS)
                .setMaxUpdates(1) // Only need one update
                .build()

            val locationCallback = object : LocationCallback() {
                override fun onLocationResult(result: LocationResult) {
                    super.onLocationResult(result)
                    locationClient.removeLocationUpdates(this)
                    cont.resume(result.lastLocation)
                }
            }

            locationClient.requestLocationUpdates(
                locationRequest,
                locationCallback,
                Looper.getMainLooper()
            )

            // Handle cancellation
            cont.invokeOnCancellation {
                locationClient.removeLocationUpdates(locationCallback)
            }
        }
    }

    companion object {
        private const val LOCATION_UPDATE_INTERVAL_MS = 10_000L // 10 seconds
        private const val LOCATION_MIN_UPDATE_INTERVAL_MS = 5_000L // 5 seconds
    }
}
