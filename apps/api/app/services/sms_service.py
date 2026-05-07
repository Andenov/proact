"""
PROACT SMS Abstraction Layer.
Supports mock provider (default) and Africa's Talking.
Switch via SMS_PROVIDER env var.
"""

import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict

from app.core.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Message Templates
# ---------------------------------------------------------------------------
SMS_TEMPLATES: Dict[str, Dict[str, str]] = {
    "flood": {
        "Low": (
            "PROACT: Low flood risk in {district}. Monitor rainfall and keep drainage clear. "
            "Stay alert for updates."
        ),
        "Medium": (
            "PROACT Alert: Moderate flood risk in {district} over the next 3 days. "
            "Protect stored inputs, clear drainage, and follow local advisories."
        ),
        "High": (
            "PROACT Alert: HIGH flood risk in {district} in the next 3 days due to heavy rainfall. "
            "Move livestock, protect stored grain, and avoid low-lying areas. Stay safe."
        ),
    },
    "landslide": {
        "Low": (
            "PROACT: Low landslide risk in {district}. Monitor hillside areas if rains intensify."
        ),
        "Medium": (
            "PROACT Alert: Moderate landslide risk in {district}. Hillside communities should "
            "stay alert and be ready to move if rains worsen."
        ),
        "High": (
            "PROACT Alert: HIGH landslide risk in {district}. Hillside communities should move "
            "to safer ground. Contact local leaders immediately. Protect lives and assets."
        ),
    },
    "food_stress": {
        "Low": (
            "PROACT: Mild drought stress in {district}. Consider water conservation and "
            "contact extension officers for advice."
        ),
        "Medium": (
            "PROACT Alert: Moderate food stress risk in {district} due to rainfall deficit. "
            "Delay planting if possible and seek advice from extension officers."
        ),
        "High": (
            "PROACT Alert: HIGH food stress risk in {district}. Severe drought conditions. "
            "Contact extension officers. Emergency food support may be available from local leaders."
        ),
    },
}


def build_sms_message(district_name: str, alert_type: str, severity: str) -> str:
    template = SMS_TEMPLATES.get(alert_type, {}).get(severity)
    if not template:
        return f"PROACT Alert: {severity} {alert_type} risk in {district_name}. Contact local officials."
    return template.format(district=district_name)


# ---------------------------------------------------------------------------
# Provider Abstraction
# ---------------------------------------------------------------------------

class BaseSMSProvider(ABC):
    @abstractmethod
    def send(self, phone: str, message: str) -> Dict:
        ...


class MockSMSProvider(BaseSMSProvider):
    def send(self, phone: str, message: str) -> Dict:
        msg_id = str(uuid.uuid4())[:8]
        logger.info(f"[MOCK SMS] To {phone}: {message}")
        return {
            "provider": "mock",
            "message_id": msg_id,
            "status": "delivered",
            "timestamp": datetime.utcnow().isoformat(),
        }


class AfricasTalkingProvider(BaseSMSProvider):
    def __init__(self):
        try:
            import africastalking
            africastalking.initialize(settings.AT_USERNAME, settings.AT_API_KEY)
            self._sms = africastalking.SMS
        except ImportError:
            raise RuntimeError(
                "africastalking package not installed. "
                "Add 'africastalking' to requirements.txt to use this provider."
            )

    def send(self, phone: str, message: str) -> Dict:
        try:
            response = self._sms.send(message, [phone])
            recipients = response.get("SMSMessageData", {}).get("Recipients", [])
            if recipients:
                rec = recipients[0]
                return {
                    "provider": "africas_talking",
                    "message_id": rec.get("messageId"),
                    "status": rec.get("status", "unknown"),
                    "cost": rec.get("cost"),
                }
            return {"provider": "africas_talking", "status": "unknown", "raw": response}
        except Exception as e:
            logger.error(f"Africa's Talking send error: {e}")
            return {"provider": "africas_talking", "status": "error", "error": str(e)}


def get_sms_provider() -> BaseSMSProvider:
    provider = settings.SMS_PROVIDER.lower()
    if provider == "africas_talking":
        return AfricasTalkingProvider()
    return MockSMSProvider()
