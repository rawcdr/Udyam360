"""Model registry and evaluation reporting loader for Udyam360 ML service."""

import json
import os
from typing import Any, Dict, Optional

MODELS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "models")
)
METADATA_PATH = os.path.join(MODELS_DIR, "model_metadata.json")
EVALUATION_PATH = os.path.join(MODELS_DIR, "evaluation_report.json")


class ModelRegistry:
    """Manages model artifacts metadata and evaluation reports."""

    def __init__(
        self,
        metadata_path: str = METADATA_PATH,
        eval_path: str = EVALUATION_PATH,
    ):
        self.metadata_path = metadata_path
        self.eval_path = eval_path
        self._cached_metadata: Optional[Dict[str, Any]] = None
        self._cached_eval: Optional[Dict[str, Any]] = None

    def get_metadata(self) -> Dict[str, Any]:
        """Loads and returns model training metadata and top feature weights."""
        if self._cached_metadata is None:
            if os.path.exists(self.metadata_path):
                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    self._cached_metadata = json.load(f)
            else:
                self._cached_metadata = {
                    "model_name": "LogisticRegression (Uninitialized)",
                    "model_version": "1.0.0",
                    "status": "NOT_TRAINED",
                    "evaluation": {},
                }
        return self._cached_metadata

    def get_evaluation_report(self) -> Dict[str, Any]:
        """Loads full candidate model comparison and held-out test evaluation."""
        if self._cached_eval is None:
            if os.path.exists(self.eval_path):
                with open(self.eval_path, "r", encoding="utf-8") as f:
                    self._cached_eval = json.load(f)
            else:
                self._cached_eval = {
                    "comparison": {},
                    "selected_model": "None",
                    "held_out_test_metrics": {},
                    "feature_importance": [],
                }
        return self._cached_eval

    def get_feature_importances(self) -> list:
        """Returns ordered list of feature weights / importances."""
        eval_data = self.get_evaluation_report()
        return eval_data.get("feature_importance", [])


# Global singleton instance
model_registry = ModelRegistry()

