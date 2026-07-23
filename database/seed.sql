-- SupplyPrescript realistic development seed data.
-- Run after database/schema.sql in an empty development database.

BEGIN;

INSERT INTO suppliers (supplier_code, supplier_name, country_code, average_lead_time_days, reliability_score) VALUES
('SUP-001', 'Shenzhen Circuit Works', 'CN', 24, 82.50),
('SUP-002', 'Bavaria Industrial Components', 'DE', 12, 94.20),
('SUP-003', 'Osaka Precision Manufacturing', 'JP', 18, 91.30),
('SUP-004', 'Monterrey Fabrication Group', 'MX', 9, 88.70),
('SUP-005', 'Bengaluru Electronics Supply', 'IN', 21, 79.40),
('SUP-006', 'Rotterdam Materials BV', 'NL', 14, 92.10),
('SUP-007', 'Busan Logistics Parts', 'KR', 19, 86.80),
('SUP-008', 'Taipei Micro Systems', 'TW', 20, 90.50),
('SUP-009', 'Milan Packaging SRL', 'IT', 11, 93.00),
('SUP-010', 'Sao Paulo Industrial SA', 'BR', 17, 76.90),
('SUP-011', 'Warsaw Automation Sp z o.o.', 'PL', 13, 89.60),
('SUP-012', 'Hanoi Textile Solutions', 'VN', 23, 78.20),
('SUP-013', 'Toronto Components Ltd.', 'CA', 8, 95.10),
('SUP-014', 'Istanbul Fasteners AS', 'TR', 16, 84.70),
('SUP-015', 'Bangkok Polymer Co.', 'TH', 22, 80.80),
('SUP-016', 'Johannesburg Mining Supply', 'ZA', 25, 75.30),
('SUP-017', 'Singapore Control Systems', 'SG', 15, 96.20),
('SUP-018', 'Prague Sensor Technologies', 'CZ', 12, 90.10),
('SUP-019', 'Melbourne Specialty Metals', 'AU', 28, 87.40),
('SUP-020', 'Dubai Trade Components', 'AE', 10, 88.90);

INSERT INTO products (product_sku, product_name, product_category, unit_cost, current_inventory_units, reorder_point_units) VALUES
('SKU-1001', 'Industrial Control Module', 'Electronics', 425.00, 240, 100),
('SKU-1002', 'Precision Ball Bearing', 'Mechanical', 38.50, 1300, 500),
('SKU-1003', 'Stainless Steel Housing', 'Metalwork', 112.00, 620, 250),
('SKU-1004', 'High Voltage Cable Reel', 'Electrical', 285.00, 180, 90),
('SKU-1005', 'Hydraulic Seal Kit', 'Mechanical', 64.75, 980, 400),
('SKU-1006', 'Temperature Sensor', 'Sensors', 155.00, 410, 180),
('SKU-1007', 'Polymer Resin Pellets', 'Raw Materials', 3.80, 8400, 3000),
('SKU-1008', 'Servo Motor Assembly', 'Electronics', 680.00, 95, 50),
('SKU-1009', 'Corrugated Packaging Roll', 'Packaging', 42.00, 2100, 800),
('SKU-1010', 'Copper Busbar', 'Electrical', 94.00, 740, 300),
('SKU-1011', 'PLC Input Card', 'Electronics', 310.00, 160, 80),
('SKU-1012', 'Safety Valve', 'Mechanical', 128.50, 460, 200),
('SKU-1013', 'Aluminum Extrusion', 'Metalwork', 76.00, 870, 350),
('SKU-1014', 'Optical Proximity Sensor', 'Sensors', 198.00, 270, 120),
('SKU-1015', 'Nylon Fastener Pack', 'Fasteners', 18.25, 3200, 1000),
('SKU-1016', 'Lithium Battery Pack', 'Energy', 540.00, 110, 60),
('SKU-1017', 'Conveyor Belt Section', 'Mechanical', 365.00, 75, 40),
('SKU-1018', 'Thermal Insulation Sheet', 'Raw Materials', 29.50, 1500, 600),
('SKU-1019', 'RFID Reader', 'Electronics', 245.00, 205, 100),
('SKU-1020', 'Steel Spring Set', 'Mechanical', 51.25, 950, 380),
('SKU-1021', 'Actuator Assembly', 'Automation', 725.00, 68, 35),
('SKU-1022', 'Silicone Adhesive Drum', 'Raw Materials', 89.00, 390, 160),
('SKU-1023', 'Terminal Block', 'Electrical', 22.75, 2600, 900),
('SKU-1024', 'Carbon Filter Cartridge', 'Filtration', 136.00, 340, 140),
('SKU-1025', 'Gearbox Unit', 'Mechanical', 890.00, 42, 25),
('SKU-1026', 'Machine Vision Camera', 'Sensors', 1150.00, 36, 20),
('SKU-1027', 'Protective Foam Insert', 'Packaging', 12.40, 4500, 1500),
('SKU-1028', 'Pressure Transducer', 'Sensors', 275.00, 190, 90),
('SKU-1029', 'Galvanized Bolt Set', 'Fasteners', 34.00, 2800, 1000),
('SKU-1030', 'Power Distribution Panel', 'Electrical', 960.00, 55, 30);

