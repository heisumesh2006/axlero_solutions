"""Simple Phase 2 demonstration. Run: python optimization/test_optimizer.py"""

from optimizer import generate_prescriptions, validate_constraints


def main() -> None:
    recommendations = generate_prescriptions(
        predicted_delay_days=14,
        predicted_delay_probability=0.87,
        shipment_cost=15000,
        available_budget=20000,
    )

    print("SupplyPrescript ranked alternatives")
    print("=" * 40)
    for item in recommendations:
        print(
            f"{item['rank']}. Option {item['option']} - {item['title']} "
            f"[{item['recommendation_label']}]"
        )
        print(f"   Cost: ${item['cost']:,.2f}")
        print(f"   Expected delay: {item['expected_delay_days']:.2f} days")
        print(f"   Risk: {item['risk_level']}")
        print(f"   Objective score: {item['objective_score']:.4f}")
        print(f"   Feasible: {item['feasible']}")
        print(f"   Reason: {item['reason']}")
        print(f"   Tradeoff: {item['tradeoff']}\n")

    assert len(recommendations) == 3
    by_option = {item["option"]: item for item in recommendations}
    assert by_option["A"]["cost"] == 15000
    assert by_option["B"]["cost"] == 16500
    assert by_option["C"]["cost"] == 0
    assert all(by_option[option]["feasible"] for option in ("A", "B", "C"))
    assert validate_constraints(recommendations, available_budget=20000)
    assert recommendations[0]["feasible"]
    print(f"Recommended option: {recommendations[0]['option']} - {recommendations[0]['title']}")
    print("Constraint verification: PASSED")


if __name__ == "__main__":
    main()
