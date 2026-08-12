"""Reusable inference functions for the SupplyPrescript delay models."""

from functools import lru_cache
from pathlib import Path
import sys
from typing import Any, Mapping

import joblib
import numpy as np
import pandas as pd


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from data.preprocess_data import CATEGORICAL_FEATURES, FEATURE_COLUMNS, NUMERIC_FEATURES


MODEL_DIR = BACKEND_DIR / "ml"


@lru_cache(maxsize=1)
def _load_artifacts() -> tuple[Any, Any, Any]:
    paths = {
        "preprocessor": MODEL_DIR / "preprocessor.pkl",
        "classifier": MODEL_DIR / "delay_classifier.pkl",
        "regressor": MODEL_DIR / "delay_regressor.pkl",
    }
    missing = [str(path) for path in paths.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing trained artifacts: {missing}")
    return (
        joblib.load(paths["preprocessor"]),
        joblib.load(paths["classifier"]),
        joblib.load(paths["regressor"]),
    )


def _prepare_input(shipment: Mapping[str, Any] | pd.DataFrame) -> pd.DataFrame:
    frame = shipment.copy() if isinstance(shipment, pd.DataFrame) else pd.DataFrame([shipment])

    if "Scheduled Delivery Date" in frame.columns:
        scheduled = pd.to_datetime(frame["Scheduled Delivery Date"], errors="coerce")
        frame["scheduled_year"] = scheduled.dt.year
        frame["scheduled_month"] = scheduled.dt.month
        frame["scheduled_quarter"] = scheduled.dt.quarter

    missing = [column for column in FEATURE_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Prediction input is missing required features: {missing}")

    for column in CATEGORICAL_FEATURES:
        values = frame[column].astype("string").str.strip()
        frame[column] = values.mask(values.eq(""), pd.NA).fillna("Unknown")
    for column in NUMERIC_FEATURES:
        frame[column] = pd.to_numeric(frame[column], errors="coerce").replace(
            [np.inf, -np.inf], np.nan
        )
    return frame[FEATURE_COLUMNS]


def predict_delay_probability(shipment: Mapping[str, Any] | pd.DataFrame) -> float | np.ndarray:
    """Return the probability that each supplied shipment is delivered late."""
    preprocessor, classifier, _ = _load_artifacts()
    probabilities = classifier.predict_proba(preprocessor.transform(_prepare_input(shipment)))[:, 1]
    return float(probabilities[0]) if len(probabilities) == 1 else probabilities


def predict_delay_days(shipment: Mapping[str, Any] | pd.DataFrame) -> float | np.ndarray:
    """Return predicted signed delay days (negative means early delivery)."""
    preprocessor, _, regressor = _load_artifacts()
    predictions = regressor.predict(preprocessor.transform(_prepare_input(shipment)))
    return float(predictions[0]) if len(predictions) == 1 else predictions
