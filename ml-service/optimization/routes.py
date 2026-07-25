"""HTTP routes for supply-chain action optimization."""

from fastapi import APIRouter

from .optimizer import OptimizationService
from .schemas import OptimizationRequest, OptimizationResponse

router = APIRouter(tags=["optimization"])
optimization_service = OptimizationService()


@router.post("/optimize", response_model=OptimizationResponse)
def optimize(request: OptimizationRequest) -> OptimizationResponse:
    """Return ranked feasible delay-mitigation actions."""
    return optimization_service.optimize(request)