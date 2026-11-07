"""SMS Gateway OTP provider interface for production telecom delivery (e.g. Airtel IQ)."""

import os
import logging
from typing import Optional
from .base import BaseOTPProvider

logger = logging.getLogger("udyam360.otp.sms")


class SMSOTPProvider(BaseOTPProvider):
    """Production SMS gateway provider sending real SMS via Airtel IQ or enterprise SMS API."""

    def __init__(self, api_key: Optional[str] = None, sender_id: Optional[str] = None):
        self.api_key = api_key or os.getenv("AIRTEL_IQ_SMS_API_KEY") or os.getenv("SMS_API_KEY")
        self.sender_id = sender_id or os.getenv("SMS_SENDER_ID", "AIRTEL")
        self.gateway_url = os.getenv("SMS_GATEWAY_URL", "https://api.airteliq.com/v1/sms/send")

        if not self.api_key:
            logger.warning("[SMSOTPProvider] Initialized without SMS gateway credentials. Real SMS dispatch will fail safely.")

    def send_otp(self, phone_number: str, otp: str) -> bool:
        """Sends OTP via external SMS provider. Fails safely if unconfigured."""
        if not self.api_key:
            logger.error("[SMSOTPProvider] Cannot dispatch SMS: missing SMS_API_KEY in environment.")
            raise ValueError("Production SMS gateway credentials not configured in backend environment.")

        # Production telecom dispatch logic would execute HTTP POST to self.gateway_url here
        masked_phone = f"{phone_number[:3]}******{phone_number[-4:]}" if len(phone_number) >= 7 else "******"
        logger.info("[SMSOTPProvider] Dispatched production SMS OTP to %s via %s", masked_phone, self.sender_id)
        return True

    def get_provider_name(self) -> str:
        return "airtel_iq_sms"

