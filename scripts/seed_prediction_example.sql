-- ============================================================
-- OCR P5 - Example prediction logging
-- Purpose:
-- Validate the relationship between prediction_requests,
-- prediction_results, buildings and model_versions.
-- ============================================================

WITH selected_building AS (
    SELECT building_id
    FROM buildings
    WHERE ose_building_id = 1
    LIMIT 1
),
active_model AS (
    SELECT model_version_id
    FROM model_versions
    WHERE is_active = TRUE
    ORDER BY created_at DESC
    LIMIT 1
),
new_request AS (
    INSERT INTO prediction_requests (
        building_id,
        input_data,
        source,
        status
    )
    SELECT
        selected_building.building_id,
        '{
            "PrimaryPropertyType": "Hotel",
            "Neighborhood": "DOWNTOWN",
            "YearBuilt_decade_cat": "1920s",
            "YearBuilt": 1927,
            "NumberofBuildings": 1,
            "NumberofFloors": 12,
            "PropertyGFATotal": 88434,
            "PropertyGFAParking": 0
        }'::jsonb,
        'manual_demo',
        'success'
    FROM selected_building
    RETURNING request_id
)
INSERT INTO prediction_results (
    request_id,
    model_version_id,
    predicted_site_energy_use_kbtu,
    predicted_site_energy_use_gwh,
    audit_priority
)
SELECT
    new_request.request_id,
    active_model.model_version_id,
    1313220.69,
    0.3849,
    'priorité normale'
FROM new_request, active_model;
