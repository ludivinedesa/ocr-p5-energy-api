import json

from fastapi import FastAPI

from app.config import SAMPLE_INPUT_PATH
from app.model_service import load_metadata, predict_energy
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


@app.get("/sample-input")
def sample_input():
    with open(SAMPLE_INPUT_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


@app.post("/predict", response_model=PredictionResponse)
def predict(features: BuildingFeatures):
    return predict_energy(features)
