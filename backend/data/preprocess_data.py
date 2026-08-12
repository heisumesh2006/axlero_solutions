"""Prepare the real SCMS delivery-history workbook for model training.

Run from the backend directory with:
    python data/preprocess_data.py
"""

from pathlib import Path

import numpy as np
import pandas as pd


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent
RAW_DATA_PATH = PROJECT_DIR / "SCMS_Delivery_History_Raw_Data.xlsx"
OUTPUT_PATH = BACKEND_DIR / "data" / "processed_supply_chain.csv"

CATEGORICAL_FEATURES = [
    "Country",
    "Managed By",
    "Fulfill Via",
    "Vendor INCO Term",
    "Shipment Mode",
    "Product Group",
    "Sub Classification",
    "Vendor",
    "Brand",
    "Dosage Form",
    "Manufacturing Site",
    "First Line Designation",
]

NUMERIC_FEATURES = [
    "Line Item Quantity",
    "Line Item Value",
    "Weight (Kilograms)",
    "Freight Cost (USD)",
    "scheduled_year",
    "scheduled_month",
    "scheduled_quarter",
]

FEATURE_COLUMNS = CATEGORICAL_FEATURES + NUMERIC_FEATURES
TARGET_COLUMNS = ["delay_days", "delayed"]


def _clean_column_names(columns: pd.Index) -> list[str]:
    """Remove whitespace and byte-order-mark artifacts from source headers."""
    return [str(column).replace("ï»¿", "").lstrip("\ufeff").strip() for column in columns]


def prepare_dataframe(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Convert the raw workbook rows into leak-free model features and targets."""
    df = raw_df.copy()
    df.columns = _clean_column_names(df.columns)

    required = set(CATEGORICAL_FEATURES) | {
        "Line Item Quantity",
        "Line Item Value",
        "Weight (Kilograms)",
        "Freight Cost (USD)",
        "Scheduled Delivery Date",
        "Delivered to Client Date",
    }
    missing = sorted(required.difference(df.columns))
    if missing:
        raise ValueError(f"Raw workbook is missing required columns: {missing}")

    scheduled = pd.to_datetime(df["Scheduled Delivery Date"], errors="coerce")
    delivered = pd.to_datetime(df["Delivered to Client Date"], errors="coerce")
    valid_target = scheduled.notna() & delivered.notna()
    invalid_count = int((~valid_target).sum())
    if invalid_count:
        print(f"Dropping {invalid_count} rows with invalid target dates.")
    df = df.loc[valid_target].copy()
    scheduled = scheduled.loc[valid_target]
    delivered = delivered.loc[valid_target]

    # Calendar values are known from the scheduled date before delivery.
    df["scheduled_year"] = scheduled.dt.year
    df["scheduled_month"] = scheduled.dt.month
    df["scheduled_quarter"] = scheduled.dt.quarter

    for column in CATEGORICAL_FEATURES:
        values = df[column].astype("string").str.strip()
        df[column] = values.mask(values.eq(""), pd.NA).fillna("Unknown")

    for column in NUMERIC_FEATURES:
        df[column] = pd.to_numeric(df[column], errors="coerce").replace(
            [np.inf, -np.inf], np.nan
        )

    df["delay_days"] = (delivered - scheduled).dt.days.astype(int)
    df["delayed"] = (df["delay_days"] > 0).astype(int)

    # Source delivery dates are used only to derive targets and never survive here.
    return df[FEATURE_COLUMNS + TARGET_COLUMNS].reset_index(drop=True)


def main() -> None:
    if not RAW_DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {RAW_DATA_PATH}")

    raw_df = pd.read_excel(RAW_DATA_PATH)
    processed_df = prepare_dataframe(raw_df)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    processed_df.to_csv(OUTPUT_PATH, index=False)

    print(f"Raw dataset shape: {raw_df.shape}")
    print(f"Processed dataset shape: {processed_df.shape}")
    print("Target distribution (delayed):")
    print(processed_df["delayed"].value_counts().sort_index().to_string())
    print(f"Saved cleaned dataset to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
