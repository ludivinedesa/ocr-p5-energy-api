-- ============================================================
-- OCR P5 - PostgreSQL schema
-- Project: Déployez un modèle de Machine Learning
-- Use case: Seattle building energy consumption prediction
-- ============================================================

-- Enable UUID generation for request identifiers
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================
-- Table: buildings
-- Role:
-- Stores the reference building data extracted from the Seattle
-- energy benchmarking dataset.
-- ============================================================
CREATE TABLE IF NOT EXISTS buildings (
    building_id SERIAL PRIMARY KEY,

    ose_building_id INTEGER UNIQUE,
    building_type VARCHAR(100),
    primary_property_type VARCHAR(150),
    property_name TEXT,

    address TEXT,
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    neighborhood VARCHAR(100),

    latitude NUMERIC(10, 6),
    longitude NUMERIC(10, 6),

    year_built INTEGER,
    number_of_buildings NUMERIC,
    number_of_floors NUMERIC,

    property_gfa_total NUMERIC,
    property_gfa_parking NUMERIC,
    property_gfa_buildings NUMERIC,

    site_energy_use_kbtu NUMERIC,
    total_ghg_emissions NUMERIC,

    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Table: model_versions
-- Role:
-- Stores metadata about the machine learning model used by the API.
-- ============================================================
CREATE TABLE IF NOT EXISTS model_versions (
    model_version_id SERIAL PRIMARY KEY,

    model_name VARCHAR(150) NOT NULL,
    model_type VARCHAR(150) NOT NULL,
    version VARCHAR(50) NOT NULL UNIQUE,
    artifact_path TEXT NOT NULL,

    metrics JSONB,
    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Table: prediction_requests
-- Role:
-- Stores each request sent to the prediction endpoint.
-- ============================================================
CREATE TABLE IF NOT EXISTS prediction_requests (
    request_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    building_id INTEGER REFERENCES buildings(building_id),
    input_data JSONB NOT NULL,

    source VARCHAR(100) DEFAULT 'api',
    status VARCHAR(30) DEFAULT 'pending',

    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_prediction_request_status
        CHECK (status IN ('pending', 'success', 'error'))
);

-- ============================================================
-- Table: prediction_results
-- Role:
-- Stores the prediction returned by the model for each request.
-- ============================================================
CREATE TABLE IF NOT EXISTS prediction_results (
    prediction_result_id SERIAL PRIMARY KEY,

    request_id UUID NOT NULL UNIQUE
        REFERENCES prediction_requests(request_id)
        ON DELETE CASCADE,

    model_version_id INTEGER
        REFERENCES model_versions(model_version_id),

    predicted_site_energy_use_kbtu NUMERIC NOT NULL,
    predicted_site_energy_use_gwh NUMERIC NOT NULL,
    audit_priority VARCHAR(100),

    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Helpful indexes
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_buildings_ose_building_id
    ON buildings(ose_building_id);

CREATE INDEX IF NOT EXISTS idx_buildings_primary_property_type
    ON buildings(primary_property_type);

CREATE INDEX IF NOT EXISTS idx_prediction_requests_created_at
    ON prediction_requests(created_at);

CREATE INDEX IF NOT EXISTS idx_prediction_results_created_at
    ON prediction_results(created_at);
