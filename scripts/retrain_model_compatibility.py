"""Rebuild the production model with the API scikit-learn version."""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


PROJECT_ROOT = Path(__file__).resolve().parents[1]

PROCESSED_DIR = (
    PROJECT_ROOT.parent
    / "Fichiers du P3"
    / "data"
    / "processed"
)

X_PATH = PROCESSED_DIR / "model_input_X.csv"
Y_PATH = PROCESSED_DIR / "target_y_log.csv"

CANDIDATE_MODEL_PATH = (
    PROJECT_ROOT
    / "app"
    / "artifacts"
    / "model_pipeline_candidate.joblib"
)

CATEGORICAL_FEATURES = [
    "PrimaryPropertyType",
    "Neighborhood",
    "LargestPropertyUseType",
    "SecondLargestPropertyUseType",
    "ThirdLargestPropertyUseType",
    "YearBuilt_decade_cat",
]

NUMERIC_FEATURES = [
    "YearBuilt",
    "NumberofBuildings",
    "NumberofFloors",
    "PropertyGFATotal",
    "PropertyGFAParking",
    "est_multi_usage",
    "has_SecondLargestPropertyUseType",
    "share_gfa_main",
    "has_geo",
    "log_geo_cell_150m_count",
    "has_gas",
]

FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES


def load_training_data():
    """Load and validate the prepared P3 training data."""
    X = pd.read_csv(X_PATH)
    y = pd.read_csv(Y_PATH).iloc[:, 0]

    if X.shape != (1649, 17):
        raise ValueError(
            f"Unexpected X shape: {X.shape}; expected (1649, 17)."
        )

    if len(y) != 1649:
        raise ValueError(
            f"Unexpected y length: {len(y)}; expected 1649."
        )

    if X.columns.tolist() != FEATURES:
        raise ValueError(
            "The input columns do not match the expected model features."
        )

    if y.isna().any() or not np.isfinite(y).all():
        raise ValueError("The target contains missing or non-finite values.")

    for column in CATEGORICAL_FEATURES:
        X[column] = X[column].astype("object")
        X[column] = X[column].where(X[column].notna(), np.nan)

    for column in NUMERIC_FEATURES:
        X[column] = pd.to_numeric(X[column], errors="coerce")

    return X, y


def build_pipeline():
    """Build the preprocessing and Random Forest pipeline."""
    numeric_transformer = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="median",
                    add_indicator=True,
                ),
            ),
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(strategy="most_frequent"),
            ),
            (
                "onehot",
                OneHotEncoder(
                    handle_unknown="ignore",
                    min_frequency=0.01,
                    sparse_output=True,
                ),
            ),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "num",
                numeric_transformer,
                NUMERIC_FEATURES,
            ),
            (
                "cat",
                categorical_transformer,
                CATEGORICAL_FEATURES,
            ),
        ],
        remainder="drop",
    )

    model = RandomForestRegressor(
        n_estimators=200,
        min_samples_split=10,
        random_state=42,
        n_jobs=1,
    )

    return Pipeline(
        steps=[
            ("preprocess", preprocessor),
            ("model", model),
        ]
    )


def main():
    """Train and save a candidate artifact without replacing production."""
    X, y = load_training_data()
    pipeline = build_pipeline()

    print("Python/scikit-learn environment")
    print("scikit-learn :", sklearn.__version__)
    print("Training rows:", len(X))
    print("Raw features :", X.shape[1])

    pipeline.fit(X, y)
    joblib.dump(pipeline, CANDIDATE_MODEL_PATH)

    prediction_log = pipeline.predict(X.iloc[[0]])[0]
    prediction_kbtu = float(np.expm1(prediction_log))

    print("\nCandidate artifact created:")
    print(CANDIDATE_MODEL_PATH)
    print("\nExample prediction:")
    print("log1p(kBtu):", round(float(prediction_log), 6))
    print("kBtu/year :", round(prediction_kbtu, 2))


if __name__ == "__main__":
    main()
