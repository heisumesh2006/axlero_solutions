"""Controlled offline candidate study; never overwrites production artifacts."""

import json
import math
from pathlib import Path
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score, average_precision_score, confusion_matrix, f1_score,
    mean_absolute_error, mean_squared_error, precision_score, r2_score,
    recall_score, roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBClassifier, XGBRegressor

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from data.preprocess_data import CATEGORICAL_FEATURES, FEATURE_COLUMNS, NUMERIC_FEATURES
from ml.train_model import RANDOM_STATE


MODEL_DIR = BACKEND_DIR / "ml"
DATA_PATH = BACKEND_DIR / "data" / "processed_supply_chain.csv"
REPORT_PATH = MODEL_DIR / "model_improvement_report.json"

CANDIDATE_CLASSIFIER_PATH = MODEL_DIR / "candidate_delay_classifier.pkl"
CANDIDATE_REGRESSOR_PATH = MODEL_DIR / "candidate_delay_regressor.pkl"
CANDIDATE_PREPROCESSOR_PATH = MODEL_DIR / "candidate_preprocessor.pkl"
CANDIDATE_CONFIG_PATH = MODEL_DIR / "candidate_model_config.json"

ENGINEERED_NUMERIC = [
    "value_per_unit", "weight_per_unit", "freight_per_kg", "freight_value_ratio"
]
CANDIDATE_NUMERIC = NUMERIC_FEATURES + ENGINEERED_NUMERIC

CLASSIFIER_CANDIDATES = [
    {"max_depth": 3, "learning_rate": .04, "n_estimators": 450, "subsample": .85, "colsample_bytree": .85, "min_child_weight": 3, "weight_multiplier": .75},
    {"max_depth": 4, "learning_rate": .04, "n_estimators": 450, "subsample": .85, "colsample_bytree": .85, "min_child_weight": 3, "weight_multiplier": 1.0},
    {"max_depth": 5, "learning_rate": .03, "n_estimators": 550, "subsample": .85, "colsample_bytree": .8, "min_child_weight": 5, "weight_multiplier": .75},
    {"max_depth": 4, "learning_rate": .06, "n_estimators": 350, "subsample": .9, "colsample_bytree": .9, "min_child_weight": 5, "weight_multiplier": .5},
    {"max_depth": 6, "learning_rate": .03, "n_estimators": 500, "subsample": .8, "colsample_bytree": .8, "min_child_weight": 8, "weight_multiplier": .75},
]
REGRESSOR_CANDIDATES = [
    {"max_depth": 3, "learning_rate": .03, "n_estimators": 550, "subsample": .85, "colsample_bytree": .85, "min_child_weight": 3},
    {"max_depth": 4, "learning_rate": .03, "n_estimators": 550, "subsample": .85, "colsample_bytree": .85, "min_child_weight": 5},
    {"max_depth": 5, "learning_rate": .025, "n_estimators": 650, "subsample": .85, "colsample_bytree": .8, "min_child_weight": 8},
    {"max_depth": 4, "learning_rate": .05, "n_estimators": 400, "subsample": .9, "colsample_bytree": .9, "min_child_weight": 10},
    {"max_depth": 6, "learning_rate": .02, "n_estimators": 700, "subsample": .8, "colsample_bytree": .8, "min_child_weight": 10},
]


