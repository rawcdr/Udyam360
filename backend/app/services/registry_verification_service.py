"""Verification service performing lookups against synthetic mock GSTIN and Udyam registries."""

import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
import pandas as pd

from app.core.config import settings
from app.schemas.kyc import RegistryVerificationResult

logger = logging.getLogger("udyam360.registry_verification")


class RegistryVerificationService:
    """Performs deterministic lookups against the hackathon's mock GSTIN and Udyam CSV databases."""

    def __init__(
        self,
        gstin_path: Optional[Path] = None,
        udyam_path: Optional[Path] = None
    ):
        self.gstin_path = (gstin_path or settings.GSTIN_REGISTRY_PATH).resolve()
        self.udyam_path = (udyam_path or settings.UDYAM_REGISTRY_PATH).resolve()

        self._gstin_df: Optional[pd.DataFrame] = None
        self._udyam_df: Optional[pd.DataFrame] = None

    def _load_gstin_registry(self) -> pd.DataFrame:
        if self._gstin_df is None:
            if not self.gstin_path.exists():
                raise FileNotFoundError(f"Mock GSTIN registry not found at: {self.gstin_path}")
            df = pd.read_csv(self.gstin_path, dtype=str)
            df["gstin"] = df["gstin"].str.strip().str.upper()
            self._gstin_df = df
        return self._gstin_df

    def _load_udyam_registry(self) -> pd.DataFrame:
        if self._udyam_df is None:
            if not self.udyam_path.exists():
                raise FileNotFoundError(f"Mock Udyam registry not found at: {self.udyam_path}")
            df = pd.read_csv(self.udyam_path, dtype=str)
            df["udyam_number"] = df["udyam_number"].str.strip().str.upper()
            self._udyam_df = df
        return self._udyam_df

    def verify_gstin(self, gstin: str) -> RegistryVerificationResult:
        """Lookup GSTIN in the mock GST registry.

        Verification logic:
        - Match found: Check status ('Active' vs 'Cancelled' vs 'Suspended').
        - Not found: Flag registry missing.
        """
        clean_gstin = gstin.strip().upper() if gstin else ""
        masked_id = f"{clean_gstin[:4]}***{clean_gstin[-3:]}" if len(clean_gstin) >= 7 else "***"

        if not clean_gstin:
            return RegistryVerificationResult(
                registry_name="mock_gstin_registry",
                searched_identifier="EMPTY",
                found=False,
                checks_passed=False,
                notes=["No GSTIN provided for verification."]
            )

        try:
            df = self._load_gstin_registry()
            matches = df[df["gstin"] == clean_gstin]

            if matches.empty:
                return RegistryVerificationResult(
                    registry_name="mock_gstin_registry",
                    searched_identifier=masked_id,
                    found=False,
                    checks_passed=False,
                    notes=["GSTIN record not found in mock GST registry database."]
                )

            record = matches.iloc[0]
            status = str(record.get("status", "Unknown")).strip()
            legal_name = str(record.get("legal_name", "")).strip()
            trade_name = str(record.get("trade_name", "")).strip()
            address = str(record.get("principal_place_of_business", "")).strip()

            notes = [f"Record located in mock GST database with status: '{status}'."]

            if status == "Active":
                checks_passed = True
            elif status == "Cancelled":
                checks_passed = False
                notes.append("CRITICAL: GSTIN registration is CANCELLED. Onboarding cannot proceed.")
            elif status == "Suspended":
                checks_passed = False
                notes.append("WARNING: GSTIN registration is SUSPENDED. Manual review required.")
            else:
                checks_passed = False
                notes.append(f"Unrecognized registration status '{status}'. Manual review required.")

            return RegistryVerificationResult(
                registry_name="mock_gstin_registry",
                searched_identifier=masked_id,
                found=True,
                status=status,
                registered_name=trade_name or legal_name,
                registered_address=address,
                checks_passed=checks_passed,
                notes=notes
            )

        except Exception as e:
            logger.error(f"Error accessing mock GSTIN registry: {str(e)}")
            return RegistryVerificationResult(
                registry_name="mock_gstin_registry",
                searched_identifier=masked_id,
                found=False,
                checks_passed=False,
                notes=[f"Registry technical error: {str(e)}"]
            )

    def verify_udyam(self, udyam_number: str) -> RegistryVerificationResult:
        """Lookup Udyam registration number in the mock Udyam registry."""
        clean_udyam = udyam_number.strip().upper() if udyam_number else ""
        masked_id = f"{clean_udyam[:8]}***{clean_udyam[-4:]}" if len(clean_udyam) >= 12 else "***"

        if not clean_udyam:
            return RegistryVerificationResult(
                registry_name="mock_udyam_registry",
                searched_identifier="EMPTY",
                found=False,
                checks_passed=False,
                notes=["No Udyam number provided for verification."]
            )

        try:
            df = self._load_udyam_registry()
            matches = df[df["udyam_number"] == clean_udyam]

            if matches.empty:
                return RegistryVerificationResult(
                    registry_name="mock_udyam_registry",
                    searched_identifier=masked_id,
                    found=False,
                    checks_passed=False,
                    notes=["Udyam record not found in mock Udyam registry database."]
                )

            record = matches.iloc[0]
            enterprise_name = str(record.get("enterprise_name", "")).strip()
            ent_type = str(record.get("enterprise_type", "")).strip()
            city = str(record.get("city", "")).strip()
            state = str(record.get("state", "")).strip()
            activity = str(record.get("major_activity", "")).strip()

            address = f"{city}, {state}".strip(", ")
            notes = [
                f"Valid enterprise registered in mock Udyam database.",
                f"Enterprise Category: {ent_type}, Major Activity: {activity}."
            ]

            return RegistryVerificationResult(
                registry_name="mock_udyam_registry",
                searched_identifier=masked_id,
                found=True,
                status=ent_type,
                registered_name=enterprise_name,
                registered_address=address,
                checks_passed=True,
                notes=notes
            )

        except Exception as e:
            logger.error(f"Error accessing mock Udyam registry: {str(e)}")
            return RegistryVerificationResult(
                registry_name="mock_udyam_registry",
                searched_identifier=masked_id,
                found=False,
                checks_passed=False,
                notes=[f"Registry technical error: {str(e)}"]
            )


registry_verification_service = RegistryVerificationService()

