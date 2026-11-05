"""Lead Prioritization and Scoring Service for Udyam360.

Applies the trained ML propensity model across lead records, ranks leads,
generates explainability rationales, and supports operational sales action logging.
"""

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import pandas as pd

from app.ml.inference import lead_propensity_inference
from app.services.analytics_service import DEFAULT_LEADS_CSV


class LeadActionRecord:
    """Audit log entry for sales follow-up interactions."""

    def __init__(
        self,
        lead_id: str,
        action_type: str,
        notes: str,
        rep_name: str = "Enterprise Sales Rep",
    ):
        self.lead_id = lead_id
        self.action_type = action_type
        self.notes = notes
        self.rep_name = rep_name
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lead_id": self.lead_id,
            "action_type": self.action_type,
            "notes": self.notes,
            "rep_name": self.rep_name,
            "timestamp": self.timestamp,
        }


class LeadScoringService:
    """Manages lead scoring, ranking, filtering, pagination, and sales follow-up notes."""

    def __init__(self, dataset_path: str = DEFAULT_LEADS_CSV):
        self.dataset_path = dataset_path
        self._scored_df: Optional[pd.DataFrame] = None
        self._lead_lookup: Dict[str, Dict[str, Any]] = {}
        self._sales_actions: Dict[str, List[LeadActionRecord]] = {}

    def _ensure_scored_data(self) -> pd.DataFrame:
        """Precomputes and caches propensity scores across lead records for fast sub-ms queries."""
        if self._scored_df is None:
            if not os.path.exists(self.dataset_path):
                raise FileNotFoundError(f"Lead dataset not found at {self.dataset_path}")

            raw_df = pd.read_csv(self.dataset_path)
            # Batch score using ML model
            scored = lead_propensity_inference.score_batch(raw_df)
            self._scored_df = scored

            # Populate lead lookup index
            for _, row in scored.iterrows():
                l_id = str(row["lead_id"])
                self._lead_lookup[l_id] = row.to_dict()

        return self._scored_df

    def get_leads_paginated(
        self,
        segment: Optional[str] = None,
        stage: Optional[str] = None,
        band: Optional[str] = None,
        search: Optional[str] = None,
        unconverted_only: bool = True,
        sort_by: str = "propensity_score",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """Filters, sorts, and paginates scored leads."""
        df = self._ensure_scored_data().copy()

        # Filter unconverted leads by default for sales prioritization
        if unconverted_only and "outcome" in df.columns:
            df = df[df["outcome"] != "Activated"]

        # Category filters
        if segment and segment != "All":
            df = df[df["segment"].str.lower() == segment.strip().lower()]

        if stage and stage != "All":
            df = df[df["stage_reached"].str.lower() == stage.strip().lower()]

        if band and band != "All":
            df = df[df["propensity_band"].str.upper() == band.strip().upper()]

        # Search filter across lead_id, business_name, city
        if search and search.strip():
            query = search.strip().lower()
            mask = (
                df["lead_id"].str.lower().str.contains(query, na=False)
                | df["business_name"].str.lower().str.contains(query, na=False)
                | df["city"].str.lower().str.contains(query, na=False)
            )
            df = df[mask]

        total_matching = len(df)

        # Sorting
        ascending = sort_order.lower() == "asc"
        valid_sort_cols = [
            "propensity_score",
            "conversion_probability",
            "monthly_telecom_spend_inr",
            "employee_count",
            "num_sites",
            "created_date",
            "lead_id",
        ]
        chosen_col = sort_by if sort_by in valid_sort_cols else "propensity_score"
        df = df.sort_values(by=chosen_col, ascending=ascending)

        # Pagination
        start = (page - 1) * page_size
        end = start + page_size
        page_items = df.iloc[start:end]

        leads_list = []
        for _, row in page_items.iterrows():
            l_dict = row.to_dict()
            lead_id = str(l_dict["lead_id"])

            # Explain lead on the fly
            exp = lead_propensity_inference.explainer.explain_lead(
                pd.DataFrame([l_dict])
            )
            l_dict["positive_factors"] = exp["positive_factors"]
            l_dict["negative_factors"] = exp["negative_factors"]
            l_dict["business_summary"] = exp["business_summary"]
            l_dict["actions_count"] = len(self._sales_actions.get(lead_id, []))
            leads_list.append(l_dict)

        total_pages = max(1, (total_matching + page_size - 1) // page_size)

        return {
            "total_count": total_matching,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "leads": leads_list,
        }

    def get_lead_detail(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves individual lead profile, propensity score, and explanations."""
        self._ensure_scored_data()
        clean_id = lead_id.strip()
        record = self._lead_lookup.get(clean_id)
        if not record:
            return None

        exp = lead_propensity_inference.explainer.explain_lead(
            pd.DataFrame([record])
        )
        actions = [a.to_dict() for a in self._sales_actions.get(clean_id, [])]

        return {
            "lead_id": clean_id,
            "business_name": record.get("business_name"),
            "business_type": record.get("business_type"),
            "segment": record.get("segment"),
            "city": record.get("city"),
            "city_tier": record.get("city_tier"),
            "state": record.get("state"),
            "lead_source": record.get("lead_source"),
            "employee_count": record.get("employee_count"),
            "num_sites": record.get("num_sites"),
            "annual_turnover_band": record.get("annual_turnover_band"),
            "has_gstin": record.get("has_gstin"),
            "has_udyam": record.get("has_udyam"),
            "current_internet": record.get("current_internet"),
            "current_provider": record.get("current_provider"),
            "monthly_telecom_spend_inr": record.get("monthly_telecom_spend_inr"),
            "products_of_interest": record.get("products_of_interest"),
            "contact_role": record.get("contact_role"),
            "stage_reached": record.get("stage_reached"),
            "outcome": record.get("outcome"),
            "conversion_probability": record.get("conversion_probability"),
            "propensity_score": record.get("propensity_score"),
            "propensity_band": record.get("propensity_band"),
            "recommended_next_action": record.get("recommended_next_action"),
            "positive_factors": exp["positive_factors"],
            "negative_factors": exp["negative_factors"],
            "business_summary": exp["business_summary"],
            "model_version": lead_propensity_inference.model_version,
            "sales_action_history": actions,
        }

    def get_propensity_overview(self) -> Dict[str, Any]:
        """Provides aggregate distribution of propensity bands across unconverted leads."""
        df = self._ensure_scored_data()
        unconverted = df[df["outcome"] != "Activated"] if "outcome" in df.columns else df

        total = len(unconverted)
        high = int((unconverted["propensity_band"] == "HIGH").sum())
        medium = int((unconverted["propensity_band"] == "MEDIUM").sum())
        low = int((unconverted["propensity_band"] == "LOW").sum())

        return {
            "total_unconverted_leads": total,
            "high_propensity_count": high,
            "high_propensity_pct": round((high / total * 100), 2) if total > 0 else 0.0,
            "medium_propensity_count": medium,
            "medium_propensity_pct": round((medium / total * 100), 2) if total > 0 else 0.0,
            "low_propensity_count": low,
            "low_propensity_pct": round((low / total * 100), 2) if total > 0 else 0.0,
            "thresholds": {
                "high": lead_propensity_inference.high_threshold,
                "medium": lead_propensity_inference.medium_threshold,
            },
            "model_version": lead_propensity_inference.model_version,
        }

    def record_sales_action(
        self,
        lead_id: str,
        action_type: str,
        notes: str,
        rep_name: str = "Enterprise Sales Rep",
    ) -> Dict[str, Any]:
        """Records a follow-up action audit entry without modifying the original dataset."""
        self._ensure_scored_data()
        clean_id = lead_id.strip()
        if clean_id not in self._lead_lookup:
            raise KeyError(f"Lead ID '{clean_id}' does not exist.")

        action = LeadActionRecord(
            lead_id=clean_id,
            action_type=action_type,
            notes=notes,
            rep_name=rep_name,
        )
        if clean_id not in self._sales_actions:
            self._sales_actions[clean_id] = []
        self._sales_actions[clean_id].append(action)

        return action.to_dict()


# Global singleton instance
lead_scoring_service = LeadScoringService()

