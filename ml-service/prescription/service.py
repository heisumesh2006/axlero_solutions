"""Orchestrates prediction and delay-mitigation optimization."""

from optimization.optimizer import OptimizationService
from optimization.schemas import OptimizationRequest
from prediction.predictor import PredictionService
from prediction.schemas import PredictionRequest

from .schemas import PrescriptionResponse


class PrescriptionService:
    """Combine a shipment-delay prediction with recommendations when needed."""

    def __init__(
        self,
        prediction_service: PredictionService,
        optimization_service: OptimizationService,
    ) -> None:
        self._prediction_service = prediction_service
        self._optimization_service = optimization_service

    def prescribe(self, request: PredictionRequest) -> PrescriptionResponse:
        """Predict delay risk and optimize mitigation for delayed shipments."""
        prediction = self._prediction_service.predict(request)
        is_delayed = prediction.delay_prediction == 1 or prediction.delay_probability >= 0.50

        if not is_delayed:
            return PrescriptionResponse(prediction=prediction, recommendations=[])

        optimization = self._optimization_service.optimize(
            OptimizationRequest(
                predicted_delay_days=14,
                budget=20000,
                inventory_units=500,
            )
        )
        return PrescriptionResponse(
            prediction=prediction,
            recommendations=optimization.recommendations,
        )
