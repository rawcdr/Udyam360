"""Central application configuration for Udyam360."""

import os
from pathlib import Path
from typing import List
from pydantic import BaseModel
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# Load environment variables
for env_path in [BASE_DIR / ".env", BASE_DIR / "backend" / ".env", Path(".env"), Path("backend/.env")]:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        break


def find_dataset_dir() -> Path:
    """Discover dataset directory dynamically without hardcoded absolute paths."""
    candidates = [
        BASE_DIR / "YTL_TrackA_Udyam_Digital_Data",
        Path("YTL_TrackA_Udyam_Digital_Data"),
        Path("../YTL_TrackA_Udyam_Digital_Data"),
        Path("../../YTL_TrackA_Udyam_Digital_Data"),
    ]
    for c in candidates:
        if c.is_dir() and (c / "product_catalogue.csv").exists():
            return c.resolve()
    # Default to base_dir / YTL_TrackA_Udyam_Digital_Data
    return (BASE_DIR / "YTL_TrackA_Udyam_Digital_Data").resolve()


class Settings:
    PROJECT_NAME: str = "Udyam360"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "AI-Powered Digital Onboarding Platform for Indian MSMEs"
    
    # Dataset Paths
    DATASET_DIR: Path = find_dataset_dir()
    PRODUCT_CATALOGUE_PATH: Path = DATASET_DIR / "product_catalogue.csv"
    SMB_LEADS_PATH: Path = DATASET_DIR / "smb_leads.csv"
    GSTIN_REGISTRY_PATH: Path = DATASET_DIR / "mock_gstin_registry.csv"
    UDYAM_REGISTRY_PATH: Path = DATASET_DIR / "mock_udyam_registry.csv"
    KYC_DOCUMENTS_DIR: Path = DATASET_DIR / "kyc_documents"

    # Synthetic baseline date per hackathon rules
    BASELINE_DATE: str = "2026-07-15"

    # Gemini & LLM Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")
    GEMINI_REQUEST_TIMEOUT_SECONDS: int = int(os.getenv("GEMINI_REQUEST_TIMEOUT_SECONDS", "30"))
    MAX_CONVERSATION_HISTORY: int = int(os.getenv("MAX_CONVERSATION_HISTORY", "20"))
    MAX_ADVISOR_RETRIES: int = int(os.getenv("MAX_ADVISOR_RETRIES", "2"))
    ADVISOR_ENABLED: bool = os.getenv("ADVISOR_ENABLED", "True").lower() in ("true", "1")

    # Default Recommendation Scoring Weights
    WEIGHT_REQUIREMENT_MATCH: float = 0.50
    WEIGHT_BUDGET_FIT: float = 0.25
    WEIGHT_CATALOGUE_ELIGIBILITY: float = 0.15
    WEIGHT_SEGMENT_SUITABILITY: float = 0.10

    # Supported Target Segments
    SEGMENT_MICRO_RETAIL: str = "micro"
    SEGMENT_PROFESSIONAL_OFFICE: str = "prof"
    SEGMENT_MULTI_SITE: str = "multi"
    SEGMENT_MANUFACTURING: str = "mfg"


settings = Settings()

