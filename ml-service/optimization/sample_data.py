"""Static action catalog used by the optimization engine."""

from dataclasses import dataclass


@dataclass(frozen=True)
class OptimizationAction:
    """A delay-mitigation action that can be recommended."""

    name: str
    cost: float
    delay_reduction: float
    inventory_impact: int


ACTIONS: tuple[OptimizationAction, ...] = (
    OptimizationAction(name="Air Freight", cost=15000, delay_reduction=12, inventory_impact=0),
    OptimizationAction(name="Secondary Supplier", cost=8000, delay_reduction=8, inventory_impact=100),
    OptimizationAction(name="Delay Product Launch", cost=0, delay_reduction=0, inventory_impact=0),
)