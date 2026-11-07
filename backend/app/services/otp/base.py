"""Abstract base class for OTP delivery providers."""

from abc import ABC, abstractmethod


class BaseOTPProvider(ABC):
    """Abstract interface for multi-channel OTP delivery."""

    @abstractmethod
    def send_otp(self, phone_number: str, otp: str) -> bool:
        """Dispatches OTP to customer mobile number."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Returns provider identifier."""
        pass

