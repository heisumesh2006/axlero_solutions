"""Train and evaluate SupplyPrescript delay models.

Run from the backend directory after preprocessing with:
    python ml/train_model.py
"""

import json
from pathlib import Path
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
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
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBClassifier, XGBRegressor


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from data.preprocess_data import CATEGORICAL_FEATURES, FEATURE_COLUMNS, NUMERIC_FEATURES


DATA_PATH = BACKEND_DIR / "data" / "processed_supply_chain.csv"
CLASSIFIER_PATH = BACKEND_DIR / "ml" / "delay_classifier.pkl"
REGRESSOR_PATH = BACKEND_DIR / "ml" / "delay_regressor.pkl"
PREPROCESSOR_PATH = BACKEND_DIR / "ml" / "preprocessor.pkl"
SCHEMA_PATH = BACKEND_DIR / "ml" / "feature_schema.json"
RANDOM_STATE = 42


def build_preprocessor() -> ColumnTransformer:
    numeric_pipeline = Pipeline(
        [("imputer", SimpleImputer(strategy="median"))]
    )
    categorical_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    return ColumnTransformer(
        [
            ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
            ("numeric", numeric_pipeline, NUMERIC_FEATURES),
        ]
    )


def main() -> None:
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Processed dataset not found: {DATA_PATH}. Run data/preprocess_data.py first."
        )

    df = pd.read_csv(DATA_PATH)
    required = set(FEATURE_COLUMNS + ["delay_days", "delayed"])
    missing = sorted(required.difference(df.columns))
    if missing:
        raise ValueError(f"Processed dataset is missing columns: {missing}")

    X = df[FEATURE_COLUMNS]
    y_class = df["delayed"].astype(int)
    y_reg = df["delay_days"].astype(float)

    # One shared split makes both model evaluations directly comparable.
    train_indices, test_indices = train_test_split(
        np.arange(len(df)),
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=y_class,
    )
    X_train, X_test = X.iloc[train_indices], X.iloc[test_indices]
    y_class_train, y_class_test = y_class.iloc[train_indices], y_class.iloc[test_indices]
    y_reg_train, y_reg_test = y_reg.iloc[train_indices], y_reg.iloc[test_indices]

    preprocessor = build_preprocessor()
    X_train_transformed = preprocessor.fit_transform(X_train)
    X_test_transformed = preprocessor.transform(X_test)

    negative_count = int((y_class_train == 0).sum())
    positive_count = int((y_class_train == 1).sum())
    scale_pos_weight = negative_count / max(positive_count, 1)

    classifier = XGBClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="binary:logistic",
        eval_metric="logloss",
        scale_pos_weight=scale_pos_weight,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    regressor = XGBRegressor(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="reg:squarederror",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )

    classifier.fit(X_train_transformed, y_class_train)
    regressor.fit(X_train_transformed, y_reg_train)

    class_predictions = classifier.predict(X_test_transformed)
    class_probabilities = classifier.predict_proba(X_test_transformed)[:, 1]
    regression_predictions = regressor.predict(X_test_transformed)

    class_metrics = {
        "accuracy": accuracy_score(y_class_test, class_predictions),
        "precision": precision_score(y_class_test, class_predictions, zero_division=0),
        "recall": recall_score(y_class_test, class_predictions, zero_division=0),
        "f1": f1_score(y_class_test, class_predictions, zero_division=0),
        "roc_auc": roc_auc_score(y_class_test, class_probabilities),
    }
    regression_metrics = {
        "mae": mean_absolute_error(y_reg_test, regression_predictions),
        "rmse": mean_squared_error(y_reg_test, regression_predictions) ** 0.5,
        "r2": r2_score(y_reg_test, regression_predictions),
    }

    joblib.dump(preprocessor, PREPROCESSOR_PATH)
    joblib.dump(classifier, CLASSIFIER_PATH)
    joblib.dump(regressor, REGRESSOR_PATH)
    SCHEMA_PATH.write_text(
        json.dumps(
            {
                "feature_columns": FEATURE_COLUMNS,
                "categorical_features": CATEGORICAL_FEATURES,
                "numeric_features": NUMERIC_FEATURES,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Dataset shape: {df.shape}")
    print(f"Train/test rows: {len(train_indices)}/{len(test_indices)}")
    print("Target distribution (delayed):")
    print(y_class.value_counts().sort_index().to_string())
    print("\nClassifier metrics:")
    for name, value in class_metrics.items():
        print(f"  {name}: {value:.4f}")
    print("\nRegression metrics:")
    for name, value in regression_metrics.items():
        print(f"  {name}: {value:.4f}")
    print("\nSaved artifacts:")
    for path in [PREPROCESSOR_PATH, CLASSIFIER_PATH, REGRESSOR_PATH, SCHEMA_PATH]:
        print(f"  {path}")


if __name__ == "__main__":
    main()