INSERT INTO shipments (
    shipment_reference, supplier_id, product_id, origin_country_code, destination_country_code,
    transport_mode, quantity_units, inventory_units_at_dispatch, shipment_cost, shipped_at,
    planned_delivery_at, shipment_status
)
SELECT
    format('SHP-%s', lpad(gs::text, 5, '0')),
    ((gs - 1) % 20) + 1,
    ((gs * 7 - 1) % 30) + 1,
    s.country_code,
    'US',
    CASE gs % 4 WHEN 0 THEN 'sea' WHEN 1 THEN 'air' WHEN 2 THEN 'road' ELSE 'rail' END,
    40 + ((gs * 37) % 460),
    25 + ((gs * 53) % 1300),
    ROUND((850 + ((gs * 173) % 6200) + (CASE gs % 4 WHEN 1 THEN 1400 ELSE 0 END))::NUMERIC, 2),
    TIMESTAMPTZ '2025-01-01 08:00:00+00' + (gs * INTERVAL '2 days'),
    TIMESTAMPTZ '2025-01-01 08:00:00+00' + (gs * INTERVAL '2 days') +
      (s.average_lead_time_days * INTERVAL '1 day'),
    'delivered'
FROM generate_series(1, 100) AS gs
JOIN suppliers s ON s.supplier_id = ((gs - 1) % 20) + 1;

INSERT INTO model_versions (model_version, accuracy, training_date, notes) VALUES
('xgb-delay-v1.0.0', 0.8735, DATE '2024-12-20', 'Initial XGBoost delay-risk model trained on historical supplier, route, inventory, and shipment-cost features.');
INSERT INTO predictions (shipment_id, model_version, delay_probability, expected_delay_days, predicted_at)
SELECT
    shipment_id,
    'xgb-delay-v1.0.0',
    ROUND((LEAST(0.95, 0.08 + ((shipment_id * 13) % 70) / 100.0 +
        CASE transport_mode WHEN 'sea' THEN 0.12 WHEN 'air' THEN -0.05 ELSE 0.03 END))::NUMERIC, 4),
    ROUND((0.30 + ((shipment_id * 11) % 55) / 10.0 +
        CASE transport_mode WHEN 'sea' THEN 1.20 WHEN 'air' THEN -0.20 ELSE 0.40 END)::NUMERIC, 2),
    shipped_at + INTERVAL '1 day'
FROM shipments;

INSERT INTO recommendations (
    shipment_id, prediction_id, recommendation_rank, action_type, action_summary,
    recommendation_cost, expected_delay_reduction_days, expected_roi
)
SELECT
    p.shipment_id,
    p.prediction_id,
    r.recommendation_rank,
    CASE r.recommendation_rank
        WHEN 1 THEN 'expedite_air'
        WHEN 2 THEN 'reroute_carrier'
        ELSE 'increase_safety_stock'
    END,
    CASE r.recommendation_rank
        WHEN 1 THEN 'Expedite the highest-risk portion of this shipment by air.'
        WHEN 2 THEN 'Reroute through the preferred carrier network to reduce transit risk.'
        ELSE 'Increase safety-stock coverage at the destination until delivery is confirmed.'
    END,
    ROUND((CASE r.recommendation_rank
        WHEN 1 THEN 950 + ((p.shipment_id * 41) % 1400)
        WHEN 2 THEN 420 + ((p.shipment_id * 29) % 750)
        ELSE 180 + ((p.shipment_id * 17) % 450)
    END)::NUMERIC, 2),
    ROUND((CASE r.recommendation_rank
        WHEN 1 THEN LEAST(p.expected_delay_days, 3.5)
        WHEN 2 THEN LEAST(p.expected_delay_days, 2.2)
        ELSE LEAST(p.expected_delay_days, 1.1)
    END)::NUMERIC, 2),
    ROUND((CASE r.recommendation_rank
        WHEN 1 THEN 0.18 + ((p.shipment_id % 20) / 100.0)
        WHEN 2 THEN 0.25 + ((p.shipment_id % 25) / 100.0)
        ELSE 0.30 + ((p.shipment_id % 15) / 100.0)
    END)::NUMERIC, 4)
