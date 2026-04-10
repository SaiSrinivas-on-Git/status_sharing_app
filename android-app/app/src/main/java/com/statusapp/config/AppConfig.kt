package com.statusapp.config

import com.statusapp.BuildConfig

/**
 * App configuration constants.
 */
object AppConfig {
    /** Backend API base URL */
    val BACKEND_URL: String = BuildConfig.BACKEND_URL

    /** Timeout for status collection on device (ms) */
    const val COLLECTION_TIMEOUT_MS = 4000L

    /** Speed threshold for "vehicle" classification (m/s) ≈ 30 km/h */
    const val VEHICLE_SPEED_THRESHOLD = 8.0f

    /** Speed threshold for "walking" classification (m/s) */
    const val WALKING_SPEED_THRESHOLD = 1.5f

    /** Signal level threshold for "weak" (0-4 scale) */
    const val SIGNAL_WEAK_THRESHOLD = 1
}
