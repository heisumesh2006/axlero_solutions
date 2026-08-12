"""Isolated continuous-learning tests; production data/artifacts are untouched."""

import hashlib
import math
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import joblib
import pandas as pd
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
from ml.retraining import (
    CLASSIFIER_PATH,
    DATA_PATH,
    METADATA_PATH,
    REGRESSOR_PATH,
    get_retraining_status,
    retrain_models,
)
from models import Decision, ModelFeedback, Outcome, Shipment
from optimization.optimizer import generate_prescriptions


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    isolated_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(isolated_engine)
    TestingSession = sessionmaker(bind=isolated_engine)

    def override_db():
        with TestingSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    production_hashes = {path: digest(path) for path in (CLASSIFIER_PATH, REGRESSOR_PATH)}

    with TestClient(app) as client:
        response = client.get("/retraining/status")
        assert response.status_code == 200
        zero_status = response.json()
        assert zero_status["feedback_records"] == 0
        assert zero_status["retraining_required"] is False

        response = client.get("/analytics")
        assert response.status_code == 200
        assert response.json()["total_decisions"] == 0
        assert response.json()["feedback_records"] == 0

        with TestingSession() as session:
            for index in range(5):
                shipment = Shipment(
                    shipment_id=f"ISOLATED-{index}", country="Nigeria",
                    vendor="Aurobindo Pharma Limited", product_group="ARV",
                    shipment_mode="Air", line_item_quantity=416,
                    line_item_value=2225.6, weight=504, freight_cost=5920.42,
                    scheduled_delivery_date=date(2006, 9, 1), available_budget=20000,
                )
                session.add(shipment)
                session.flush()
                decision = Decision(
                    shipment_id=shipment.shipment_id, selected_option="A",
                    option_title="Air Freight", predicted_delay_probability=0.8,
                    predicted_delay_days=2, predicted_cost=15000, available_budget=20000,
                )
                session.add(decision)
                session.flush()
                actual_delay = 8 + index
                actual_cost = 18000 + index * 100
                session.add(Outcome(
                    decision_id=decision.id, actual_cost=actual_cost,
                    actual_delay_days=actual_delay, success=False,
                ))
                session.add(ModelFeedback(
                    decision_id=decision.id, predicted_cost=15000,
                    actual_cost=actual_cost, cost_error=actual_cost - 15000,
                    predicted_delay_days=2, actual_delay_days=actual_delay,
                    delay_error=actual_delay - 2,
                ))
            session.commit()

        triggered = client.get("/retraining/status").json()
        assert triggered["feedback_records"] == 5
        assert triggered["retraining_required"] is True

        with TemporaryDirectory() as directory:
            isolated_models = Path(directory)

            def isolated_retrain(database_engine):
                return retrain_models(
                    database_engine=database_engine,
                    data_path=DATA_PATH,
                    model_dir=isolated_models,
                    metadata_path=isolated_models / "model_metadata.json",
                )

            old_version = triggered["model_version"]
            with patch("main.retrain_models", side_effect=isolated_retrain):
                response = client.post("/retraining/run")
            assert response.status_code == 200, response.text
            result = response.json()
            assert result["status"] == "completed"
            assert result["model_version"] != old_version
            assert result["training_rows"] == 10329
            assert all(
                math.isfinite(value)
                for metrics in (result["classifier_metrics"], result["regressor_metrics"])
                for value in metrics.values()
            )
            for filename in (
                "preprocessor.pkl", "delay_classifier.pkl", "delay_regressor.pkl", "model_metadata.json"
            ):
                assert (isolated_models / filename).exists()

            # Verify the isolated retrained artifact set can still predict.
            row = pd.read_csv(DATA_PATH).iloc[[0]]
            preprocessor = joblib.load(isolated_models / "preprocessor.pkl")
            classifier = joblib.load(isolated_models / "delay_classifier.pkl")
            regressor = joblib.load(isolated_models / "delay_regressor.pkl")
            transformed = preprocessor.transform(row)
            probability = float(classifier.predict_proba(transformed)[0, 1])
            days = float(regressor.predict(transformed)[0])
            assert 0 <= probability <= 1 and math.isfinite(days)

    app.dependency_overrides.clear()
    assert {path: digest(path) for path in production_hashes} == production_hashes
    assert generate_prescriptions(14, 0.87, 15000, 20000)[0]["feasible"]
    print("Zero-feedback status endpoint: PASSED")
    print("Five-record threshold trigger: PASSED")
    print("Isolated POST /retraining/run: PASSED")
    print("Temporary artifacts and finite metrics: PASSED")
    print("Prediction with retrained artifacts: PASSED")
    print("Production model hashes unchanged: PASSED")
    print("Existing optimization smoke test: PASSED")


if __name__ == "__main__":
    main()
