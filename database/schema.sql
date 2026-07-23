-- SupplyPrescript PostgreSQL schema
-- PostgreSQL 14+ is recommended.

CREATE TABLE suppliers (
    supplier_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    supplier_code VARCHAR(20) NOT NULL UNIQUE,
    supplier_name VARCHAR(150) NOT NULL,
    country_code CHAR(2) NOT NULL,
    average_lead_time_days INTEGER NOT NULL,
    reliability_score NUMERIC(5,2) NOT NULL DEFAULT 80.00,
    daily_capacity INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT suppliers_country_code_check CHECK (country_code ~ '^[A-Z]{2}$'),
    CONSTRAINT suppliers_lead_time_check CHECK (average_lead_time_days BETWEEN 1 AND 365),
    CONSTRAINT suppliers_reliability_check CHECK (reliability_score BETWEEN 0 AND 100),
    CONSTRAINT suppliers_daily_capacity_check CHECK (daily_capacity >= 0)
);

CREATE TABLE products (
    product_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_sku VARCHAR(40) NOT NULL UNIQUE,
    product_name VARCHAR(200) NOT NULL,
    product_category VARCHAR(100) NOT NULL,
    unit_cost NUMERIC(12,2) NOT NULL,
    current_inventory_units INTEGER NOT NULL,
    reorder_point_units INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT products_unit_cost_check CHECK (unit_cost > 0),
    CONSTRAINT products_inventory_check CHECK (current_inventory_units >= 0),
    CONSTRAINT products_reorder_point_check CHECK (reorder_point_units >= 0)
);

CREATE TABLE shipments (
    shipment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    shipment_reference VARCHAR(40) NOT NULL UNIQUE,
    supplier_id BIGINT NOT NULL REFERENCES suppliers(supplier_id) ON DELETE RESTRICT,
    product_id BIGINT NOT NULL REFERENCES products(product_id) ON DELETE RESTRICT,
    origin_country_code CHAR(2) NOT NULL,
    destination_country_code CHAR(2) NOT NULL,
    transport_mode VARCHAR(20) NOT NULL,
    quantity_units INTEGER NOT NULL,
    inventory_units_at_dispatch INTEGER NOT NULL,
    shipment_cost NUMERIC(12,2) NOT NULL,
    weather_condition VARCHAR(30) NOT NULL DEFAULT 'unknown',
    delay_reason VARCHAR(40) NOT NULL DEFAULT 'none',
    budget_limit NUMERIC(12,2) NOT NULL DEFAULT 0,
    delivery_deadline_days SMALLINT NOT NULL DEFAULT 0,
    minimum_inventory_required INTEGER NOT NULL DEFAULT 0,
    lead_time_days SMALLINT NOT NULL DEFAULT 0,
    shipped_at TIMESTAMPTZ NOT NULL,
    planned_delivery_at TIMESTAMPTZ NOT NULL,
    shipment_status VARCHAR(20) NOT NULL DEFAULT 'in_transit',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT shipments_country_code_check CHECK (
        origin_country_code ~ '^[A-Z]{2}$' AND destination_country_code ~ '^[A-Z]{2}$'
    ),
    CONSTRAINT shipments_transport_mode_check CHECK (transport_mode IN ('air', 'road', 'rail', 'sea')),
    CONSTRAINT shipments_quantity_check CHECK (quantity_units > 0),
    CONSTRAINT shipments_inventory_snapshot_check CHECK (inventory_units_at_dispatch >= 0),
    CONSTRAINT shipments_cost_check CHECK (shipment_cost >= 0),
    CONSTRAINT shipments_weather_condition_check CHECK (weather_condition IN ('clear', 'rain', 'snow', 'storm', 'extreme_heat', 'fog', 'unknown')),
    CONSTRAINT shipments_delay_reason_check CHECK (delay_reason IN ('none', 'weather', 'carrier_capacity', 'customs', 'supplier_shortage', 'port_congestion', 'mechanical', 'labor_disruption')),
    CONSTRAINT shipments_budget_limit_check CHECK (budget_limit >= 0),
    CONSTRAINT shipments_delivery_deadline_check CHECK (delivery_deadline_days >= 0),
    CONSTRAINT shipments_minimum_inventory_check CHECK (minimum_inventory_required >= 0),
    CONSTRAINT shipments_lead_time_days_check CHECK (lead_time_days BETWEEN 0 AND 365),
    CONSTRAINT shipments_delivery_window_check CHECK (planned_delivery_at >= shipped_at),
    CONSTRAINT shipments_status_check CHECK (shipment_status IN ('planned', 'in_transit', 'delivered', 'cancelled'))
);

CREATE TABLE model_versions (
    model_version_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    model_version VARCHAR(80) NOT NULL UNIQUE,
    accuracy NUMERIC(5,4) NOT NULL,
    training_date DATE NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT model_versions_accuracy_check CHECK (accuracy BETWEEN 0 AND 1)
);
CREATE TABLE predictions (
    prediction_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    shipment_id BIGINT NOT NULL REFERENCES shipments(shipment_id) ON DELETE CASCADE,
    model_version VARCHAR(80) NOT NULL REFERENCES model_versions(model_version) ON DELETE RESTRICT,
    delay_probability NUMERIC(5,4) NOT NULL,
    expected_delay_days NUMERIC(6,2) NOT NULL,
    predicted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT predictions_shipment_model_unique UNIQUE (shipment_id, model_version),
    CONSTRAINT predictions_shipment_prediction_unique UNIQUE (shipment_id, prediction_id),
    CONSTRAINT predictions_probability_check CHECK (delay_probability BETWEEN 0 AND 1),
    CONSTRAINT predictions_expected_delay_check CHECK (expected_delay_days >= 0)
);

