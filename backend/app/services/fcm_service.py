"""FCM service — send high-priority data messages to Android device."""

from firebase_admin import messaging
import logging
import time

logger = logging.getLogger(__name__)


class FCMService:
    """Firebase Cloud Messaging service for triggering device refresh."""

    MAX_RETRIES = 2
    RETRY_DELAY_BASE = 0.5  # seconds

    def send_refresh_trigger(self, device_token: str, request_id: str) -> bool:
        """
        Send a high-priority data-only FCM message to the Android device.

        Args:
            device_token: FCM registration token of the device
            request_id: Unique request ID to track this refresh

        Returns:
            True if message was sent successfully, False otherwise
        """
        message = messaging.Message(
            data={
                "type": "refresh_status",
                "request_id": request_id,
                "timestamp": str(int(time.time())),
            },
            token=device_token,
            android=messaging.AndroidConfig(
                priority="high",
                ttl=30,  # Message expires after 30 seconds
            ),
        )

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                response = messaging.send(message)
                logger.info(
                    f"FCM message sent successfully: {response}, "
                    f"request_id={request_id}"
                )
                return True
            except messaging.UnregisteredError:
                logger.error(
                    f"FCM token is unregistered/invalid: {device_token[:20]}..."
                )
                return False
            except Exception as e:
                if attempt < self.MAX_RETRIES:
                    delay = self.RETRY_DELAY_BASE * (2 ** attempt)
                    logger.warning(
                        f"FCM send attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        f"FCM send failed after {self.MAX_RETRIES + 1} attempts: {e}"
                    )
                    return False

        return False
