"""Tests for the status derivation engine."""

import pytest
from app.services.status_engine import StatusEngine


class TestDeriveSound:
    def test_silent(self):
        assert StatusEngine.derive_sound("silent") == "Phone is on silent"

    def test_vibrate(self):
        assert StatusEngine.derive_sound("vibrate") == "Phone is on vibrate"

    def test_normal(self):
        assert StatusEngine.derive_sound("normal") == "Phone is reachable"

    def test_unknown(self):
        assert StatusEngine.derive_sound("") == "Sound status unknown"

    def test_none(self):
        assert StatusEngine.derive_sound(None) == "Sound status unknown"

    def test_case_insensitive(self):
        assert StatusEngine.derive_sound("SILENT") == "Phone is on silent"
        assert StatusEngine.derive_sound("Vibrate") == "Phone is on vibrate"


class TestDeriveMovement:
    def test_high_speed(self):
        result = StatusEngine.derive_movement(speed=15.0)
        assert result == "Currently travelling"

    def test_walking_speed(self):
        result = StatusEngine.derive_movement(speed=2.0)
        assert result == "Possibly on the move"

    def test_vehicle_activity(self):
        result = StatusEngine.derive_movement(activity="in_vehicle")
        assert result == "Currently travelling"

    def test_walking_activity(self):
        result = StatusEngine.derive_movement(activity="walking")
        assert result == "Possibly on the move"

    def test_still_activity(self):
        result = StatusEngine.derive_movement(activity="still")
        assert result == "Currently stationary"

    def test_speed_overrides_activity(self):
        # Speed > threshold should take precedence
        result = StatusEngine.derive_movement(activity="still", speed=15.0)
        assert result == "Currently travelling"

    def test_no_data(self):
        result = StatusEngine.derive_movement()
        assert "uncertain" in result.lower()


class TestDeriveNetwork:
    def test_weak_with_wifi(self):
        result = StatusEngine.derive_network(signal_level=1, wifi_connected=True)
        assert "weak" in result.lower()
        assert "WiFi" in result

    def test_weak_no_wifi(self):
        result = StatusEngine.derive_network(signal_level=0, wifi_connected=False)
        assert result == "Network seems weak"

    def test_strong_signal(self):
        result = StatusEngine.derive_network(signal_level=3)
        assert "good" in result.lower()

    def test_wifi_only(self):
        result = StatusEngine.derive_network(wifi_connected=True)
        assert "good" in result.lower()

    def test_no_data(self):
        result = StatusEngine.derive_network()
        assert "unknown" in result.lower()


class TestDeriveContactSuggestion:
    def test_weak_mobile_wifi(self):
        text, methods = StatusEngine.derive_contact_suggestion(
            signal_level=1, wifi_connected=True
        )
        assert "WhatsApp" in text
        assert "whatsapp" in methods
        assert "meet" in methods

    def test_weak_no_wifi(self):
        text, methods = StatusEngine.derive_contact_suggestion(
            signal_level=0, wifi_connected=False
        )
        assert "text" in text.lower() or "sms" in str(methods).lower()

    def test_good_signal(self):
        text, methods = StatusEngine.derive_contact_suggestion(
            signal_level=4, wifi_connected=False
        )
        assert text is None
        assert "call" in methods


class TestDeriveOutdoor:
    def test_moving(self):
        result = StatusEngine.derive_outdoor(speed=5.0)
        assert "outdoors" in result.lower()

    def test_in_vehicle(self):
        result = StatusEngine.derive_outdoor(activity="in_vehicle")
        assert "outdoors" in result.lower()

    def test_near_road(self):
        result = StatusEngine.derive_outdoor(near_road=True)
        assert "outdoors" in result.lower()

    def test_building_context(self):
        result = StatusEngine.derive_outdoor(
            speed=0, activity="still", location_type="establishment"
        )
        assert "indoors" in result.lower()

    def test_road_context(self):
        result = StatusEngine.derive_outdoor(location_type="route")
        assert "outdoors" in result.lower()

    def test_still_no_context(self):
        result = StatusEngine.derive_outdoor(activity="still")
        assert "indoors" in result.lower()

    def test_no_data(self):
        result = StatusEngine.derive_outdoor()
        assert "uncertain" in result.lower()

    def test_never_claims_certainty(self):
        """Verify all outputs use 'Likely' or 'uncertain', never 'definitely'."""
        test_cases = [
            StatusEngine.derive_outdoor(speed=20.0),
            StatusEngine.derive_outdoor(activity="still"),
            StatusEngine.derive_outdoor(near_road=True),
            StatusEngine.derive_outdoor(),
        ]
        for result in test_cases:
            assert "Likely" in result or "uncertain" in result.lower()


class TestGenerateSummary:
    def test_all_normal(self):
        # "Currently stationary" triggers the stationary keyword
        result = StatusEngine.generate_summary(
            "Phone is reachable", "Currently stationary",
            "Network looks good", "Likely indoors"
        )
        assert result == "Stationary"

    def test_truly_all_normal(self):
        # When no keywords match, we get the default
        result = StatusEngine.generate_summary(
            "Phone is reachable", "Movement status uncertain",
            "Network looks good", "Likely indoors"
        )
        assert result == "Available and reachable"

    def test_silent_travelling(self):
        result = StatusEngine.generate_summary(
            "Phone is on silent", "Currently travelling",
            "Network looks good", "Likely outdoors"
        )
        assert "silent" in result.lower()
        assert "move" in result.lower()
