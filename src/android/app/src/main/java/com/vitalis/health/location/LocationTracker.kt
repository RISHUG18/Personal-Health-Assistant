package com.vitalis.health.location

import android.location.Location

/**
 * Interface for obtaining the device's current location.
 *
 * This abstraction allows for:
 * - Easy mocking in tests
 * - Swapping implementations (GPS, network, fused)
 * - Centralized permission checking
 */
interface LocationTracker {

    /**
     * Attempts to get the device's current location.
     *
     * @return The current [Location] if available, or null if:
     *   - Location permissions are not granted
     *   - Location services are disabled
     *   - Location could not be determined
     */
    suspend fun getCurrentLocation(): Location?
}
