"""Inspect real high-delay SCMS shipments suitable for the final demonstration.

This script is read-only. It ranks eligible records exclusively by their actual
historical ``delay_days`` value and does not write to SQLite or any data file.
Run from the backend directory with:

    python data/find_demo_shipments.py
"""

from pathlib import Path

import pandas as pd


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent
PROCESSED_PATH = BACKEND_DIR / "data" / "processed_supply_chain.csv"
RAW_PATH = PROJECT_DIR / "SCMS_Delivery_History_Raw_Data.xlsx"

DISPLAY_FIELDS = [
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
    "Line Item Quantity",
    "Line Item Value",
    "Weight (Kilograms)",
    "Freight Cost (USD)",
]


def main() -> None:
    processed = pd.read_csv(PROCESSED_PATH)
    raw = pd.read_excel(RAW_PATH)
    raw.columns = [
        str(column).replace("ï»¿", "").lstrip("\ufeff").strip()
        for column in raw.columns
    ]
    if len(processed) != len(raw):
        raise ValueError(
            "Processed and source row counts differ; source-row alignment is unsafe."
        )

    identifier_columns = [column for column in raw.columns if column.upper().endswith("ID")]
    if not identifier_columns:
        raise ValueError("The source workbook does not contain an identifiable ID column.")
    source_id_column = identifier_columns[0]

    candidates = processed.copy()
    # Phase 1 intentionally excluded identifiers and full dates. Recover these
    # two display-only values from the same real source row without changing it.
    candidates["shipment_id"] = raw[source_id_column].astype(str).values
    candidates["Scheduled Delivery Date"] = pd.to_datetime(
        raw["Scheduled Delivery Date"], errors="coerce"
    ).dt.date.values

    numeric_complete = candidates[
        ["Line Item Quantity", "Line Item Value", "Weight (Kilograms)", "Freight Cost (USD)"]
    ].notna().all(axis=1)
    categorical_complete = candidates[DISPLAY_FIELDS[:12]].apply(
        lambda column: column.notna() & column.astype(str).str.strip().ne("")
        & column.astype(str).str.strip().ne("Unknown")
    ).all(axis=1)
    reasonable_freight = candidates["Freight Cost (USD)"].between(1, 50000)
    eligible = candidates.loc[
        candidates["delayed"].eq(1)
        & numeric_complete
        & categorical_complete
        & reasonable_freight
        & candidates["Scheduled Delivery Date"].notna()
    ].sort_values("delay_days", ascending=False, kind="stable").head(10)

    if eligible.empty:
        print("No complete delayed candidates matched the inspection criteria.")
        return

    print(f"Processed dataset shape: {processed.shape}")
    print(f"Eligible complete delayed shipments: {len(candidates.loc[candidates['delayed'].eq(1) & numeric_complete & categorical_complete & reasonable_freight])}")
    print("Ranking basis: actual historical delay_days descending (no predictions used).")
    print("Reasonable freight filter: $1 to $50,000.")
    print("=" * 78)

    for rank, (_, row) in enumerate(eligible.iterrows(), start=1):
        freight = float(row["Freight Cost (USD)"])
        line_value = float(row["Line Item Value"])
        actual_cost = line_value + freight
        print(f"\nRANK {rank}")
        print(f"shipment_id: {row['shipment_id']}")
        for field in DISPLAY_FIELDS:
            label = {
                "Weight (Kilograms)": "Weight",
                "Freight Cost (USD)": "Freight Cost",
            }.get(field, field)
            print(f"{label}: {row[field]}")
        print(f"Scheduled Delivery Date: {row['Scheduled Delivery Date']}")
        print(f"delayed: {int(row['delayed'])}")
        print(f"delay_days: {int(row['delay_days'])}")
        print(f"actual_cost: {actual_cost:.2f}")


if __name__ == "__main__":
    main()
