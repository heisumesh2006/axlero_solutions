"""PuLP-backed optimization service for supply-chain mitigation actions."""

from pulp import LpBinary, LpMaximize, LpProblem, LpVariable, PULP_CBC_CMD, value

from .sample_data import ACTIONS, OptimizationAction
from .schemas import OptimizationRecommendation, OptimizationRequest, OptimizationResponse


class OptimizationService:
    """Select and rank feasible actions without changing operational state."""

    def optimize(self, request: OptimizationRequest) -> OptimizationResponse:
        """Return up to three feasible actions ranked by benefit, then cost."""
        problem = LpProblem("supply_prescript_optimization", LpMaximize)
        selected = {
            action.name: LpVariable(f"select_{index}", cat=LpBinary)
            for index, action in enumerate(ACTIONS)
        }

        for action in ACTIONS:
            variable = selected[action.name]
            problem += action.cost * variable <= request.budget
            problem += action.inventory_impact * variable <= request.inventory_units

        # Delay reduction is primary; lower cost is the deterministic tie-breaker.
        cost_weight = max(action.cost for action in ACTIONS) + 1
        problem += sum(
            (action.delay_reduction * cost_weight - action.cost + 0.001) * selected[action.name]
            for action in ACTIONS
        )
        problem.solve(PULP_CBC_CMD(msg=False))

        feasible = [
            action
            for action in ACTIONS
            if value(selected[action.name]) is not None and value(selected[action.name]) >= 0.5
        ]
        ranked_actions = sorted(feasible, key=self._ranking_key)[:3]

        return OptimizationResponse(
            recommendations=[
                OptimizationRecommendation(
                    rank=rank,
                    action=action.name,
                    cost=action.cost,
                    delay_reduction=action.delay_reduction,
                    inventory_impact=action.inventory_impact,
                    score=self._score(action),
                )
                for rank, action in enumerate(ranked_actions, start=1)
            ]
        )

    @staticmethod
    def _ranking_key(action: OptimizationAction) -> tuple[float, float, str]:
        """Sort by highest delay reduction and then lowest cost."""
        return (-action.delay_reduction, action.cost, action.name)

    @staticmethod
    def _score(action: OptimizationAction) -> float:
        """Expose the same deterministic score used by the LP objective."""
        cost_weight = max(candidate.cost for candidate in ACTIONS) + 1
        return action.delay_reduction * cost_weight - action.cost