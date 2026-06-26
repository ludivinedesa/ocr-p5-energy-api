import logging

from fastapi import Depends, FastAPI

from app.config import DATABASE_LOGGING_ENABLED
from app.model_service import load_metadata, predict_energy
from app.prediction_repository import (
    create_prediction_request,
    mark_prediction_request_as_error,
    save_prediction_result,
)
from app.sample_service import get_random_sample_input
from app.security import require_api_key
from app.schemas import BuildingFeatures, PredictionResponse


logger = logging.getLogger(__name__)


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


@app.post(
    "/predict",
    response_model=PredictionResponse,
    dependencies=[Depends(require_api_key)],
)
def predict(features: BuildingFeatures):
    """
    Run the energy prediction and optionally log it in PostgreSQL.

    Database logging is controlled by the DATABASE_LOGGING_ENABLED
    environment variable.
    """
    if not DATABASE_LOGGING_ENABLED:
        return predict_energy(features)

    request_id = create_prediction_request(
        input_data=features.model_dump(),
        source="api",
    )

    try:
        prediction = predict_energy(features)

        save_prediction_result(
            request_id=request_id,
            model_version=prediction["model_version"],
            prediction=prediction,
        )

        return prediction

    except Exception as exc:
        try:
            mark_prediction_request_as_error(
                request_id=request_id,
                error_message=str(exc),
            )
        except Exception:
            logger.exception(
                "Unable to mark prediction request %s as failed.",
                request_id,
            )

        raise
