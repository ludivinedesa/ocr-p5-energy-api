import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"

# Load local environment variables from the project .env file.
# In CI or production, existing environment variables remain authoritative.
load_dotenv(PROJECT_ROOT / ".env", override=False)

MODEL_PATH = ARTIFACTS_DIR / "model_pipeline.joblib"
METADATA_PATH = ARTIFACTS_DIR / "model_metadata.json"
SAMPLE_INPUTS_PATH = ARTIFACTS_DIR / "sample_inputs.json"

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "ocr_p5_energy")
POSTGRES_USER = os.getenv("POSTGRES_USER", "ocr_p5_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

DATABASE_LOGGING_ENABLED = (
    os.getenv("DATABASE_LOGGING_ENABLED", "false").strip().lower()
    in {"1", "true", "yes", "on"}
)

API_KEY = os.getenv("API_KEY")
