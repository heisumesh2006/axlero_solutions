"""Business logic for loading and executing the shipment-delay model."""

import logging
import joblib
from pathlib import Path
from typing import Any

import pandas as pd

from .schemas import PredictionRequest, PredictionResponse

logger = logging.getLogger(__name__)
MODEL_DIR = Path(__file__).resolve().parent.parent / "models"
MODEL_PATH = MODEL_DIR / "shipment_delay_model.pkl"
ENCODERS_PATH = MODEL_DIR / "label_encoders.pkl"


class UnknownCategoryError(ValueError):
    """Raised when a request contains a category absent from training data."""


class PredictionService:
    """Loads model artifacts once and provides validated delay predictions."""

    def __init__(self) -> None:
        self._model: Any | None = None
        self._label_encoders: dict[str, Any] | None = None

    def load_model(self) -> None:
        """Load the model and label encoders once for the lifetime of the service."""
        if self._model is not None and self._label_encoders is not None:
            return
        logger.info("Loading shipment delay prediction artifacts")
        self._model = joblib.load(MODEL_PATH)
        self._label_encoders = joblib.load(ENCODERS_PATH)
        logger.info("Shipment delay prediction artifacts loaded")

    def encode_input(self, request: PredictionRequest) -> pd.DataFrame:
        """Validate categorical values and convert a request into model features."""
        if self._model is None or self._label_encoders is None:
            raise RuntimeError("Prediction model has not been loaded")
        values = request.model_dump(by_alias=True)
        for column, encoder in self._label_encoders.items():
            value = values[column]
            if value not in encoder.classes_:
                raise UnknownCategoryError(
                    f"Unknown value {value!r} for '{column}'. The value was not seen during training."
                )
            values[column] = int(encoder.transform([value])[0])
        feature_names = list(getattr(self._model, "feature_names_in_", values.keys()))
        return pd.DataFrame([values], columns=feature_names)

    def predict(self, request: PredictionRequest) -> PredictionResponse:
        """Produce a binary delay prediction and its probability."""
        features = self.encode_input(request)
        if self._model is None:
            raise RuntimeError("Prediction model has not been loaded")
        prediction = int(self._model.predict(features)[0])
        probability = float(self._model.predict_proba(features)[0][1])
        message = "Shipment is predicted to be delayed." if prediction else "Shipment is predicted to arrive on time."
        return PredictionResponse(delay_prediction=prediction, delay_probability=probability, message=message)
