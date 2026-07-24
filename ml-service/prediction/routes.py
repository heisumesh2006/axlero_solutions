"""HTTP routes for shipment-delay predictions."""

import logging

from fastapi import APIRouter, HTTPException, status

from .predictor import PredictionService, UnknownCategoryError
from .schemas import PredictionRequest, PredictionResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["prediction"])
prediction_service = PredictionService()


@router.post("/predict", response_model=PredictionResponse)
def predict_delay(request: PredictionRequest) -> PredictionResponse:
    """Return the trained model's delay-risk prediction for a shipment."""
    try:
        return prediction_service.predict(request)
    except UnknownCategoryError as exc:
        logger.info("Rejected prediction request: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
