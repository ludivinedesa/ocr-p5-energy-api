import json
from functools import lru_cache

import joblib
import numpy as np
import pandas as pd

from app.config import METADATA_PATH, MODEL_PATH
from app.schemas import BuildingFeatures


KBTU_TO_GWH = 2.930710701722222e-7


@lru_cache(maxsize=1)
def load_model():
    """Charge le pipeline complet : prétraitement + modèle."""
    return joblib.load(MODEL_PATH)


@lru_cache(maxsize=1)
def load_metadata() -> dict:
    """Charge les informations utiles pour documenter le modèle."""
    with open(METADATA_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def compute_audit_priority(predicted_kbtu: float) -> str:
    """
    Règle métier volontairement simple pour le POC local.

    À ce stade, on ne remplace pas une analyse énergétique réelle.
    On fournit seulement une indication lisible à partir de la prédiction.
    """
    metadata = load_metadata()
    mae_kbtu = float(metadata.get("mae_oof_kbtu", 0))

    if predicted_kbtu >= 2 * mae_kbtu:
        return "priorité élevée"
    if predicted_kbtu >= mae_kbtu:
        return "à surveiller"
    return "priorité normale"


def predict_energy(features: BuildingFeatures) -> dict:
    """
    Transforme la requête API en DataFrame, lance le pipeline,
    puis convertit la prédiction log1p vers l'unité métier kBtu/an.
    """
    model = load_model()
    metadata = load_metadata()

    input_df = pd.DataFrame([features.model_dump()])

    prediction_log = float(model.predict(input_df)[0])
    prediction_kbtu = float(np.expm1(prediction_log))
    prediction_kbtu = max(prediction_kbtu, 0.0)

    return {
        "predicted_site_energy_use_kbtu": round(prediction_kbtu, 2),
        "predicted_site_energy_use_gwh": round(prediction_kbtu * KBTU_TO_GWH, 4),
        "audit_priority": compute_audit_priority(prediction_kbtu),
        "model_type": metadata.get("model_type", "unknown"),
        "model_version": "local-v0.1.0",
    }
