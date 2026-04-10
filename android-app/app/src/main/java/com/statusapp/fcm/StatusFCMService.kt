package com.statusapp.fcm

import android.util.Log
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import com.statusapp.collectors.*
import com.statusapp.engine.StatusDerivationEngine
import com.statusapp.network.ApiClient
import kotlinx.coroutines.*

/**
 * Firebase Cloud Messaging service.
 *
 * Receives high-priority data messages from the backend,
 * collects device state, derives status, and uploads it.
 */
class StatusFCMService : FirebaseMessagingService() {

    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())

    companion object {
        private const val TAG = "StatusFCM"
    }

    override fun onMessageReceived(message: RemoteMessage) {
        super.onMessageReceived(message)

        val data = message.data
        Log.d(TAG, "FCM message received: $data")

        val type = data["type"]
        val requestId = data["request_id"]

        if (type == "refresh_status" && requestId != null) {
            Log.d(TAG, "Starting status refresh for request: $requestId")
            scope.launch {
                handleRefreshRequest(requestId)
            }
        }
    }

    override fun onNewToken(token: String) {
        super.onNewToken(token)
        Log.d(TAG, "New FCM token: ${token.take(20)}...")

        // Upload new token to backend
        scope.launch {
            try {
                ApiClient.getInstance(applicationContext).updateFCMToken(token)
                Log.d(TAG, "FCM token uploaded to backend")
            } catch (e: Exception) {
                Log.e(TAG, "Failed to upload FCM token", e)
            }
        }
    }

    /**
     * Handle a status refresh request:
     * 1. Collect device state
     * 2. Derive human-readable status
     * 3. Upload to backend
     */
    private suspend fun handleRefreshRequest(requestId: String) {
        try {
            // Collect all device data in parallel, with timeout
            val deviceData = withTimeoutOrNull(4000L) {
                collectDeviceData()
            } ?: DeviceData.empty()

            Log.d(TAG, "Collected device data: $deviceData")

            // Derive status (pure function, never fails)
            val derivedStatus = StatusDerivationEngine.deriveAll(deviceData)

            Log.d(TAG, "Derived status: $derivedStatus")

            // Upload to backend
            val apiClient = ApiClient.getInstance(applicationContext)
            apiClient.uploadStatus(requestId, derivedStatus)

            Log.d(TAG, "Status uploaded successfully for request: $requestId")

        } catch (e: Exception) {
            Log.e(TAG, "Failed to handle refresh request: $requestId", e)
        }
    }

    /**
     * Collect all device sensor data in parallel.
     */
    private suspend fun collectDeviceData(): DeviceData = coroutineScope {
        val context = applicationContext

        // Launch all collectors in parallel
        val ringerDeferred = async { RingerCollector.collect(context) }
        val signalDeferred = async { SignalCollector.collect(context) }
        val wifiDeferred = async { WifiCollector.collect(context) }
        val activityDeferred = async { ActivityCollector.collect(context) }
        val locationDeferred = async { LocationCollector.collect(context) }
        val batteryDeferred = async { BatteryCollector.collect(context) }

        DeviceData(
            ringerMode = ringerDeferred.await(),
            signalLevel = signalDeferred.await(),
            wifiConnected = wifiDeferred.await(),
            activity = activityDeferred.await(),
            location = locationDeferred.await(),
            batteryLevel = batteryDeferred.await(),
        )
    }

    override fun onDestroy() {
        super.onDestroy()
        scope.cancel()
    }
}

/**
 * Container for all collected device data.
 */
data class DeviceData(
    val ringerMode: String = "unknown",
    val signalLevel: Int? = null,
    val wifiConnected: Boolean = false,
    val activity: String = "unknown",
    val location: LocationData? = null,
    val batteryLevel: Int? = null,
) {
    companion object {
        fun empty() = DeviceData()
    }
}

data class LocationData(
    val latitude: Double,
    val longitude: Double,
    val speed: Float? = null,
    val accuracy: Float? = null,
)
