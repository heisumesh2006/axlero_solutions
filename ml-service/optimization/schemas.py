"""Request and response contracts for optimization."""

from typing import Annotated

from pydantic import BaseModel, Field


class OptimizationRequest(BaseModel):
    """Operational limits used to evaluate mitigation actions."""

    predicted_delay_days: Annotated[float, Field(ge=0)]
    budget: Annotated[float, Field(ge=0)]
    inventory_units: Annotated[int, Field(ge=0)]


class OptimizationRecommendation(BaseModel):
    """One feasible mitigation action, ordered by preference."""

    rank: Annotated[int, Field(ge=1)]
    action: str
    cost: float
    delay_reduction: float
    inventory_impact: int
    score: float


class OptimizationResponse(BaseModel):
    """Ranked feasible actions returned by the optimizer."""

    recommendations: list[OptimizationRecommendation]