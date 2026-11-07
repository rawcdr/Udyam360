"""OTP provider factory and configuration selector."""

import os
from .base import BaseOTPProvider
from .mock_provider import MockOTPProvider
from .sms_provider import SMSOTPProvider

_default_mock_provider = MockOTPProvider()


def get_otp_provider() -> BaseOTPProvider:
    """Instantiates or returns the configured OTP provider.
    
    Strictly forbids MockOTPProvider in production environment.
    """
    env = os.getenv("ENVIRONMENT", "development").strip().lower()
    configured_provider = os.getenv("OTP_PROVIDER", "mock").strip().lower()

    if env == "production" and configured_provider == "mock":
        raise RuntimeError(
            "CRITICAL SECURITY CONFIGURATION ERROR: "
            "MockOTPProvider is strictly prohibited in production mode. "
            "Configure a real SMS provider (e.g. OTP_PROVIDER=sms) and supply API credentials."
        )

    if configured_provider == "sms":
        return SMSOTPProvider()

    return _default_mock_provider

