"""Status derivation engine — pure-function rules for deriving human-readable status."""

from typing import Optional
import logging

logger = logging.getLogger(__name__)


class StatusEngine:
    """
    Derives human-readable status phrases from device sensor data.
    All methods are pure functions — no side effects, fully unit-testable.
    """

    # Speed threshold in m/s (roughly 10 km/h)
    VEHICLE_SPEED_THRESHOLD = 8.0
    WALKING_SPEED_THRESHOLD = 1.5

    # Signal level thresholds (0-4 scale from Android)
    SIGNAL_WEAK_THRESHOLD = 1

    @staticmethod
    def derive_sound(ringer_mode: str) -> str:
        """Derive sound status from ringer mode."""
        mode = ringer_mode.lower().strip() if ringer_mode else "unknown"
        mapping = {
            "silent": "Phone is on silent",
            "vibrate": "Phone is on vibrate",
            "normal": "Phone is reachable",
        }
        return mapping.get(mode, "Sound status unknown")

    @staticmethod
    def derive_movement(activity: Optional[str] = None,
                        speed: Optional[float] = None) -> str:
        """Derive movement status from activity recognition and speed."""
        activity = (activity or "").lower().strip()

        # Check speed first (more reliable)
        if speed is not None:
            if speed > StatusEngine.VEHICLE_SPEED_THRESHOLD:
                return "Currently travelling"
            elif speed > StatusEngine.WALKING_SPEED_THRESHOLD:
                return "Possibly on the move"

        # Fall back to activity recognition
        if activity in ("in_vehicle", "on_bicycle"):
            return "Currently travelling"
        elif activity in ("walking", "running", "on_foot"):
            return "Possibly on the move"
        elif activity in ("still", "tilting"):
            return "Currently stationary"

        return "Movement status uncertain"

    @staticmethod
    def derive_network(signal_level: Optional[int] = None,
                       wifi_connected: bool = False) -> str:
        """Derive network status from signal strength and WiFi."""
        is_weak = (
            signal_level is not None and
            signal_level <= StatusEngine.SIGNAL_WEAK_THRESHOLD
        )

        if is_weak and wifi_connected:
            return "Mobile network is weak, but WiFi is available"
        elif is_weak and not wifi_connected:
            return "Network seems weak"
        elif wifi_connected:
            return "Network looks good (WiFi connected)"
        elif signal_level is not None and signal_level > StatusEngine.SIGNAL_WEAK_THRESHOLD:
            return "Network looks good"
        else:
            return "Network status unknown"

    @staticmethod
    def derive_contact_suggestion(signal_level: Optional[int] = None,
                                   wifi_connected: bool = False) -> tuple[Optional[str], list[str]]:
        """
        Suggest contact methods based on network conditions.
        Returns (suggestion_text, list_of_methods).
        """
        is_weak_mobile = (
            signal_level is not None and
            signal_level <= StatusEngine.SIGNAL_WEAK_THRESHOLD
        )

        if is_weak_mobile and wifi_connected:
            return (
                "Regular calls may not work well. Try WhatsApp or Google Meet instead.",
                ["whatsapp", "meet"]
            )
        elif is_weak_mobile and not wifi_connected:
            return (
                "Network is weak. A text message might be more reliable than a call.",
                ["sms"]
            )
        else:
            return (None, ["call", "whatsapp", "meet"])

    @staticmethod
    def derive_outdoor(
        speed: Optional[float] = None,
        activity: Optional[str] = None,
        near_road: Optional[bool] = None,
        location_type: Optional[str] = None,
    ) -> str:
        """
        Derive outdoor likelihood heuristic.

        NEVER claims certainty — uses "Likely" prefix.

        Args:
            speed: Device speed in m/s
            activity: Activity recognition result
            near_road: Whether device is near a road (from Roads API)
            location_type: Reverse geocode context (e.g., "building", "road", "park")
        """
        activity = (activity or "").lower().strip()

        # Moving = likely outdoors
        if speed is not None and speed > StatusEngine.WALKING_SPEED_THRESHOLD:
            return "Likely outdoors"

        if activity in ("in_vehicle", "on_bicycle", "walking", "running", "on_foot"):
            return "Likely outdoors"

        # Near a road = likely outdoors
        if near_road is True:
            return "Likely outdoors"

        # Location context from reverse geocode
        if location_type:
            lt = location_type.lower()
            indoor_types = ["building", "establishment", "store", "office",
                          "hospital", "school", "university", "mall",
                          "restaurant", "cafe", "gym"]
            outdoor_types = ["road", "route", "highway", "park", "garden",
                           "street", "intersection", "natural_feature"]

            if any(t in lt for t in indoor_types):
                return "Likely indoors"
            if any(t in lt for t in outdoor_types):
                return "Likely outdoors"

        # Stationary with no context
        if activity == "still":
            return "Likely indoors"

        return "Location uncertain"

    @staticmethod
    def generate_summary(sound: str, movement: str, network: str,
                         outdoor: str) -> str:
        """Generate a one-line summary of the overall status."""
        parts = []

        if "silent" in sound.lower():
            parts.append("Phone silent")
        elif "vibrate" in sound.lower():
            parts.append("Phone on vibrate")

        if "travelling" in movement.lower():
            parts.append("on the move")
        elif "stationary" in movement.lower():
            parts.append("stationary")

        if "weak" in network.lower():
            parts.append("weak network")

        if not parts:
            return "Available and reachable"

        return ", ".join(parts).capitalize()