def engineer_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Derive explainable pre-delivery ratios; zero denominators become missing."""
    result = frame.copy()
    quantity = pd.to_numeric(result["Line Item Quantity"], errors="coerce").replace(0, np.nan)
    value = pd.to_numeric(result["Line Item Value"], errors="coerce").replace(0, np.nan)
    weight = pd.to_numeric(result["Weight (Kilograms)"], errors="coerce").replace(0, np.nan)
    freight = pd.to_numeric(result["Freight Cost (USD)"], errors="coerce")
    result["value_per_unit"] = value / quantity
    result["weight_per_unit"] = weight / quantity
    result["freight_per_kg"] = freight / weight
    result["freight_value_ratio"] = freight / value
    return result.replace([np.inf, -np.inf], np.nan)


def build_candidate_preprocessor() -> ColumnTransformer:
    return ColumnTransformer([
        ("categorical", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]), CATEGORICAL_FEATURES),
        ("numeric", Pipeline([("imputer", SimpleImputer(strategy="median"))]), CANDIDATE_NUMERIC),
    ])


def classifier_metrics(y_true, probabilities, threshold):
    predictions = (probabilities >= threshold).astype(int)
    return {
        "threshold": float(threshold),
        "accuracy": float(accuracy_score(y_true, predictions)),
        "precision": float(precision_score(y_true, predictions, zero_division=0)),
        "recall": float(recall_score(y_true, predictions, zero_division=0)),
        "f1": float(f1_score(y_true, predictions, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, probabilities)),
        "pr_auc": float(average_precision_score(y_true, probabilities)),
        "confusion_matrix": confusion_matrix(y_true, predictions).tolist(),
    }


def regression_metrics(y_true, predictions):
    return {
        "mae": float(mean_absolute_error(y_true, predictions)),
        "rmse": float(mean_squared_error(y_true, predictions) ** .5),
        "r2": float(r2_score(y_true, predictions)),
    }


def choose_threshold(y_true, probabilities):
    choices = []
    for threshold in np.arange(.15, .81, .01):
        metrics = classifier_metrics(y_true, probabilities, threshold)
        if metrics["recall"] >= .65:
            choices.append(metrics)
    return max(choices, key=lambda item: (item["f1"], item["precision"]))


def percentage_change(baseline, candidate, lower_is_better=False):
    if baseline == 0:
        return None
    difference = baseline - candidate if lower_is_better else candidate - baseline
    return float(100 * difference / abs(baseline))


def main():
    data = pd.read_csv(DATA_PATH)
    X = engineer_features(data[FEATURE_COLUMNS])
    y_class = data["delayed"].astype(int)
    y_reg = data["delay_days"].astype(float)
    train_idx, test_idx = train_test_split(
        np.arange(len(data)), test_size=.2, random_state=RANDOM_STATE, stratify=y_class
    )
    inner_idx, validation_idx = train_test_split(
        train_idx, test_size=.2, random_state=RANDOM_STATE, stratify=y_class.iloc[train_idx]
    )

    selection_preprocessor = build_candidate_preprocessor()
    X_inner = selection_preprocessor.fit_transform(X.iloc[inner_idx])
    X_validation = selection_preprocessor.transform(X.iloc[validation_idx])
    negative = int((y_class.iloc[inner_idx] == 0).sum())
    positive = int((y_class.iloc[inner_idx] == 1).sum())
    imbalance_ratio = negative / positive

    classifier_results = []
    for params in CLASSIFIER_CANDIDATES:
        model_params = {key: value for key, value in params.items() if key != "weight_multiplier"}
        model = XGBClassifier(
            **model_params, scale_pos_weight=imbalance_ratio * params["weight_multiplier"],
            objective="binary:logistic", eval_metric="logloss", random_state=RANDOM_STATE, n_jobs=-1,
        )
        model.fit(X_inner, y_class.iloc[inner_idx])
        probabilities = model.predict_proba(X_validation)[:, 1]
        selected = choose_threshold(y_class.iloc[validation_idx], probabilities)
        classifier_results.append({"params": params, "validation": selected})
    best_classifier = max(
        classifier_results,
        key=lambda item: (item["validation"]["f1"], item["validation"]["roc_auc"]),
    )

    regressor_results = []
    for params in REGRESSOR_CANDIDATES:
        model = XGBRegressor(
            **params, objective="reg:squarederror", random_state=RANDOM_STATE, n_jobs=-1
        )
        model.fit(X_inner, y_reg.iloc[inner_idx])
        metrics = regression_metrics(y_reg.iloc[validation_idx], model.predict(X_validation))
        regressor_results.append({"params": params, "validation": metrics})
    best_regressor = min(regressor_results, key=lambda item: item["validation"]["mae"])

    final_preprocessor = build_candidate_preprocessor()
    X_train = final_preprocessor.fit_transform(X.iloc[train_idx])
    X_test = final_preprocessor.transform(X.iloc[test_idx])
    negative = int((y_class.iloc[train_idx] == 0).sum())
    positive = int((y_class.iloc[train_idx] == 1).sum())
    params = best_classifier["params"]
    model_params = {key: value for key, value in params.items() if key != "weight_multiplier"}
    classifier = XGBClassifier(
        **model_params, scale_pos_weight=(negative / positive) * params["weight_multiplier"],
        objective="binary:logistic", eval_metric="logloss", random_state=RANDOM_STATE, n_jobs=-1,
    )
    regressor = XGBRegressor(
        **best_regressor["params"], objective="reg:squarederror", random_state=RANDOM_STATE, n_jobs=-1
    )
    classifier.fit(X_train, y_class.iloc[train_idx])
    regressor.fit(X_train, y_reg.iloc[train_idx])
    candidate_class = classifier_metrics(
        y_class.iloc[test_idx], classifier.predict_proba(X_test)[:, 1],
        best_classifier["validation"]["threshold"],
    )
    candidate_reg = regression_metrics(y_reg.iloc[test_idx], regressor.predict(X_test))

    production_preprocessor = joblib.load(MODEL_DIR / "preprocessor.pkl")
    production_classifier = joblib.load(MODEL_DIR / "delay_classifier.pkl")
    production_regressor = joblib.load(MODEL_DIR / "delay_regressor.pkl")
    baseline_test = production_preprocessor.transform(data.iloc[test_idx][FEATURE_COLUMNS])
    baseline_class = classifier_metrics(
        y_class.iloc[test_idx], production_classifier.predict_proba(baseline_test)[:, 1], .5
    )
    baseline_reg = regression_metrics(y_reg.iloc[test_idx], production_regressor.predict(baseline_test))

    classifier_promotable = (
        candidate_class["roc_auc"] >= baseline_class["roc_auc"]
        and candidate_class["f1"] > baseline_class["f1"]
        and candidate_class["recall"] >= .65
    )
    regressor_promotable = (
        candidate_reg["mae"] < baseline_reg["mae"]
        and candidate_reg["rmse"] < baseline_reg["rmse"]
        and candidate_reg["r2"] > baseline_reg["r2"]
    )
    metrics_to_check = list(candidate_class.values())[1:-1] + list(candidate_reg.values())
    if not all(math.isfinite(float(value)) for value in metrics_to_check):
        raise RuntimeError("Candidate metrics are not finite.")

    joblib.dump(classifier, CANDIDATE_CLASSIFIER_PATH)
    joblib.dump(regressor, CANDIDATE_REGRESSOR_PATH)
    joblib.dump(final_preprocessor, CANDIDATE_PREPROCESSOR_PATH)
    config = {
        "classification_threshold": best_classifier["validation"]["threshold"],
        "engineered_numeric_features": ENGINEERED_NUMERIC,
        "classifier_params": best_classifier["params"],
        "regressor_params": best_regressor["params"],
    }
    CANDIDATE_CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")
    report = {
        "split": {"train_rows": len(train_idx), "test_rows": len(test_idx), "validation_rows": len(validation_idx)},
        "baseline": {"classifier": baseline_class, "regressor": baseline_reg},
        "candidate": {"classifier": candidate_class, "regressor": candidate_reg},
        "percentage_improvement": {
            "classifier_f1": percentage_change(baseline_class["f1"], candidate_class["f1"]),
            "classifier_roc_auc": percentage_change(baseline_class["roc_auc"], candidate_class["roc_auc"]),
            "classifier_recall": percentage_change(baseline_class["recall"], candidate_class["recall"]),
            "regressor_mae": percentage_change(baseline_reg["mae"], candidate_reg["mae"], True),
            "regressor_rmse": percentage_change(baseline_reg["rmse"], candidate_reg["rmse"], True),
            "regressor_r2": percentage_change(baseline_reg["r2"], candidate_reg["r2"]),
        },
        "promotion": {
            "classifier_criteria_met": classifier_promotable,
            "regressor_criteria_met": regressor_promotable,
            "production_replaced": False,
        },
        "selection": config,
        "validation_search": {"classifier": classifier_results, "regressor": regressor_results},
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("baseline", "candidate", "percentage_improvement", "promotion", "selection")}, indent=2))


if __name__ == "__main__":
    main()
