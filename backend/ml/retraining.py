"""Safe, threshold-driven continuous learning for SupplyPrescript."""

from __future__ import annotations

import json
import math
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session
from xgboost import XGBClassifier, XGBRegressor

from data.preprocess_data import CATEGORICAL_FEATURES, FEATURE_COLUMNS, NUMERIC_FEATURES
from database import engine as production_engine
from ml.train_model import RANDOM_STATE, build_preprocessor
from models import Decision, ModelFeedback, Shipment


MIN_FEEDBACK_RECORDS = 5
MIN_COST_ERROR = 2000.0
MIN_DELAY_ERROR = 3.0

BACKEND_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BACKEND_DIR / "data" / "processed_supply_chain.csv"
MODEL_DIR = BACKEND_DIR / "ml"
CLASSIFIER_PATH = MODEL_DIR / "delay_classifier.pkl"
REGRESSOR_PATH = MODEL_DIR / "delay_regressor.pkl"
PREPROCESSOR_PATH = MODEL_DIR / "preprocessor.pkl"
METADATA_PATH = MODEL_DIR / "model_metadata.json"


def _metadata(path: Path = METADATA_PATH) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def get_retraining_status(
    database_engine: Engine = production_engine,
    metadata_path: Path = METADATA_PATH,
) -> dict[str, Any]:
    """Summarize feedback volume/error and apply the explainable trigger rule."""
    with Session(database_engine) as session:
        feedback_records = int(session.scalar(select(func.count(ModelFeedback.id))) or 0)
        mean_cost_error = float(
            session.scalar(select(func.avg(func.abs(ModelFeedback.cost_error)))) or 0.0
        )
        mean_delay_error = float(
            session.scalar(select(func.avg(func.abs(ModelFeedback.delay_error)))) or 0.0
        )

    enough_feedback = feedback_records >= MIN_FEEDBACK_RECORDS
    meaningful_error = (
        mean_cost_error >= MIN_COST_ERROR or mean_delay_error >= MIN_DELAY_ERROR
    )
    required = enough_feedback and meaningful_error
    if not enough_feedback:
        reason = (
            f"Insufficient feedback: {feedback_records} of "
            f"{MIN_FEEDBACK_RECORDS} required records are available."
        )
    elif not meaningful_error:
        reason = (
            "Feedback error is below both retraining thresholds: "
            f"mean absolute cost error < ${MIN_COST_ERROR:,.0f} and "
            f"mean absolute delay error < {MIN_DELAY_ERROR:.1f} days."
        )
    else:
        exceeded = []
        if mean_cost_error >= MIN_COST_ERROR:
            exceeded.append("cost error")
        if mean_delay_error >= MIN_DELAY_ERROR:
            exceeded.append("delay error")
        reason = f"Retraining required: sufficient feedback and meaningful {' and '.join(exceeded)}."

    metadata = _metadata(metadata_path)
    return {
        "feedback_records": feedback_records,
        "mean_cost_error": mean_cost_error,
        "mean_delay_error": mean_delay_error,
        "retraining_required": required,
        "reason": reason,
        "last_retrained_at": metadata.get("trained_at"),
        "model_version": metadata.get("model_version", "unversioned-phase-1"),
    }


def _feedback_training_rows(database_engine: Engine) -> pd.DataFrame:
    """Build rows using shipment characteristics and actual delay outcomes only."""
    statement = (
        select(ModelFeedback, Decision, Shipment)
        .join(Decision, ModelFeedback.decision_id == Decision.id)
        .join(Shipment, Decision.shipment_id == Shipment.shipment_id)
    )
    rows: list[dict[str, Any]] = []
    with Session(database_engine) as session:
        for feedback, _decision, shipment in session.execute(statement):
            scheduled = shipment.scheduled_delivery_date
            row = {column: "Unknown" for column in CATEGORICAL_FEATURES}
            row.update(
                {
                    "Country": shipment.country,
                    "Shipment Mode": shipment.shipment_mode,
                    "Product Group": shipment.product_group,
                    "Vendor": shipment.vendor,
                    "Line Item Quantity": shipment.line_item_quantity,
                    "Line Item Value": shipment.line_item_value,
                    "Weight (Kilograms)": shipment.weight,
                    "Freight Cost (USD)": shipment.freight_cost,
                    "scheduled_year": scheduled.year,
                    "scheduled_month": scheduled.month,
                    "scheduled_quarter": (scheduled.month - 1) // 3 + 1,
                    # Actual observed delay is the only new target.
                    "delay_days": feedback.actual_delay_days,
                    "delayed": int(feedback.actual_delay_days > 0),
                }
            )
            rows.append(row)
    return pd.DataFrame(rows, columns=FEATURE_COLUMNS + ["delay_days", "delayed"])


def _finite_metrics(metrics: dict[str, float]) -> bool:
    return all(math.isfinite(float(value)) for value in metrics.values())


