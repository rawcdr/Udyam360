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
        "Referred by existing partner/customer (+166% conversion odds, OR 2.66)",
        "Not a referral lead",
    ),
    "lead_source_Inbound call": (
        "High-intent inbound phone inquiry (+32% conversion odds, OR 1.32)",
        "Outbound / passive lead origin",
    ),
    "lead_source_Channel partner": (
        "Enterprise channel partner source (+31% conversion odds, OR 1.31)",
        "Direct self-sourced lead",
    ),
    "lead_source_Field sales": (
        "Direct field sales engagement (+4% conversion odds, OR 1.04)",
        "Non-field lead channel",
    ),
    "lead_source_Website form": (
        "Standard website inbound webform (-41% conversion odds, OR 0.59)",
        "Non-webform origin",
    ),
    "lead_source_WhatsApp campaign": (
        "Low-conversion WhatsApp campaign origin (-72% conversion odds, OR 0.28)",
        "Non-campaign channel",
    ),
    "has_gstin_Y": (
        "Verified GSTIN registration declared (+97% conversion odds, OR 1.97)",
        "Unregistered business entity",
    ),
    "has_gstin_N": (
        "Exempt / non-registered entity (-59% conversion odds, OR 0.41)",
        "Lacks GSTIN registration",
    ),
    "has_udyam_Y": (
        "Formal Udyam MSME certification (+3% conversion odds, OR 1.03)",
        "No Udyam certification",
    ),
    "has_udyam_N": (
        "No Udyam certificate on record (-22% conversion odds, OR 0.78)",
        "Has Udyam certification",
    ),
    "segment_Professional offices": (
        "High-LTV professional office vertical (+27% conversion odds, OR 1.27)",
        "Non-office segment",
    ),
    "segment_Small multi-site businesses": (
        "Multi-branch footprint requiring multi-CPE networking (+8% conversion odds, OR 1.08)",
        "Single branch entity",
    ),
    "segment_Small manufacturers": (
        "Small manufacturing segment (-15% conversion odds, OR 0.85)",
        "Non-manufacturing vertical",
    ),
    "segment_Micro retail & services": (
        "Micro retail archetype (-32% conversion odds, OR 0.68)",
        "Non-micro-retail vertical",
    ),
    "preferred_language_Punjabi": (
        "Vernacular Punjabi language preference (-63% conversion odds, OR 0.37)",
        "Standard collateral language",
    ),
    "business_type_Real estate agency": (
        "High-velocity real estate agency vertical (+110% conversion odds, OR 2.10)",
        "Non-real-estate vertical",
    ),
    "business_type_Mobile repair shop": (
        "High digital adoption mobile repair vertical (+91% conversion odds, OR 1.91)",
        "Non-repair vertical",
    ),
    "business_type_Auto-parts unit": (
        "Traditional auto-parts industrial vertical (-53% conversion odds, OR 0.47)",
        "Non-auto-parts vertical",
    ),
    "business_type_Restaurant chain": (
        "Multi-outlet restaurant dining vertical (-49% conversion odds, OR 0.51)",
        "Non-restaurant vertical",
    ),
    "business_type_Pharmacy": (
        "Neighborhood pharmacy retail vertical (-47% conversion odds, OR 0.53)",
        "Non-pharmacy vertical",
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
        "Commercial broadband intent flagged",
        "No commercial broadband requirement declared",
    ),
    "has_cloud_security_interest": (
        "Interest in cloud backup or surveillance",
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
            "non_causal_note": "Model associations represent conditional odds ratios within this observational dataset, not causal effects.",
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
