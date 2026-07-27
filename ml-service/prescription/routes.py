"""HTTP route for combined shipment prescriptions."""

import logging

from fastapi import APIRouter, HTTPException, status

from optimization.routes import optimization_service
from prediction.predictor import UnknownCategoryError
from prediction.routes import prediction_service
from prediction.schemas import PredictionRequest

from .schemas import PrescriptionResponse
from .service import PrescriptionService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["prescription"])
prescription_service = PrescriptionService(prediction_service, optimization_service)


@router.post("/prescribe", response_model=PrescriptionResponse)
def prescribe(request: PredictionRequest) -> PrescriptionResponse:
    """Return a delay prediction and mitigation recommendations when warranted."""
    try:
        return prescription_service.prescribe(request)
    except UnknownCategoryError as exc:
        logger.info("Rejected prescription request: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
