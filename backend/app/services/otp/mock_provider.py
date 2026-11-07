"""Mock OTP delivery provider for local development, hackathon demonstration, and testing."""

import logging
from typing import Dict, Optional
from .base import BaseOTPProvider

logger = logging.getLogger("udyam360.otp.mock")


class MockOTPProvider(BaseOTPProvider):
    """Simulated OTP provider storing generated OTPs in memory for testing and evaluation."""

    def __init__(self):
        # Maps normalized phone_number -> last sent otp string (for automated test verification)
        self._sent_otps: Dict[str, str] = {}

    def send_otp(self, phone_number: str, otp: str) -> bool:
        """Simulates SMS dispatch. Records OTP for test harness verification."""
        clean_phone = phone_number.strip()
        self._sent_otps[clean_phone] = otp
        masked_phone = f"{clean_phone[:3]}******{clean_phone[-4:]}" if len(clean_phone) >= 7 else "******"
        logger.info("[MockOTPProvider] Dispatched simulated SMS OTP to %s", masked_phone)
        return True

    def get_last_otp(self, phone_number: str) -> Optional[str]:
        """Test harness helper to retrieve last dispatched OTP for verification."""
        return self._sent_otps.get(phone_number.strip())

    def clear(self) -> None:
        """Clears recorded test OTPs."""
        self._sent_otps.clear()

    def get_provider_name(self) -> str:
        return "mock"

