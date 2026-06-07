from fastapi import FastAPI

from app.model_service import load_metadata, predict_energy
from app.sample_service import get_random_sample_input
from app.schemas import BuildingFeatures, PredictionResponse


app = FastAPI(
    title="OCR P5 - API de prédiction énergétique",
    description=(
        "API locale permettant d'exposer le modèle du projet 3 "
        "OpenClassrooms : prédiction de la consommation énergétique "
        "des bâtiments non résidentiels de Seattle."
    ),
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "message": "API OCR P5 opérationnelle",
        "documentation": "/docs",
        "prediction_endpoint": "/predict",
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/model-info")
def model_info():
    return load_metadata()


@app.get("/sample-input", response_model=BuildingFeatures)
def sample_input():
    return get_random_sample_input()


@app.post("/predict", response_model=PredictionResponse)
def predict(features: BuildingFeatures):
    return predict_energy(features)
