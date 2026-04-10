package com.statusapp.engine

import com.statusapp.config.AppConfig
import com.statusapp.fcm.DeviceData

/**
 * Status Derivation Engine — pure functions that convert raw device data
 * into human-readable status phrases.
 *
 * Rules:
 * - NEVER expose raw GPS coordinates
 * - NEVER claim certainty about location (use "Likely")
 * - All methods are stateless and unit-testable
 */
object StatusDerivationEngine {

    /**
     * Derive all status fields from device data.
     */
    fun deriveAll(data: DeviceData): DerivedStatus {
        val sound = deriveSound(data.ringerMode)
        val movement = deriveMovement(data.activity, data.location?.speed)
        val network = deriveNetwork(data.signalLevel, data.wifiConnected)
        val (contactSuggestion, contactMethods) = deriveContactSuggestion(
            data.signalLevel, data.wifiConnected
        )
        val outdoor = deriveOutdoor(data.location?.speed, data.activity)
        val summary = generateSummary(sound, movement, network, outdoor)

        return DerivedStatus(
            soundStatus = sound,
            movementStatus = movement,
            networkStatus = network,
            outdoorStatus = outdoor,
            contactSuggestion = contactSuggestion,
            contactMethods = contactMethods,
            deviceBattery = data.batteryLevel,
            summary = summary,
        )
    }

    fun deriveSound(ringerMode: String): String {
        return when (ringerMode.lowercase().trim()) {
            "silent" -> "Phone is on silent"
            "vibrate" -> "Phone is on vibrate"
            "normal" -> "Phone is reachable"
            else -> "Sound status unknown"
        }
    }

    fun deriveMovement(activity: String?, speed: Float?): String {
        // Speed is more reliable than activity recognition
        if (speed != null) {
            if (speed > AppConfig.VEHICLE_SPEED_THRESHOLD) return "Currently travelling"
            if (speed > AppConfig.WALKING_SPEED_THRESHOLD) return "Possibly on the move"
        }

        val act = activity?.lowercase()?.trim() ?: ""
        return when (act) {
            "in_vehicle", "on_bicycle" -> "Currently travelling"
            "walking", "running", "on_foot" -> "Possibly on the move"
            "still", "tilting" -> "Currently stationary"
            else -> if (speed != null && speed <= AppConfig.WALKING_SPEED_THRESHOLD) {
                "Currently stationary"
            } else {
                "Movement status uncertain"
            }
        }
    }

    fun deriveNetwork(signalLevel: Int?, wifiConnected: Boolean): String {
        val isWeak = signalLevel != null && signalLevel <= AppConfig.SIGNAL_WEAK_THRESHOLD

        return when {
            isWeak && wifiConnected -> "Mobile network is weak, but WiFi is available"
            isWeak && !wifiConnected -> "Network seems weak"
            wifiConnected -> "Network looks good (WiFi connected)"
            signalLevel != null && signalLevel > AppConfig.SIGNAL_WEAK_THRESHOLD -> "Network looks good"
            else -> "Network status unknown"
        }
    }

    fun deriveContactSuggestion(
        signalLevel: Int?,
        wifiConnected: Boolean
    ): Pair<String?, List<String>> {
        val isWeakMobile = signalLevel != null && signalLevel <= AppConfig.SIGNAL_WEAK_THRESHOLD

        return when {
            isWeakMobile && wifiConnected -> Pair(
                "Regular calls may not work well. Try WhatsApp or Google Meet instead.",
                listOf("whatsapp", "meet")
            )
            isWeakMobile && !wifiConnected -> Pair(
                "Network is weak. A text message might be more reliable than a call.",
                listOf("sms")
            )
            else -> Pair(null, listOf("call", "whatsapp", "meet"))
        }
    }

    fun deriveOutdoor(speed: Float?, activity: String?): String {
        val act = activity?.lowercase()?.trim() ?: ""

        // Moving = likely outdoors
        if (speed != null && speed > AppConfig.WALKING_SPEED_THRESHOLD) {
            return "Likely outdoors"
        }

        if (act in listOf("in_vehicle", "on_bicycle", "walking", "running", "on_foot")) {
            return "Likely outdoors"
        }

        // Stationary = likely indoors
        if (act == "still") {
            return "Likely indoors"
        }

        return "Location uncertain"
    }

    fun generateSummary(sound: String, movement: String, network: String, outdoor: String): String {
        val parts = mutableListOf<String>()

        if ("silent" in sound.lowercase()) parts.add("Phone silent")
        else if ("vibrate" in sound.lowercase()) parts.add("Phone on vibrate")

        if ("travelling" in movement.lowercase()) parts.add("on the move")
        else if ("stationary" in movement.lowercase()) parts.add("stationary")

        if ("weak" in network.lowercase()) parts.add("weak network")

        return if (parts.isEmpty()) "Available and reachable"
        else parts.joinToString(", ").replaceFirstChar { it.uppercase() }
    }
}

/**
 * Container for derived status — only human-readable strings,
 * NO raw sensor data.
 */
data class DerivedStatus(
    val soundStatus: String,
    val movementStatus: String,
    val networkStatus: String,
    val outdoorStatus: String,
    val contactSuggestion: String?,
    val contactMethods: List<String>,
    val deviceBattery: Int?,
    val summary: String,
)
