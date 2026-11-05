"""Feature engineering and allowlist schema for lead propensity scoring.

Ensures strict zero-leakage: Excludes all downstream funnel milestones,
post-quote commercial specs, and post-activation operational metrics.
"""

from typing import Dict, List, Tuple, Any
import numpy as np
import pandas as pd

# Safe allowlist features available at lead intake time
CATEGORICAL_FEATURES: List[str] = [
    "lead_source",
    "business_type",
    "segment",
    "city",
    "state",
    "preferred_language",
    "annual_turnover_band",
    "has_gstin",
    "has_udyam",
    "current_internet",
    "current_provider",
    "contact_role",
]

NUMERIC_FEATURES: List[str] = [
    "city_tier",
    "employee_count",
    "num_sites",
    "monthly_telecom_spend_inr",
    "created_day_of_week",
    "created_month",
    "num_products_of_interest",
    "has_broadband_interest",
    "has_voice_interest",
    "has_cloud_security_interest",
    "spend_per_employee",
    "spend_per_site",
]

# Explicit downstream leakage blacklist to be rejected
LEAKAGE_BLACKLIST: List[str] = [
    "outcome",
    "stage_reached",
    "drop_reason",
    "contacted_date",
    "needs_assessed_date",
    "quote_accepted_date",
    "kyc_complete_date",
    "activated_date",
    "days_lead_to_activation",
    "customer_follow_up_calls",
    "bundle_products",
    "monthly_bundle_value_inr",
    "one_time_setup_inr",
    "contract_months",
    "churned_within_6_months",
    "nps_score",
    "acquisition_cost_inr",
]


def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    """Transforms raw lead records into the safe allowlist feature space."""
    data = df.copy()

    # Temporal features from created_date (if available, else defaults)
    if "created_date" in data.columns:
        dates = pd.to_datetime(data["created_date"], errors="coerce")
        data["created_day_of_week"] = dates.dt.day_of_week.fillna(2).astype(int)
        data["created_month"] = dates.dt.month.fillna(5).astype(int)
    else:
        data["created_day_of_week"] = 2
        data["created_month"] = 5

    # Products of interest intent flags
    if "products_of_interest" in data.columns:
        prods = data["products_of_interest"].astype(str)
        data["num_products_of_interest"] = prods.apply(
            lambda x: len(x.split(";")) if x not in ["nan", "None", ""] else 0
        )
        data["has_broadband_interest"] = prods.apply(
            lambda x: int("P01" in x or "P02" in x)
        )
        data["has_voice_interest"] = prods.apply(
            lambda x: int("P07" in x or "P08" in x)
        )
        data["has_cloud_security_interest"] = prods.apply(
            lambda x: int(any(p in x for p in ["P14", "P19", "P20", "P21", "P22"]))
        )
    else:
        data["num_products_of_interest"] = 0
        data["has_broadband_interest"] = 0
        data["has_voice_interest"] = 0
        data["has_cloud_security_interest"] = 0

    # Financial intensity ratios
    spend = data.get("monthly_telecom_spend_inr", 3000).astype(float)
    employees = data.get("employee_count", 5).astype(float).clip(lower=1)
    sites = data.get("num_sites", 1).astype(float).clip(lower=1)

    data["spend_per_employee"] = spend / employees
    data["spend_per_site"] = spend / sites

    # Impute missing categorical entries with "Missing"
    for col in CATEGORICAL_FEATURES:
        if col in data.columns:
            data[col] = data[col].fillna("Missing").astype(str)
        else:
            data[col] = "Missing"

    # Ensure numeric columns are properly typed
    for col in NUMERIC_FEATURES:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce").fillna(0.0)
        else:
            data[col] = 0.0

    # Select solely the allowlist columns
    return data[CATEGORICAL_FEATURES + NUMERIC_FEATURES]


def prepare_training_data(
    df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
    """Prepares feature matrix X, target vector y, and lead IDs from raw dataset."""
    lead_ids = df["lead_id"].copy() if "lead_id" in df.columns else pd.Series(df.index)
    if "outcome" not in df.columns:
        raise ValueError("Dataset does not contain required 'outcome' column.")

    y = (df["outcome"] == "Activated").astype(int)
    X = extract_features(df)
    return X, y, lead_ids