FROM predictions p
CROSS JOIN (VALUES (1::SMALLINT), (2::SMALLINT), (3::SMALLINT)) AS r(recommendation_rank);

INSERT INTO decisions (shipment_id, recommendation_id, decision_status, decided_by, decision_notes, decided_at)
SELECT
    r.shipment_id,
    r.recommendation_id,
    'approved',
    CASE r.shipment_id % 5
        WHEN 0 THEN 'Ava Patel'
        WHEN 1 THEN 'Liam Chen'
        WHEN 2 THEN 'Sofia Martinez'
        WHEN 3 THEN 'Noah Williams'
        ELSE 'Mia Robinson'
    END,
    'Selected after reviewing model risk, inventory coverage, and incremental cost.',
    s.shipped_at + INTERVAL '1 day 2 hours'
FROM recommendations r
JOIN shipments s ON s.shipment_id = r.shipment_id
WHERE r.recommendation_rank = ((r.shipment_id - 1) % 3) + 1;

INSERT INTO actual_outcomes (
    shipment_id, delivered_at, actual_delay_days, actual_transport_cost,
    actual_recommendation_cost, actual_total_cost, delay_penalty_cost, realized_roi, outcome_notes
)
SELECT
    scenario.shipment_id,
    scenario.planned_delivery_at + (scenario.actual_delay_days * INTERVAL '1 day'),
    scenario.actual_delay_days,
    ROUND((scenario.shipment_cost * (1 + ((scenario.shipment_id % 9) - 4) / 100.0))::NUMERIC, 2),
    scenario.actual_recommendation_cost,
    ROUND((scenario.shipment_cost * (1 + ((scenario.shipment_id % 9) - 4) / 100.0) +
           scenario.actual_recommendation_cost + scenario.delay_penalty_cost)::NUMERIC, 2),
    scenario.delay_penalty_cost,
    ROUND(((scenario.avoided_penalty - scenario.actual_recommendation_cost) /
           NULLIF(scenario.actual_recommendation_cost, 0))::NUMERIC, 4),
    CASE WHEN scenario.actual_delay_days = 0 THEN 'Delivered on time after mitigation.'
         WHEN scenario.actual_delay_days <= 2 THEN 'Minor delay; customer commitment maintained.'
         ELSE 'Delay recorded for model performance monitoring.' END
FROM (
    SELECT
        s.*,
        d.recommendation_id,
        r.recommendation_cost,
        GREATEST(0, ROUND((p.expected_delay_days + ((s.shipment_id % 7) - 3) * 0.45 -
            r.expected_delay_reduction_days * 0.65)::NUMERIC, 2)) AS actual_delay_days,
        ROUND((r.recommendation_cost * (0.90 + ((s.shipment_id % 5) * 0.05)))::NUMERIC, 2)
            AS actual_recommendation_cost,
        ROUND((GREATEST(0, p.expected_delay_days -
            GREATEST(0, p.expected_delay_days + ((s.shipment_id % 7) - 3) * 0.45 -
            r.expected_delay_reduction_days * 0.65)) * 750 +
            (s.quantity_units * 6))::NUMERIC, 2) AS avoided_penalty,
        ROUND((GREATEST(0, p.expected_delay_days + ((s.shipment_id % 7) - 3) * 0.45 -
            r.expected_delay_reduction_days * 0.65) * 900 +
            CASE WHEN s.inventory_units_at_dispatch < 150 THEN 450 ELSE 0 END)::NUMERIC, 2)
            AS delay_penalty_cost
    FROM shipments s
    JOIN predictions p ON p.shipment_id = s.shipment_id
    JOIN decisions d ON d.shipment_id = s.shipment_id
    JOIN recommendations r ON r.recommendation_id = d.recommendation_id
) AS scenario;

COMMIT;