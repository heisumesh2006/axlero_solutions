"""End-to-end API tests. Run from backend with: python test_api.py"""

from uuid import uuid4

import pandas as pd
from fastapi.testclient import TestClient

from main import app


def main() -> None:
    shipment_id = f"TEST-{uuid4().hex[:12]}"
    shipment_payload = {
        "shipment_id": shipment_id,
        "country": "Nigeria",
        "vendor": "Test Vendor",
        "product_group": "ARV",
        "shipment_mode": "Air",
        "line_item_quantity": 1000,
        "line_item_value": 15000,
        "weight": 500,
        "freight_cost": 1200,
        "scheduled_delivery_date": "2026-09-01",
        "available_budget": 20000,
    }

    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "SupplyPrescript API is running"}

        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

        # Exercise the saved Phase 1 models using a real processed dataset row.
        real_row = pd.read_csv("data/processed_supply_chain.csv").iloc[0]
        nullable_number = lambda value: None if pd.isna(value) else float(value)
        prescription_payload = {
            "country": real_row["Country"],
            "managed_by": real_row["Managed By"],
            "fulfill_via": real_row["Fulfill Via"],
            "vendor_inco_term": real_row["Vendor INCO Term"],
            "shipment_mode": real_row["Shipment Mode"],
            "product_group": real_row["Product Group"],
            "sub_classification": real_row["Sub Classification"],
            "vendor": real_row["Vendor"],
            "brand": real_row["Brand"],
            "dosage_form": real_row["Dosage Form"],
            "manufacturing_site": real_row["Manufacturing Site"],
            "first_line_designation": real_row["First Line Designation"],
            "line_item_quantity": float(real_row["Line Item Quantity"]),
            "line_item_value": float(real_row["Line Item Value"]),
            "weight": nullable_number(real_row["Weight (Kilograms)"]),
            "freight_cost": nullable_number(real_row["Freight Cost (USD)"]),
            "scheduled_delivery_date": (
                f"{int(real_row['scheduled_year']):04d}-"
                f"{int(real_row['scheduled_month']):02d}-01"
            ),
            "available_budget": 20000,
        }
        response = client.post("/prescribe", json=prescription_payload)
        assert response.status_code == 200, response.text
        prescription = response.json()
        assert 0 <= prescription["prediction"]["delay_probability"] <= 1
        assert len(prescription["recommendations"]) == 3
        assert prescription["recommendations"][0]["feasible"] is True

        response = client.post("/shipments", json=shipment_payload)
        assert response.status_code == 201, response.text
        created_shipment = response.json()
        assert created_shipment["shipment_id"] == shipment_id

        decision_payload = {
            "shipment_id": shipment_id,
            "selected_option": "A",
            "option_title": "Air Freight",
            "predicted_delay_probability": 0.87,
            "predicted_delay_days": 14,
            "predicted_cost": 15000,
            "available_budget": 20000,
        }
        response = client.post("/decisions", json=decision_payload)
        assert response.status_code == 201, response.text
        decision = response.json()
        assert decision["decision_status"] == "EXECUTED"

        over_budget = {**decision_payload, "predicted_cost": 21000}
        response = client.post("/decisions", json=over_budget)
        assert response.status_code == 400

        response = client.get("/decisions")
        assert response.status_code == 200
        assert any(item["id"] == decision["id"] for item in response.json())

        response = client.post(
            "/outcomes",
            json={"decision_id": decision["id"], "actual_cost": 15500, "actual_delay_days": 12},
        )
        assert response.status_code == 201, response.text
        outcome = response.json()
        assert outcome["success"] is True

        response = client.post(f"/evaluate/{decision['id']}")
        assert response.status_code == 200, response.text
        evaluation = response.json()
        assert evaluation["cost_error"] == 500
        assert evaluation["delay_error"] == -2
        assert evaluation["success"] is True

        response = client.get("/analytics")
        assert response.status_code == 200
        analytics = response.json()
        assert analytics["total_decisions"] >= 1
        assert analytics["successful_decisions"] >= 1

        response = client.get("/docs")
        assert response.status_code == 200
        assert "swagger-ui" in response.text.lower()

    print("GET /: PASSED")
    print("GET /health: PASSED")
    print("POST /prescribe with real dataset row: PASSED")
    print("POST /shipments: PASSED")
    print("POST /decisions write-back: PASSED")
    print("POST /decisions budget rejection: PASSED")
    print("GET /decisions: PASSED")
    print("POST /outcomes: PASSED")
    print("POST /evaluate/{decision_id}: PASSED")
    print("GET /analytics: PASSED")
    print("GET /docs Swagger HTML: PASSED")
    print(f"Created test shipment: {shipment_id}")
    print(f"Created decision ID: {decision['id']}")
    print(f"Analytics snapshot: {analytics}")


if __name__ == "__main__":
    main()
