-- ============================================================
-- OCR P5 - Seed model versions
-- Project: Déployez un modèle de Machine Learning
-- Role:
-- Inserts or updates the metadata of the model currently used
-- by the FastAPI prediction endpoint.
-- ============================================================

INSERT INTO model_versions (
    model_name,
    model_type,
    version,
    artifact_path,
    metrics,
    is_active
)
VALUES (
    'Seattle Building Energy Consumption Model',
    'RandomForestRegressor',
    'local-v0.1.0',
    'app/artifacts/model_pipeline.joblib',
    '{
        "project": "OCR P5 - Déploiement modèle ML",
        "source_project": "Projet 3 - Anticipez les besoins en consommation de bâtiments",
        "target": "SiteEnergyUse(kBtu)",
        "target_transform": "log1p",
        "prediction_unit_after_inverse_transform": "kBtu/an",
        "random_state": 42,
        "n_rows_training": 1649,
        "n_features_raw_model_input": 17,
        "mae_oof_kbtu": 4302834.274307696,
        "mae_oof_gwh": 1.26103624480403,
        "status": "baseline_model"
    }'::jsonb,
    TRUE
)
ON CONFLICT (version)
DO UPDATE SET
    model_name = EXCLUDED.model_name,
    model_type = EXCLUDED.model_type,
    artifact_path = EXCLUDED.artifact_path,
    metrics = EXCLUDED.metrics,
    is_active = EXCLUDED.is_active;
