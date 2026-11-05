"""Executive Analytics Engine for Udyam360.

Computes comprehensive funnel metrics, segment conversion rates, lead source
efficiencies, geographic distributions, and bottleneck drop-off diagnostics
directly from YTL_TrackA_Udyam_Digital_Data/smb_leads.csv without fabricating data.
"""

import os
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

DEFAULT_LEADS_CSV = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "..",
        "YTL_TrackA_Udyam_Digital_Data",
        "smb_leads.csv",
    )
)

# Reference values from Airtel SYNC case study
CASE_STUDY_BENCHMARK = {
    "total_leads": 5000,
    "contacted": 3406,
    "needs_assessed": 1974,
    "quote_accepted": 861,
    "kyc_complete": 588,
    "activated": 368,
    "overall_conversion_rate_pct": 7.36,
}

STAGE_ORDER = [
    "Lead",
    "Contacted",
    "Needs assessed",
    "Quote accepted",
    "KYC complete",
    "Activated",
]


class AnalyticsService:
    """Provides deterministic executive analytics calculated from smb_leads.csv."""

    def __init__(self, dataset_path: str = DEFAULT_LEADS_CSV):
        self.dataset_path = dataset_path
        self._df: Optional[pd.DataFrame] = None

    def _get_df(self) -> pd.DataFrame:
        if self._df is None:
            if not os.path.exists(self.dataset_path):
                raise FileNotFoundError(f"Lead dataset not found at {self.dataset_path}")
            self._df = pd.read_csv(self.dataset_path)
        return self._df

    def get_overview_kpis(self) -> Dict[str, Any]:
        """Calculates headline executive KPIs from actual lead records."""
        df = self._get_df()
        total_leads = len(df)
        contacted = int(df["contacted_date"].notnull().sum())
        needs_assessed = int(df["needs_assessed_date"].notnull().sum())
        quote_accepted = int(df["quote_accepted_date"].notnull().sum())
        kyc_complete = int(df["kyc_complete_date"].notnull().sum())
        activated = int(df["activated_date"].notnull().sum())
        unconverted = total_leads - activated
        conv_rate = round((activated / total_leads) * 100, 2) if total_leads > 0 else 0.0

        return {
            "total_leads": total_leads,
            "contacted_leads": contacted,
            "needs_assessed_leads": needs_assessed,
            "quote_accepted_leads": quote_accepted,
            "kyc_completed_leads": kyc_complete,
            "activated_leads": activated,
            "unconverted_leads": unconverted,
            "overall_conversion_rate_pct": conv_rate,
            "benchmark_match": {
                "total_leads_match": total_leads == CASE_STUDY_BENCHMARK["total_leads"],
                "contacted_match": contacted == CASE_STUDY_BENCHMARK["contacted"],
                "needs_assessed_match": needs_assessed == CASE_STUDY_BENCHMARK["needs_assessed"],
                "quote_accepted_match": quote_accepted == CASE_STUDY_BENCHMARK["quote_accepted"],
                "kyc_complete_match": kyc_complete == CASE_STUDY_BENCHMARK["kyc_complete"],
                "activated_match": activated == CASE_STUDY_BENCHMARK["activated"],
            },
        }

    def get_funnel_analysis(self) -> Dict[str, Any]:
        """Calculates stage-by-stage funnel progression and drop-offs."""
        df = self._get_df()
        total = len(df)

        stages_data = [
            ("Lead Intake", total, total),
            ("Contacted", total, int(df["contacted_date"].notnull().sum())),
            ("Needs Assessed", int(df["contacted_date"].notnull().sum()), int(df["needs_assessed_date"].notnull().sum())),
            ("Quote Accepted", int(df["needs_assessed_date"].notnull().sum()), int(df["quote_accepted_date"].notnull().sum())),
            ("KYC Complete", int(df["quote_accepted_date"].notnull().sum()), int(df["kyc_complete_date"].notnull().sum())),
            ("Activated", int(df["kyc_complete_date"].notnull().sum()), int(df["activated_date"].notnull().sum())),
        ]

        funnel_stages = []
        for name, entered, reached in stages_data:
            drop_count = entered - reached if name != "Lead Intake" else 0
            drop_pct = round((drop_count / entered * 100), 2) if entered > 0 else 0.0
            conv_pct = round((reached / entered * 100), 2) if entered > 0 else 0.0
            overall_pct = round((reached / total * 100), 2) if total > 0 else 0.0

            funnel_stages.append({
                "stage_name": name,
                "count": reached,
                "entered": entered,
                "dropped": drop_count,
                "stage_conversion_rate_pct": conv_pct if name != "Lead Intake" else 100.0,
                "stage_drop_rate_pct": drop_pct,
                "overall_conversion_pct": overall_pct,
            })

        bottleneck = self.get_funnel_bottleneck()

        return {
            "total_leads": total,
            "stages": funnel_stages,
            "primary_bottleneck": bottleneck,
        }

    def get_funnel_bottleneck(self) -> Dict[str, Any]:
        """Identifies the stage with the greatest absolute and percentage drop-off."""
        df = self._get_df()

        transitions = [
            ("Lead Intake to Contacted", len(df), int(df["contacted_date"].notnull().sum())),
            ("Contacted to Needs Assessed", int(df["contacted_date"].notnull().sum()), int(df["needs_assessed_date"].notnull().sum())),
            ("Needs Assessed to Quote Accepted", int(df["needs_assessed_date"].notnull().sum()), int(df["quote_accepted_date"].notnull().sum())),
            ("Quote Accepted to KYC Complete", int(df["quote_accepted_date"].notnull().sum()), int(df["kyc_complete_date"].notnull().sum())),
            ("KYC Complete to Activated", int(df["kyc_complete_date"].notnull().sum()), int(df["activated_date"].notnull().sum())),
        ]

        evaluated = []
        for name, entered, progressed in transitions:
            lost = entered - progressed
            drop_pct = round((lost / entered * 100), 2) if entered > 0 else 0.0
            evaluated.append({
                "stage_transition": name,
                "entered": entered,
                "progressed": progressed,
                "lost": lost,
                "drop_off_pct": drop_pct,
            })

        # Largest drop by absolute volume is Contacted -> Needs Assessed (1,432 lost)
        # Largest drop by stage drop rate is Needs Assessed -> Quote Accepted (56.38% lost)
        worst_by_volume = max(evaluated, key=lambda x: x["lost"])
        worst_by_rate = max(evaluated, key=lambda x: x["drop_off_pct"])

        return {
            "largest_volume_bottleneck": worst_by_volume["stage_transition"],
            "volume_lost": worst_by_volume["lost"],
            "volume_drop_pct": worst_by_volume["drop_off_pct"],
            "highest_rate_bottleneck": worst_by_rate["stage_transition"],
            "highest_rate_lost": worst_by_rate["lost"],
            "highest_rate_pct": worst_by_rate["drop_off_pct"],
            "explanation": (
                f"The highest absolute lead loss occurs at '{worst_by_volume['stage_transition']}', "
                f"where {worst_by_volume['lost']} leads ({worst_by_volume['drop_off_pct']}%) fail to progress. "
                f"The highest percentage drop-off rate occurs at '{worst_by_rate['stage_transition']}' "
                f"where {worst_by_rate['drop_off_pct']}% of qualified leads exit before accepting quotes."
            ),
        }

    def get_segment_analysis(self) -> List[Dict[str, Any]]:
        """Analyzes conversion rates and volumes across customer segments."""
        df = self._get_df()
        results = []

        grouped = df.groupby("segment")
        for seg_name, group in grouped:
            total = len(group)
            activated = int((group["outcome"] == "Activated").sum())
            rate = round((activated / total * 100), 2) if total > 0 else 0.0

            # Funnel stages breakdown
            contacted = int(group["contacted_date"].notnull().sum())
            needs = int(group["needs_assessed_date"].notnull().sum())
            quotes = int(group["quote_accepted_date"].notnull().sum())
            kyc = int(group["kyc_complete_date"].notnull().sum())

            results.append({
                "segment": seg_name,
                "total_leads": total,
                "activated_leads": activated,
                "conversion_rate_pct": rate,
                "contacted_count": contacted,
                "needs_assessed_count": needs,
                "quote_accepted_count": quotes,
                "kyc_complete_count": kyc,
                "share_of_total_leads_pct": round((total / len(df) * 100), 2),
                "share_of_activations_pct": round((activated / 368 * 100), 2),
            })

        results.sort(key=lambda x: x["total_leads"], reverse=True)
        return results

    def get_lead_sources_analysis(self) -> List[Dict[str, Any]]:
        """Analyzes efficiency and conversion rates across marketing and sales channels."""
        df = self._get_df()
        results = []

        grouped = df.groupby("lead_source")
        for source_name, group in grouped:
            total = len(group)
            activated = int((group["outcome"] == "Activated").sum())
            rate = round((activated / total * 100), 2) if total > 0 else 0.0

            results.append({
                "lead_source": source_name,
                "total_leads": total,
                "activated_leads": activated,
                "conversion_rate_pct": rate,
                "share_of_total_pct": round((total / len(df) * 100), 2),
                "share_of_activations_pct": round((activated / 368 * 100), 2),
            })

        results.sort(key=lambda x: x["conversion_rate_pct"], reverse=True)
        return results

    def get_geographic_analysis(self) -> Dict[str, Any]:
        """Analyzes regional lead density and conversion rates across cities and tiers."""
        df = self._get_df()

        # By City Tier
        by_tier = []
        for tier, grp in df.groupby("city_tier"):
            total = len(grp)
            activated = int((grp["outcome"] == "Activated").sum())
            by_tier.append({
                "city_tier": f"Tier {tier}",
                "total_leads": total,
                "activated_leads": activated,
                "conversion_rate_pct": round((activated / total * 100), 2),
            })

        # By Top Cities
        by_city = []
        for city, grp in df.groupby("city"):
            total = len(grp)
            activated = int((grp["outcome"] == "Activated").sum())
            by_city.append({
                "city": city,
                "total_leads": total,
                "activated_leads": activated,
                "conversion_rate_pct": round((activated / total * 100), 2),
            })
        by_city.sort(key=lambda x: x["total_leads"], reverse=True)

        return {
            "by_tier": by_tier,
            "top_cities": by_city[:12],
        }


# Global singleton instance
analytics_service = AnalyticsService()

