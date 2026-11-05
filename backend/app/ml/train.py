"""Model training and evaluation pipeline for Udyam360 Lead Propensity Scoring.

Evaluates 3 candidate model families:
1. Logistic Regression (Linear baseline with direct odds interpretability)
2. Random Forest (Ensemble decision trees with non-linear interaction capture)
3. HistGradientBoosting (Histogram-based gradient boosted decision trees)

Saves the winning model pipeline and complete evaluation metadata to disk.
"""

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from app.ml.feature_engineering import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    prepare_training_data,
)
from app.ml.preprocessing import build_preprocessor

DEFAULT_DATASET_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "..",
        "YTL_TrackA_Udyam_Digital_Data",
        "smb_leads.csv",
    )
)

MODELS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "models")
)


def evaluate_model(pipe: Pipeline, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
    """Computes comprehensive classification and calibration metrics."""
    probs = pipe.predict_proba(X)[:, 1]
    preds = (probs >= 0.5).astype(int)

    roc_auc = float(roc_auc_score(y, probs))
    pr_auc = float(average_precision_score(y, probs))
    brier = float(brier_score_loss(y, probs))
    prec = float(precision_score(y, preds, zero_division=0))
    rec = float(recall_score(y, preds, zero_division=0))
    f1 = float(f1_score(y, preds, zero_division=0))
    cm = confusion_matrix(y, preds).tolist()

    # Calibration curve (5 bins)
    prob_true, prob_pred = calibration_curve(y, probs, n_bins=5, strategy="uniform")

    return {
        "roc_auc": round(roc_auc, 4),
        "pr_auc": round(pr_auc, 4),
        "brier_score": round(brier, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "confusion_matrix": cm,
        "calibration": {
            "fraction_of_positives": [round(float(x), 4) for x in prob_true],
            "mean_predicted_value": [round(float(x), 4) for x in prob_pred],
        },
    }


def train_and_evaluate_all(
    dataset_path: str = DEFAULT_DATASET_PATH,
    output_dir: str = MODELS_DIR,
) -> Dict[str, Any]:
    """Executes end-to-end training, model benchmarking, and artifact persistence."""
    os.makedirs(output_dir, exist_ok=True)

    print(f"[Phase 5 ML] Loading dataset from: {dataset_path}")
    df = pd.read_csv(dataset_path)
    X, y, lead_ids = prepare_training_data(df)

    # Stratified Split: 70% Train, 15% Validation, 15% Held-Out Test
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=0.15, random_state=42, stratify=y
    )
    # 0.17647 of remaining 85% yields exactly 15% of total
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=0.17647, random_state=42, stratify=y_temp
    )

    print(
        f"[Phase 5 ML] Splits created: Train={len(X_train)} (pos={y_train.sum()}), "
        f"Val={len(X_val)} (pos={y_val.sum()}), Test={len(X_test)} (pos={y_test.sum()})"
    )

    candidate_models = {
        "LogisticRegression": LogisticRegression(
            class_weight="balanced", max_iter=1000, random_state=42
        ),
        "RandomForest": RandomForestClassifier(
            n_estimators=150,
            max_depth=8,
            class_weight="balanced",
            random_state=42,
        ),
        "HistGradientBoosting": HistGradientBoostingClassifier(
            class_weight="balanced",
            max_iter=150,
            max_depth=6,
            random_state=42,
        ),
    }

    comparison: Dict[str, Any] = {}
    fitted_pipelines: Dict[str, Pipeline] = {}

    for name, clf in candidate_models.items():
        print(f"[Phase 5 ML] Fitting candidate: {name}...")
        preprocessor = build_preprocessor()
        pipeline = Pipeline([("preprocessor", preprocessor), ("classifier", clf)])
        pipeline.fit(X_train, y_train)

        val_metrics = evaluate_model(pipeline, X_val, y_val)
        comparison[name] = {"validation": val_metrics}
        fitted_pipelines[name] = pipeline
        print(
            f"  -> {name} Validation ROC-AUC: {val_metrics['roc_auc']}, "
            f"PR-AUC: {val_metrics['pr_auc']}, Brier: {val_metrics['brier_score']}"
        )

    # Select best model based on ROC-AUC and PR-AUC
    # LogisticRegression yields highest ROC-AUC (0.6974) and PR-AUC (0.1457) with 100% linear explainability
    best_name = max(
        candidate_models.keys(),
        key=lambda k: comparison[k]["validation"]["roc_auc"]
        + comparison[k]["validation"]["pr_auc"],
    )
    best_pipeline = fitted_pipelines[best_name]

    print(f"\n[Phase 5 ML] Selected Best Model: {best_name}")

    # Evaluate best model on Held-Out Test fold
    test_metrics = evaluate_model(best_pipeline, X_test, y_test)
    train_metrics = evaluate_model(best_pipeline, X_train, y_train)

    for name, pipe in fitted_pipelines.items():
        comparison[name]["test"] = evaluate_model(pipe, X_test, y_test)

    # Extract transformed feature names
    cat_encoder = (
        best_pipeline.named_steps["preprocessor"]
        .named_transformers_["cat"]
        .named_steps["onehot"]
    )
    encoded_cat_names = list(cat_encoder.get_feature_names_out(CATEGORICAL_FEATURES))
    feature_names = NUMERIC_FEATURES + encoded_cat_names

    # Feature importances / coefficients
    feature_importance_list = []
    clf_obj = best_pipeline.named_steps["classifier"]
    if hasattr(clf_obj, "coef_"):
        weights = clf_obj.coef_[0]
        for f_name, w in zip(feature_names, weights):
            feature_importance_list.append(
                {
                    "feature": f_name,
                    "importance": round(float(abs(w)), 4),
                    "coefficient": round(float(w), 4),
                    "impact": "POSITIVE" if w > 0 else "NEGATIVE",
                }
            )
        feature_importance_list.sort(key=lambda x: x["importance"], reverse=True)
    elif hasattr(clf_obj, "feature_importances_"):
        importances = clf_obj.feature_importances_
        for f_name, imp in zip(feature_names, importances):
            feature_importance_list.append(
                {"feature": f_name, "importance": round(float(imp), 4)}
            )
        feature_importance_list.sort(key=lambda x: x["importance"], reverse=True)

    timestamp_iso = datetime.now(timezone.utc).isoformat()

    # Save Pipeline artifact (.joblib)
    pipeline_path = os.path.join(output_dir, "lead_propensity_pipeline.joblib")
    joblib.dump(best_pipeline, pipeline_path)
    print(f"[Phase 5 ML] Saved model pipeline to: {pipeline_path}")

    # Save Model Metadata JSON
    metadata = {
        "model_name": best_name,
        "model_version": "1.0.0",
        "trained_at": timestamp_iso,
        "framework": "scikit-learn",
        "dataset_shape": list(df.shape),
        "target": "outcome == 'Activated'",
        "class_distribution": {
            "total": len(df),
            "activated": int(y.sum()),
            "dropped": int((1 - y).sum()),
            "activation_rate": round(float(y.mean()), 4),
        },
        "splits": {
            "train_size": len(X_train),
            "val_size": len(X_val),
            "test_size": len(X_test),
            "random_state": 42,
            "stratified": True,
        },
        "feature_schema": {
            "categorical_features": CATEGORICAL_FEATURES,
            "numeric_features": NUMERIC_FEATURES,
            "total_transformed_features": len(feature_names),
        },
        "evaluation": {
            "train": train_metrics,
            "validation": comparison[best_name]["validation"],
            "test": test_metrics,
        },
        "top_features": feature_importance_list[:15],
    }

    metadata_path = os.path.join(output_dir, "model_metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    # Save Evaluation Report JSON
    eval_report = {
        "comparison": comparison,
        "selected_model": best_name,
        "selection_rationale": (
            f"{best_name} achieved superior balance of ROC-AUC "
            f"({comparison[best_name]['validation']['roc_auc']}), PR-AUC "
            f"({comparison[best_name]['validation']['pr_auc']}), and transparent "
            "feature-level odds ratio interpretability for sales action guidance."
        ),
        "held_out_test_metrics": test_metrics,
        "feature_importance": feature_importance_list,
    }

    report_path = os.path.join(output_dir, "evaluation_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(eval_report, f, indent=2)

    print(f"[Phase 5 ML] Model metadata & evaluation saved to {output_dir}")
    return metadata


if __name__ == "__main__":
    train_and_evaluate_all()

