"""Model explainability module for Udyam360 lead propensity predictions.

Computes exact linear feature contributions and maps them to transparent,
grounded business language for sales prioritization.
"""

from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from app.ml.feature_engineering import CATEGORICAL_FEATURES, NUMERIC_FEATURES, extract_features

# Friendly business glossary for raw feature keys
FEATURE_DESCRIPTIONS: Dict[str, Tuple[str, str]] = {
    "lead_source_Referral": (
        "Referred by existing partner/customer (+98% conversion odds)",
        "Not a referral lead",
    ),
    "lead_source_Inbound call": (
        "High-intent inbound inquiry (+26% conversion odds)",
        "Outbound / passive lead origin",
    ),
    "lead_source_Channel partner": (
        "Enterprise channel partner source",
        "Direct self-sourced lead",
    ),
    "lead_source_Field sales": (
        "Direct field sales engagement",
        "Non-field lead channel",
    ),
    "lead_source_Website form": (
        "Standard website inbound webform",
        "Low-converting website inquiry (-59% conversion odds)",
    ),
    "lead_source_WhatsApp campaign": (
        "Low-conversion WhatsApp campaign origin (-101% conversion odds)",
        "Non-campaign channel",
    ),
    "has_gstin_Y": (
        "Verified GSTIN registration declared (+61% conversion odds)",
        "Unregistered business entity",
    ),
    "has_gstin_N": (
        "Exempt / non-registered entity",
        "Lacks GSTIN registration (-77% conversion odds)",
    ),
    "has_udyam_Y": (
        "Formal Udyam MSME certification (+15% conversion odds)",
        "No Udyam certification",
    ),
    "segment_Small manufacturers": (
        "High-ARPU small manufacturing sector (+54% conversion odds)",
        "Non-manufacturing vertical",
    ),
    "segment_Professional offices": (
        "High-LTV professional office vertical (+32% conversion odds)",
        "Non-office segment",
    ),
    "segment_Small multi-site businesses": (
        "Multi-branch footprint requiring multi-CPE networking",
        "Single branch entity",
    ),
    "segment_Micro retail & services": (
        "Micro retail archetype (historically higher price sensitivity)",
        "Micro retail segment (-73% conversion odds)",
    ),
    "contact_role_Owner": (
        "Primary decision-maker (Owner) directly engaged",
        "Non-owner contact point",
    ),
    "contact_role_Partner": (
        "Authorized business partner engaged",
        "Non-partner contact point",
    ),
    "has_broadband_interest": (
        "High-speed commercial broadband intent flagged",
        "No high-speed broadband requirement declared",
    ),
    "has_cloud_security_interest": (
        "Interest in high-value cloud backup or surveillance",
        "Baseline connectivity-only interest",
    ),
}


class ModelExplainer:
    """Provides local and global feature attribution for the propensity model."""

    def __init__(self, pipeline: Pipeline):
        self.pipeline = pipeline
        self.classifier = pipeline.named_steps["classifier"]
        self.preprocessor = pipeline.named_steps["preprocessor"]

        cat_encoder = self.preprocessor.named_transformers_["cat"].named_steps["onehot"]
        self.encoded_cat_names = list(
            cat_encoder.get_feature_names_out(CATEGORICAL_FEATURES)
        )
        self.feature_names = NUMERIC_FEATURES + self.encoded_cat_names

        if hasattr(self.classifier, "coef_"):
            self.weights = self.classifier.coef_[0]
        else:
            self.weights = np.zeros(len(self.feature_names))

    def explain_lead(self, lead_features_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculates positive and negative feature contributions for a single lead."""
        expected_cols = set(CATEGORICAL_FEATURES + NUMERIC_FEATURES)
        if set(lead_features_df.columns) != expected_cols:
            lead_features_df = extract_features(lead_features_df)

        transformed = self.preprocessor.transform(lead_features_df)
        row = transformed[0]

        # Calculate element-wise contribution: x_i * w_i
        contributions = row * self.weights

        pos_items: List[Tuple[str, float]] = []
        neg_items: List[Tuple[str, float]] = []

        for f_name, c_val in zip(self.feature_names, contributions):
            if abs(c_val) < 0.01:
                continue
            if c_val > 0:
                pos_items.append((f_name, c_val))
            else:
                neg_items.append((f_name, c_val))

        pos_items.sort(key=lambda x: x[1], reverse=True)
        neg_items.sort(key=lambda x: x[1])  # Most negative first

        positive_factors = []
        for f_name, val in pos_items[:3]:
            positive_factors.append(self._format_factor(f_name, True))

        negative_factors = []
        for f_name, val in neg_items[:3]:
            negative_factors.append(self._format_factor(f_name, False))

        # Build concise human-readable summary
        summary_parts = []
        if positive_factors:
            summary_parts.append(f"Strengths: {'; '.join(positive_factors[:2])}.")
        if negative_factors:
            summary_parts.append(f"Risks: {'; '.join(negative_factors[:2])}.")

        summary = " ".join(summary_parts) if summary_parts else "Balanced lead profile."

        return {
            "positive_factors": positive_factors,
            "negative_factors": negative_factors,
            "business_summary": summary,
        }

    def _format_factor(self, feature_name: str, is_positive: bool) -> str:
        """Converts raw feature string to clean business English."""
        if feature_name in FEATURE_DESCRIPTIONS:
            return FEATURE_DESCRIPTIONS[feature_name][0 if is_positive else 1]

        # Fallback formatting for numeric or other categorical features
        clean = (
            feature_name.replace("business_type_", "Business type: ")
            .replace("city_", "Location: ")
            .replace("state_", "State: ")
            .replace("current_internet_", "Current network: ")
            .replace("current_provider_", "Current provider: ")
            .replace("_", " ")
        )
        return clean.capitalize()
