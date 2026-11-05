"""Analyze product catalogue schema and print markdown summary."""
import pandas as pd
from pathlib import Path

df = pd.read_csv("YTL_TrackA_Udyam_Digital_Data/product_catalogue.csv")

print("Total Products:", len(df))
print("\nCategories:")
print(df["category"].value_counts().to_string())

print("\nUnits:")
print(df["unit"].value_counts().to_string())

print("\nRequires GSTIN:")
print(df["requires_gstin"].value_counts().to_string())

print("\nMin Employees distribution:")
print(df["min_employees"].value_counts().to_string())

print("\nMin Sites distribution:")
print(df["min_sites"].value_counts().to_string())

print("\nCity Tiers distribution:")
print(df["available_city_tiers"].value_counts().to_string())

print("\nDependencies (requires_one_of):")
for _, r in df[df["requires_one_of"].notna()].iterrows():
    print(f"  {r['product_id']} ({r['product_name']}): requires one of {r['requires_one_of']}")

print("\nTarget Segments breakdown:")
all_segs = {}
for s in df["target_segments"]:
    for item in s.split(";"):
        all_segs[item] = all_segs.get(item, 0) + 1
print(all_segs)

