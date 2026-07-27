"""Response contract for shipment prescriptions."""

from pydantic import BaseModel

from optimization.schemas import OptimizationRecommendation
from prediction.schemas import PredictionResponse


class PrescriptionResponse(BaseModel):
    """A delay prediction with any applicable mitigation recommendations."""

    prediction: PredictionResponse
    recommendations: list[OptimizationRecommendation]