CREATE TABLE recommendations (
    recommendation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    shipment_id BIGINT NOT NULL REFERENCES shipments(shipment_id) ON DELETE CASCADE,
    prediction_id BIGINT NOT NULL,
    recommendation_rank SMALLINT NOT NULL,
    action_type VARCHAR(40) NOT NULL,
    action_summary TEXT NOT NULL,
    recommendation_cost NUMERIC(12,2) NOT NULL,
    expected_delay_reduction_days NUMERIC(6,2) NOT NULL,
    expected_roi NUMERIC(10,4) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT recommendations_shipment_rank_unique UNIQUE (shipment_id, recommendation_rank),
    CONSTRAINT recommendations_shipment_recommendation_unique UNIQUE (shipment_id, recommendation_id),
    CONSTRAINT recommendations_prediction_for_shipment_fk
        FOREIGN KEY (shipment_id, prediction_id)
        REFERENCES predictions (shipment_id, prediction_id) ON DELETE RESTRICT,
    CONSTRAINT recommendations_rank_check CHECK (recommendation_rank BETWEEN 1 AND 3),
    CONSTRAINT recommendations_action_type_check CHECK (action_type IN ('expedite_air', 'reroute_carrier', 'increase_safety_stock', 'air_freight', 'secondary_supplier', 'delay_launch')),
    CONSTRAINT recommendations_cost_check CHECK (recommendation_cost >= 0),
    CONSTRAINT recommendations_delay_reduction_check CHECK (expected_delay_reduction_days >= 0),
    CONSTRAINT recommendations_roi_check CHECK (expected_roi >= -1)
);

CREATE TABLE decisions (
    decision_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    shipment_id BIGINT NOT NULL,
    recommendation_id BIGINT NOT NULL,
    decision_status VARCHAR(20) NOT NULL DEFAULT 'recommended',
    decided_by VARCHAR(150) NOT NULL,
    decision_notes TEXT,
    decided_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT decisions_one_per_shipment UNIQUE (shipment_id),
    CONSTRAINT decisions_recommendation_once UNIQUE (recommendation_id),
    CONSTRAINT decisions_recommendation_for_shipment_fk
        FOREIGN KEY (shipment_id, recommendation_id)
        REFERENCES recommendations (shipment_id, recommendation_id) ON DELETE RESTRICT,
    CONSTRAINT decisions_status_check CHECK (decision_status IN ('recommended', 'approved', 'executed', 'completed', 'rejected', 'expired'))
);

CREATE TABLE actual_outcomes (
    actual_outcome_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    shipment_id BIGINT NOT NULL UNIQUE REFERENCES shipments(shipment_id) ON DELETE CASCADE,
    delivered_at TIMESTAMPTZ NOT NULL,
    actual_delay_days NUMERIC(6,2) NOT NULL,
    actual_transport_cost NUMERIC(12,2) NOT NULL,
    actual_recommendation_cost NUMERIC(12,2) NOT NULL DEFAULT 0,
    actual_total_cost NUMERIC(12,2) NOT NULL,
    delay_penalty_cost NUMERIC(12,2) NOT NULL DEFAULT 0,
    realized_roi NUMERIC(10,4),
    outcome_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT actual_outcomes_delay_check CHECK (actual_delay_days >= 0),
    CONSTRAINT actual_outcomes_transport_cost_check CHECK (actual_transport_cost >= 0),
    CONSTRAINT actual_outcomes_recommendation_cost_check CHECK (actual_recommendation_cost >= 0),
    CONSTRAINT actual_outcomes_total_cost_check CHECK (actual_total_cost >= 0),
    CONSTRAINT actual_outcomes_penalty_check CHECK (delay_penalty_cost >= 0)
);

-- PostgreSQL does not automatically index foreign-key columns.
CREATE INDEX idx_products_category ON products(product_category);
CREATE INDEX idx_shipments_supplier_id ON shipments(supplier_id);
CREATE INDEX idx_shipments_product_id ON shipments(product_id);
CREATE INDEX idx_shipments_status_planned_delivery ON shipments(shipment_status, planned_delivery_at);
CREATE INDEX idx_shipments_shipped_at ON shipments(shipped_at);
CREATE INDEX idx_predictions_shipment_predicted_at ON predictions(shipment_id, predicted_at DESC);
CREATE INDEX idx_predictions_model_version ON predictions(model_version);
CREATE INDEX idx_predictions_delay_probability ON predictions(delay_probability);
CREATE INDEX idx_recommendations_prediction_id ON recommendations(prediction_id);
CREATE INDEX idx_recommendations_shipment_id ON recommendations(shipment_id);
CREATE INDEX idx_decisions_recommendation_id ON decisions(recommendation_id);
CREATE INDEX idx_actual_outcomes_delivered_at ON actual_outcomes(delivered_at);
CREATE INDEX idx_actual_outcomes_delay_days ON actual_outcomes(actual_delay_days);
CREATE INDEX idx_model_versions_training_date ON model_versions(training_date DESC);

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER suppliers_set_updated_at BEFORE UPDATE ON suppliers
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER products_set_updated_at BEFORE UPDATE ON products
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER shipments_set_updated_at BEFORE UPDATE ON shipments
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER model_versions_set_updated_at BEFORE UPDATE ON model_versions
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER predictions_set_updated_at BEFORE UPDATE ON predictions
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER recommendations_set_updated_at BEFORE UPDATE ON recommendations
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER decisions_set_updated_at BEFORE UPDATE ON decisions
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER actual_outcomes_set_updated_at BEFORE UPDATE ON actual_outcomes
FOR EACH ROW EXECUTE FUNCTION set_updated_at();