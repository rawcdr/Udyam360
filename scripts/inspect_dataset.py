"""Inspect and validate the hackathon dataset for Udyam360.

This script discovers the dataset folder, verifies the presence and integrity
of all expected files, analyzes row/column counts, missing values, duplicates,
and image counts without modifying any dataset file or exposing sensitive identifiers.
"""

from pathlib import Path
import os
import sys
import pandas as pd


EXPECTED_FILES = [
    "product_catalogue.csv",
    "smb_leads.csv",
    "mock_gstin_registry.csv",
    "mock_udyam_registry.csv",
    "kyc_documents",
    "README.md",
]

EXPECTED_BENCHMARKS = {
    "product_catalogue.csv": 25,
    "smb_leads.csv": 5000,
    "mock_gstin_registry.csv": 3534,
    "mock_udyam_registry.csv": 2723,
    "kyc_images": 47,
}


def find_dataset_dir(base_dir: Path) -> Path:
    """Discover dataset directory within the project base directory."""
    # Look for known candidates or folders containing smb_leads.csv
    for entry in base_dir.iterdir():
        if entry.is_dir() and (entry / "smb_leads.csv").exists():
            return entry

    # Search one level deeper if needed
    for entry in base_dir.glob("*/smb_leads.csv"):
        return entry.parent

    raise FileNotFoundError("Could not discover hackathon dataset folder containing smb_leads.csv")


def inspect_dataset() -> dict:
    """Run full dataset inspection and return a structured summary report."""
    base_dir = Path(__file__).resolve().parent.parent
    dataset_dir = find_dataset_dir(base_dir)
    print(f"[INFO] Discovered dataset directory: {dataset_dir.name} (at {dataset_dir})")

    results = {
        "dataset_dir": dataset_dir.name,
        "files_found": {},
        "missing_expected_files": [],
        "unexpected_files": [],
        "csv_details": {},
        "kyc_details": {},
    }

    # Verify expected and unexpected files
    actual_items = {item.name: item for item in dataset_dir.iterdir()}
    for exp in EXPECTED_FILES:
        if exp in actual_items:
            results["files_found"][exp] = True
        else:
            results["missing_expected_files"].append(exp)

    for actual in actual_items:
        if actual not in EXPECTED_FILES:
            results["unexpected_files"].append(actual)

    # Inspect CSVs
    csv_files = ["product_catalogue.csv", "smb_leads.csv", "mock_gstin_registry.csv", "mock_udyam_registry.csv"]
    for csv_name in csv_files:
        csv_path = dataset_dir / csv_name
        if not csv_path.exists():
            print(f"[WARN] Expected CSV missing: {csv_name}")
            continue

        print(f"\n--- Inspecting {csv_name} ---")
        df = pd.read_csv(csv_path)
        row_count, col_count = df.shape
        expected_rows = EXPECTED_BENCHMARKS.get(csv_name)
        row_match = (row_count == expected_rows)

        # Duplicates
        duplicate_count = int(df.duplicated().sum())

        # Missing values
        missing_per_col = df.isnull().sum().to_dict()
        cols_with_missing = {col: int(cnt) for col, cnt in missing_per_col.items() if cnt > 0}

        # Data types
        dtypes = {col: str(dtype) for col, dtype in df.dtypes.items()}

        csv_summary = {
            "row_count": row_count,
            "col_count": col_count,
            "expected_rows": expected_rows,
            "row_count_matches": row_match,
            "duplicate_rows": duplicate_count,
            "columns": list(df.columns),
            "dtypes": dtypes,
            "missing_values": cols_with_missing,
        }

        # Categorical previews for key columns without leaking PII
        cat_summaries = {}
        if csv_name == "product_catalogue.csv":
            for cat_col in ["category", "billing_frequency", "requires_gstin", "available_city_tiers"]:
                if cat_col in df.columns:
                    cat_summaries[cat_col] = df[cat_col].value_counts().to_dict()
        elif csv_name == "smb_leads.csv":
            for cat_col in ["segment", "stage_reached", "outcome", "city_tier", "has_gstin", "has_udyam", "drop_reason"]:
                if cat_col in df.columns:
                    cat_summaries[cat_col] = df[cat_col].value_counts().dropna().to_dict()
        elif csv_name == "mock_gstin_registry.csv":
            for cat_col in ["status", "constitution_of_business", "state_jurisdiction"]:
                if cat_col in df.columns:
                    cat_summaries[cat_col] = df[cat_col].value_counts().head(5).to_dict()
        elif csv_name == "mock_udyam_registry.csv":
            for cat_col in ["enterprise_type", "major_activity", "status"]:
                if cat_col in df.columns:
                    cat_summaries[cat_col] = df[cat_col].value_counts().to_dict()

        csv_summary["categorical_summaries"] = cat_summaries
        results["csv_details"][csv_name] = csv_summary

        print(f"Rows: {row_count} (Expected: {expected_rows}, Match: {row_match})")
        print(f"Columns ({col_count}): {list(df.columns)}")
        print(f"Duplicates: {duplicate_count}")
        print(f"Columns with missing values: {len(cols_with_missing)}")

    # Inspect KYC documents directory
    kyc_dir = dataset_dir / "kyc_documents"
    if kyc_dir.is_dir():
        kyc_files = list(kyc_dir.iterdir())
        image_extensions = {}
        applicant_ids = set()
        total_images = 0

        for f in kyc_files:
            if f.is_file():
                ext = f.suffix.lower()
                image_extensions[ext] = image_extensions.get(ext, 0) + 1
                total_images += 1
                # Check applicant ID convention (e.g., K01_...)
                prefix = f.stem.split("_")[0]
                applicant_ids.add(prefix)

        results["kyc_details"] = {
            "total_files": total_images,
            "expected_count": EXPECTED_BENCHMARKS["kyc_images"],
            "matches_expected": (total_images == EXPECTED_BENCHMARKS["kyc_images"]),
            "extensions": image_extensions,
            "unique_applicants": sorted(list(applicant_ids)),
            "applicant_count": len(applicant_ids),
        }
        print(f"\n--- Inspecting KYC Documents ---")
        print(f"Total KYC files: {total_images} (Expected: {EXPECTED_BENCHMARKS['kyc_images']})")
        print(f"File extensions: {image_extensions}")
        print(f"Applicant IDs ({len(applicant_ids)}): {sorted(list(applicant_ids))}")

    # Inspect README
    readme_path = dataset_dir / "README.md"
    results["readme_present"] = readme_path.exists()
    print(f"\nDataset README exists: {results['readme_present']}")

    return results


if __name__ == "__main__":
    inspect_dataset()

