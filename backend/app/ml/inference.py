"""Lead Propensity Scoring Inference Service.

Applies the pre-trained, leakage-free pipeline artifact to score unconverted
and inbound MSME leads, categorizing them into HIGH, MEDIUM, and LOW propensity
bands and generating actionable sales recommendations based on current funnel stage.
"""

import os
from typing import Any, Dict, List, Optional
import joblib
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from app.ml.explainability import ModelExplainer
from app.ml.feature_engineering import extract_features

MODELS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "models")
)
PIPELINE_PATH = os.path.join(MODELS_DIR, "lead_propensity_pipeline.joblib")

STAGE_RECOMMENDED_ACTIONS = {
    "Lead": "Prioritize initial sales outreach; introduce core broadband & telecom offerings.",
    "Contacted": "Schedule structured needs assessment; identify business apps, sites, and budget.",
    "Needs assessed": "Present tailored product quote (Essential/Growth); highlight budget alignment.",
    "Quote accepted": "Guide customer through Smart KYC upload, registry consent, and document review.",
    "KYC complete": "Coordinate circuit provisioning, router delivery, and field engineer dispatch.",
    "Activated": "Service active. Retain customer for 90-day NPS and add-on engagement.",
}


class LeadPropensityInference:
    """Inference engine for lead conversion propensity scoring."""

    def __init__(
        self,
        pipeline_path: str = PIPELINE_PATH,
        high_threshold: float = 0.70,
        medium_threshold: float = 0.40,
    ):
        self.high_threshold = high_threshold
        self.medium_threshold = medium_threshold
        self.pipeline: Optional[Pipeline] = None
        self.explainer: Optional[ModelExplainer] = None
        self.model_version = "1.0.0"
        self._load_model(pipeline_path)

    def _load_model(self, pipeline_path: str) -> None:
        if os.path.exists(pipeline_path):
            self.pipeline = joblib.load(pipeline_path)
            self.explainer = ModelExplainer(self.pipeline)
        else:
            print(
                f"[LeadPropensityInference] Warning: Model artifact not found at {pipeline_path}. Inference degraded."
            )

    def is_ready(self) -> bool:
        return self.pipeline is not None and self.explainer is not None

    def get_propensity_band(self, prob: float) -> str:
        if prob >= self.high_threshold:
            return "HIGH"
        elif prob >= self.medium_threshold:
            return "MEDIUM"
        else:
            return "LOW"

    def get_recommended_action(self, current_stage: str) -> str:
        return STAGE_RECOMMENDED_ACTIONS.get(
            current_stage,
            "Review customer business profile and schedule discovery call.",
        )

    def score_single_lead(self, lead_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates propensity score and explanations for a single lead."""
        if not self.is_ready():
            raise RuntimeError("Lead propensity model pipeline is not loaded.")

        df_single = pd.DataFrame([lead_dict])
        X = extract_features(df_single)
        prob = float(self.pipeline.predict_proba(X)[0, 1])
        band = self.get_propensity_band(prob)

        explanation = self.explainer.explain_lead(X)
        current_stage = str(lead_dict.get("stage_reached", "Lead"))
        action = self.get_recommended_action(current_stage)

        return {
            "lead_id": str(lead_dict.get("lead_id", "UNKNOWN")),
            "conversion_probability": round(prob, 4),
            "propensity_score": round(prob * 100, 1),
            "propensity_band": band,
            "current_stage": current_stage,
            "recommended_next_action": action,
            "positive_factors": explanation["positive_factors"],
            "negative_factors": explanation["negative_factors"],
            "business_summary": explanation["business_summary"],
            "model_version": self.model_version,
        }

    def score_batch(self, leads_df: pd.DataFrame) -> pd.DataFrame:
        """Batch scores leads and appends propensity columns."""
        if not self.is_ready():
            raise RuntimeError("Lead propensity model pipeline is not loaded.")

        X = extract_features(leads_df)
        probs = self.pipeline.predict_proba(X)[:, 1]

        results = leads_df.copy()
        results["conversion_probability"] = np.round(probs, 4)
        results["propensity_score"] = np.round(probs * 100, 1)
        results["propensity_band"] = [self.get_propensity_band(p) for p in probs]
        results["recommended_next_action"] = [
            self.get_recommended_action(str(s))
            for s in leads_df.get("stage_reached", ["Lead"] * len(leads_df))
        ]

        return results


# Global singleton inference instance
lead_propensity_inference = LeadPropensityInference()