def retrain_models(
    database_engine: Engine = production_engine,
    data_path: Path = DATA_PATH,
    model_dir: Path = MODEL_DIR,
    metadata_path: Path | None = None,
    require_trigger: bool = True,
) -> dict[str, Any]:
    """Retrain, validate, and safely promote a complete compatible artifact set."""
    model_dir = Path(model_dir)
    metadata_path = Path(metadata_path or model_dir / "model_metadata.json")
    status = get_retraining_status(database_engine, metadata_path)
    if require_trigger and not status["retraining_required"]:
        raise ValueError(status["reason"])

    original = pd.read_csv(data_path)
    required_columns = set(FEATURE_COLUMNS + ["delay_days", "delayed"])
    missing = sorted(required_columns.difference(original.columns))
    if missing:
        raise ValueError(f"Processed dataset is missing required columns: {missing}")
    feedback_rows = _feedback_training_rows(database_engine)
    combined = pd.concat([original[FEATURE_COLUMNS + ["delay_days", "delayed"]], feedback_rows], ignore_index=True)

    X = combined[FEATURE_COLUMNS]
    y_class = combined["delayed"].astype(int)
    y_reg = combined["delay_days"].astype(float)
    train_idx, test_idx = train_test_split(
        np.arange(len(combined)), test_size=0.2, random_state=RANDOM_STATE, stratify=y_class
    )
    preprocessor = build_preprocessor()
    X_train = preprocessor.fit_transform(X.iloc[train_idx])
    X_test = preprocessor.transform(X.iloc[test_idx])
    y_class_train, y_class_test = y_class.iloc[train_idx], y_class.iloc[test_idx]
    y_reg_train, y_reg_test = y_reg.iloc[train_idx], y_reg.iloc[test_idx]

    positives = int((y_class_train == 1).sum())
    negatives = int((y_class_train == 0).sum())
    classifier = XGBClassifier(
        n_estimators=300, max_depth=5, learning_rate=0.05, subsample=0.8,
        colsample_bytree=0.8, objective="binary:logistic", eval_metric="logloss",
        scale_pos_weight=negatives / max(positives, 1), random_state=RANDOM_STATE, n_jobs=-1,
    )
    regressor = XGBRegressor(
        n_estimators=300, max_depth=5, learning_rate=0.05, subsample=0.8,
        colsample_bytree=0.8, objective="reg:squarederror", random_state=RANDOM_STATE, n_jobs=-1,
    )
    classifier.fit(X_train, y_class_train)
    regressor.fit(X_train, y_reg_train)

    class_predictions = classifier.predict(X_test)
    class_probabilities = classifier.predict_proba(X_test)[:, 1]
    regression_predictions = regressor.predict(X_test)
    classifier_metrics = {
        "accuracy": float(accuracy_score(y_class_test, class_predictions)),
        "precision": float(precision_score(y_class_test, class_predictions, zero_division=0)),
        "recall": float(recall_score(y_class_test, class_predictions, zero_division=0)),
        "f1": float(f1_score(y_class_test, class_predictions, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_class_test, class_probabilities)),
    }
    regressor_metrics = {
        "mae": float(mean_absolute_error(y_reg_test, regression_predictions)),
        "rmse": float(mean_squared_error(y_reg_test, regression_predictions) ** 0.5),
        "r2": float(r2_score(y_reg_test, regression_predictions)),
    }
    if not (_finite_metrics(classifier_metrics) and _finite_metrics(regressor_metrics)):
        raise RuntimeError("Retrained model produced non-finite evaluation metrics.")

    model_dir.mkdir(parents=True, exist_ok=True)
    version = datetime.now().astimezone().replace(microsecond=0).isoformat()
    metadata = {
        "model_version": version,
        "trained_at": version,
        "training_rows": int(len(combined)),
        "feedback_rows": int(len(feedback_rows)),
        "classifier_metrics": classifier_metrics,
        "regressor_metrics": regressor_metrics,
    }
    targets = {
        "preprocessor.pkl": preprocessor,
        "delay_classifier.pkl": classifier,
        "delay_regressor.pkl": regressor,
    }
    temporary_paths: list[Path] = []
    try:
        for filename, artifact in targets.items():
            temporary = model_dir / f".{filename}.tmp"
            joblib.dump(artifact, temporary)
            joblib.load(temporary)  # Confirm each temporary artifact is readable.
            temporary_paths.append(temporary)
        temporary_metadata = model_dir / ".model_metadata.json.tmp"
        temporary_metadata.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        json.loads(temporary_metadata.read_text(encoding="utf-8"))
        temporary_paths.append(temporary_metadata)

        for filename in targets:
            os.replace(model_dir / f".{filename}.tmp", model_dir / filename)
        os.replace(temporary_metadata, metadata_path)
        # The prediction module caches loaded production artifacts for speed.
        if model_dir.resolve() == MODEL_DIR.resolve():
            from ml.predict import _load_artifacts

            _load_artifacts.cache_clear()
    finally:
        for temporary in temporary_paths:
            temporary.unlink(missing_ok=True)

    return metadata
