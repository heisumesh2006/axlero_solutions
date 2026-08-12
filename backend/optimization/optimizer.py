"""Turn SupplyPrescript ML predictions into ranked business actions.

The optimizer uses a small linear program with one variable per action. The
variables sum to one, and an unaffordable action receives an upper bound of
zero. Since the objective is linear, the optimum selects the feasible action
with the lowest weighted cost, delay, and residual-risk score.
"""

from __future__ import annotations

from typing import Any, Mapping

import numpy as np
from scipy.optimize import linprog


# Presentation-friendly business priorities. They sum to 1.0.
COST_WEIGHT = 0.30
DELAY_WEIGHT = 0.45
RISK_WEIGHT = 0.25

# Residual risk after each action; lower is better.
RISK_FACTORS = {"LOW": 0.20, "MEDIUM": 0.50, "HIGH": 1.00}


def _validate_inputs(
    predicted_delay_days: float,
    predicted_delay_probability: float,
    shipment_cost: float,
    available_budget: float,
    minimum_inventory: float,
) -> None:
    values = {
        "predicted_delay_days": predicted_delay_days,
        "predicted_delay_probability": predicted_delay_probability,
        "shipment_cost": shipment_cost,
        "available_budget": available_budget,
        "minimum_inventory": minimum_inventory,
    }
    for name, value in values.items():
        if not isinstance(value, (int, float, np.number)) or not np.isfinite(value):
            raise ValueError(f"{name} must be a finite number.")
    if not 0 <= predicted_delay_probability <= 1:
        raise ValueError("predicted_delay_probability must be between 0 and 1.")
    if shipment_cost < 0 or available_budget < 0 or minimum_inventory < 0:
        raise ValueError("shipment_cost, available_budget, and minimum_inventory cannot be negative.")


def validate_constraints(
    recommendations: list[dict[str, Any]], available_budget: float
) -> bool:
    """Verify that feasible results obey the budget and have valid delays."""
    if available_budget < 0:
        raise ValueError("available_budget cannot be negative.")
    for recommendation in recommendations:
        if recommendation["expected_delay_days"] < 0:
            raise ValueError(
                f"Option {recommendation['option']} has a negative resulting delay."
            )
        if recommendation["feasible"] and recommendation["cost"] > available_budget:
            raise ValueError(
                f"Feasible option {recommendation['option']} exceeds the budget."
            )
    return True


def generate_prescriptions(
    predicted_delay_days: float,
    predicted_delay_probability: float,
    shipment_cost: float,
    available_budget: float,
    minimum_inventory: float = 0,
) -> list[dict[str, Any]]:
    """Return the three business actions ranked best to worst.

    ``minimum_inventory`` is treated as an inventory buffer measured in days.
    It absorbs that many days of operational delay before launch is affected.
    The prediction values are supplied by ``ml.predict`` by the caller; this
    function does not manufacture or alter ML predictions.
    """
    _validate_inputs(
        predicted_delay_days,
        predicted_delay_probability,
        shipment_cost,
        available_budget,
        minimum_inventory,
    )

    predicted_delay = max(float(predicted_delay_days), 0.0)
    buffer_days = float(minimum_inventory)
    alternatives = [
        {
            "option": "A",
            "title": "Air Freight",
            "cost": 15000.0,
            "raw_delay": 2.0,
            "risk_level": "LOW",
            "reason": "Air freight sharply reduces transit time and delay risk.",
            "tradeoff": "Higher fixed cost but much faster delivery.",
        },
        {
            "option": "B",
            "title": "Secondary Supplier",
            "cost": 1.10 * float(shipment_cost),
            "raw_delay": 7.0,
            "risk_level": "MEDIUM",
            "reason": "A backup supplier reduces dependency on the delayed shipment.",
            "tradeoff": "Moderate premium and delay with partial risk reduction.",
        },
        {
            "option": "C",
            "title": "Delay Final Product Launch",
            "cost": 0.0,
            "raw_delay": predicted_delay,
            "risk_level": "HIGH",
            "reason": "Accept the model-predicted delay without mitigation spending.",
            "tradeoff": "No added cost, but the full predicted delay and risk remain.",
        },
    ]

    # All alternatives use one common scale. Using the highest candidate cost
    # keeps normalized costs between 0 and 1 and makes dollar costs comparable.
    cost_scale = max(action["cost"] for action in alternatives) or 1.0
    delay_scale = max(predicted_delay, 7.0, 2.0, 1.0)

    for action in alternatives:
        action["expected_delay_days"] = max(action.pop("raw_delay") - buffer_days, 0.0)
        cost_score = action["cost"] / cost_scale
        delay_score = action["expected_delay_days"] / delay_scale
        risk_score = predicted_delay_probability * RISK_FACTORS[action["risk_level"]]
        action["objective_score"] = float(
            COST_WEIGHT * cost_score
            + DELAY_WEIGHT * delay_score
            + RISK_WEIGHT * risk_score
        )
        action["feasible"] = bool(action["cost"] <= available_budget)
        if not action["feasible"]:
            shortfall = action["cost"] - available_budget
            action["reason"] = (
                f"Infeasible: cost exceeds the available budget by ${shortfall:,.2f}. "
                + action["reason"]
            )

    # x[i] is the share assigned to action i. sum(x)=1 selects one action;
    # setting an unaffordable action's upper bound to zero enforces the budget.
    scores = np.array([action["objective_score"] for action in alternatives])
    bounds = [(0.0, 1.0 if action["feasible"] else 0.0) for action in alternatives]
    result = linprog(
        c=scores,
        A_eq=np.ones((1, len(alternatives))),
        b_eq=np.array([1.0]),
        bounds=bounds,
        method="highs",
    )
    if not result.success:
        raise RuntimeError(f"Optimization failed: {result.message}")

    selected_index = int(np.argmax(result.x))
    selected_option = alternatives[selected_index]["option"]
    ranked = sorted(
        alternatives,
        key=lambda action: (not action["feasible"], action["objective_score"]),
    )
    if ranked[0]["option"] != selected_option:
        raise RuntimeError("LP result does not match the ranked feasible optimum.")

    for rank, action in enumerate(ranked, start=1):
        action["rank"] = rank
        action["recommendation_label"] = (
            "RECOMMENDED" if rank == 1 else "SECOND-BEST" if rank == 2 else "THIRD-BEST"
        )

    validate_constraints(ranked, available_budget)
    if not ranked[0]["feasible"]:
        raise RuntimeError("The recommended action must be feasible.")
    return ranked


def generate_prescriptions_from_shipment(
    shipment: Mapping[str, Any],
    shipment_cost: float,
    available_budget: float,
    minimum_inventory: float = 0,
) -> list[dict[str, Any]]:
    """Run the saved Phase 1 models, then optimize actions for a real shipment."""
    from ml.predict import predict_delay_days, predict_delay_probability

    predicted_days = predict_delay_days(shipment)
    predicted_probability = predict_delay_probability(shipment)
    return generate_prescriptions(
        predicted_delay_days=predicted_days,
        predicted_delay_probability=predicted_probability,
        shipment_cost=shipment_cost,
        available_budget=available_budget,
        minimum_inventory=minimum_inventory,
    )
