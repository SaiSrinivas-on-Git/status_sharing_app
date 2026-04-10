package com.statusapp.collectors

import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.media.AudioManager
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.net.wifi.WifiManager
import android.os.BatteryManager
import android.os.Build
import android.telephony.CellSignalStrength
import android.telephony.TelephonyManager
import android.util.Log
import androidx.annotation.RequiresPermission
import com.google.android.gms.location.FusedLocationProviderClient
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import com.google.android.gms.tasks.CancellationTokenSource
import com.statusapp.fcm.LocationData
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.tasks.await
import kotlin.coroutines.resume

private const val TAG = "Collectors"

// ═══════════════════════════════════════════════════════════════════
// RINGER MODE COLLECTOR
// ═══════════════════════════════════════════════════════════════════

object RingerCollector {
    fun collect(context: Context): String {
        return try {
            val audio = context.getSystemService(Context.AUDIO_SERVICE) as AudioManager
            when (audio.ringerMode) {
                AudioManager.RINGER_MODE_SILENT -> "silent"
                AudioManager.RINGER_MODE_VIBRATE -> "vibrate"
                AudioManager.RINGER_MODE_NORMAL -> "normal"
                else -> "unknown"
            }
        } catch (e: Exception) {
            Log.e(TAG, "RingerCollector failed", e)
            "unknown"
        }
    }
}

// ═══════════════════════════════════════════════════════════════════
// SIGNAL STRENGTH COLLECTOR
// ═══════════════════════════════════════════════════════════════════

object SignalCollector {
    fun collect(context: Context): Int? {
        return try {
            val telephony = context.getSystemService(Context.TELEPHONY_SERVICE) as TelephonyManager

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                val signalStrength = telephony.signalStrength
                signalStrength?.level  // Returns 0-4
            } else {
                null
            }
        } catch (e: SecurityException) {
            Log.w(TAG, "SignalCollector: permission denied", e)
            null
        } catch (e: Exception) {
            Log.e(TAG, "SignalCollector failed", e)
            null
        }
    }
}

// ═══════════════════════════════════════════════════════════════════
// WIFI COLLECTOR
// ═══════════════════════════════════════════════════════════════════

object WifiCollector {
    fun collect(context: Context): Boolean {
        return try {
            val cm = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
            val network = cm.activeNetwork ?: return false
            val caps = cm.getNetworkCapabilities(network) ?: return false
            caps.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)
        } catch (e: Exception) {
            Log.e(TAG, "WifiCollector failed", e)
            false
        }
    }
}

// ═══════════════════════════════════════════════════════════════════
// ACTIVITY RECOGNITION COLLECTOR
// ═══════════════════════════════════════════════════════════════════

object ActivityCollector {
    /**
     * Get the most recent detected activity.
     * For simplicity, this uses a heuristic based on speed from location
     * since full Activity Recognition API requires a persistent listener.
     *
     * In a production app, you'd register an ActivityRecognitionClient
     * listener and cache the last result.
     */
    fun collect(context: Context): String {
        // Simplified — will be enhanced by speed-based detection
        // For now, return "unknown" and let the engine use speed.
        return "unknown"
    }
}

// ═══════════════════════════════════════════════════════════════════
// LOCATION COLLECTOR
// ═══════════════════════════════════════════════════════════════════

object LocationCollector {
    suspend fun collect(context: Context): LocationData? {
        return try {
            val client: FusedLocationProviderClient =
                LocationServices.getFusedLocationProviderClient(context)

            // Try to get current location with a short timeout
            val cts = CancellationTokenSource()
            @Suppress("MissingPermission")
            val location = try {
                client.getCurrentLocation(
                    Priority.PRIORITY_BALANCED_POWER_ACCURACY,
                    cts.token
                ).await()
            } catch (e: SecurityException) {
                Log.w(TAG, "LocationCollector: permission denied, trying last location")
                // Fall back to last known location
                @Suppress("MissingPermission")
                client.lastLocation.await()
            }

            if (location != null) {
                LocationData(
                    latitude = location.latitude,
                    longitude = location.longitude,
                    speed = if (location.hasSpeed()) location.speed else null,
                    accuracy = if (location.hasAccuracy()) location.accuracy else null,
                )
            } else {
                Log.w(TAG, "LocationCollector: no location available")
                null
            }
        } catch (e: SecurityException) {
            Log.w(TAG, "LocationCollector: permission denied", e)
            null
        } catch (e: Exception) {
            Log.e(TAG, "LocationCollector failed", e)
            null
        }
    }
}

// ═══════════════════════════════════════════════════════════════════
// BATTERY COLLECTOR
// ═══════════════════════════════════════════════════════════════════

object BatteryCollector {
    fun collect(context: Context): Int? {
        return try {
            val batteryStatus: Intent? = IntentFilter(Intent.ACTION_BATTERY_CHANGED).let {
                context.registerReceiver(null, it)
            }
            val level = batteryStatus?.getIntExtra(BatteryManager.EXTRA_LEVEL, -1) ?: -1
            val scale = batteryStatus?.getIntExtra(BatteryManager.EXTRA_SCALE, -1) ?: -1
            if (level >= 0 && scale > 0) {
                (level * 100 / scale)
            } else {
                null
            }
        } catch (e: Exception) {
            Log.e(TAG, "BatteryCollector failed", e)
            null
        }
    }
}
