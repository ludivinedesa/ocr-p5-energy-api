from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"

MODEL_PATH = ARTIFACTS_DIR / "model_pipeline.joblib"
METADATA_PATH = ARTIFACTS_DIR / "model_metadata.json"
SAMPLE_INPUTS_PATH = ARTIFACTS_DIR / "sample_inputs.json"
