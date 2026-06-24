import json
from pathlib import Path

import numpy as np
import pandas as pd


RAW_DATA_PATH = Path("data/raw/2016_Building_Energy_Benchmarking.csv")
OUTPUT_PATH = Path("app/artifacts/sample_inputs.json")

FEATURE_COLUMNS = [
    "PrimaryPropertyType",
    "Neighborhood",
    "LargestPropertyUseType",
    "SecondLargestPropertyUseType",
    "ThirdLargestPropertyUseType",
    "YearBuilt_decade_cat",
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


def clean_text_column(series: pd.Series, default: str = "None") -> pd.Series:
    return (
        series.fillna(default)
        .astype(str)
        .str.strip()
        .replace({"": default, "nan": default, "None or Unspecified": default})
    )


def build_decade_category(year: pd.Series) -> pd.Series:
    decade = (year.astype(int) // 10) * 10
    return decade.astype(str) + "s"


def compute_geo_density(df: pd.DataFrame) -> pd.Series:
    """
    Approximation de la densité locale sur une grille d'environ 150 mètres.
    Cette variable sert uniquement à produire des exemples réalistes pour l'API.
    """
    has_geo = df["Latitude"].notna() & df["Longitude"].notna()

    density = pd.Series(0.0, index=df.index)

    if has_geo.sum() == 0:
        return density

    meters = 150
    lat_step = meters / 111_320

    median_latitude = df.loc[has_geo, "Latitude"].median()
    lon_step = meters / (111_320 * np.cos(np.radians(median_latitude)))

    lat_cell = np.floor(df.loc[has_geo, "Latitude"] / lat_step)
    lon_cell = np.floor(df.loc[has_geo, "Longitude"] / lon_step)

    cells = pd.DataFrame(
        {
            "lat_cell": lat_cell,
            "lon_cell": lon_cell,
        },
        index=df.loc[has_geo].index,
    )

    counts = cells.groupby(["lat_cell", "lon_cell"])["lat_cell"].transform("count")
    density.loc[has_geo] = np.log1p(counts)

    return density


def generate_sample_inputs(n_samples: int = 200) -> list[dict]:
    df = pd.read_csv(RAW_DATA_PATH)

    df = df.copy()

    df["PrimaryPropertyType"] = clean_text_column(df["PrimaryPropertyType"])
    df["Neighborhood"] = clean_text_column(df["Neighborhood"])
    df["LargestPropertyUseType"] = clean_text_column(
        df["LargestPropertyUseType"],
        default="Unknown",
    )
    df["SecondLargestPropertyUseType"] = clean_text_column(
        df["SecondLargestPropertyUseType"],
    )
    df["ThirdLargestPropertyUseType"] = clean_text_column(
        df["ThirdLargestPropertyUseType"],
    )

    required_numeric_columns = [
        "YearBuilt",
        "NumberofBuildings",
        "NumberofFloors",
        "PropertyGFATotal",
        "PropertyGFAParking",
    ]

    for column in required_numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna(subset=required_numeric_columns)
    df = df[df["PropertyGFATotal"] > 0]

    df["YearBuilt_decade_cat"] = build_decade_category(df["YearBuilt"])

    df["has_SecondLargestPropertyUseType"] = (
        df["SecondLargestPropertyUseType"].ne("None").astype(int)
    )

    df["has_ThirdLargestPropertyUseType"] = (
        df["ThirdLargestPropertyUseType"].ne("None").astype(int)
    )

    df["est_multi_usage"] = (
        (df["has_SecondLargestPropertyUseType"] == 1)
        | (df["has_ThirdLargestPropertyUseType"] == 1)
    ).astype(int)

    df["LargestPropertyUseTypeGFA"] = pd.to_numeric(
        df["LargestPropertyUseTypeGFA"],
        errors="coerce",
    )

    df["share_gfa_main"] = (
        df["LargestPropertyUseTypeGFA"] / df["PropertyGFATotal"]
    )
    df["share_gfa_main"] = df["share_gfa_main"].fillna(1.0).clip(0, 1)

    df["has_geo"] = (
        df["Latitude"].notna() & df["Longitude"].notna()
    ).astype(int)

    df["log_geo_cell_150m_count"] = compute_geo_density(df)

    df["NaturalGas(kBtu)"] = pd.to_numeric(
        df["NaturalGas(kBtu)"],
        errors="coerce",
    ).fillna(0)

    df["NaturalGas(therms)"] = pd.to_numeric(
        df["NaturalGas(therms)"],
        errors="coerce",
    ).fillna(0)

    df["has_gas"] = (
        (df["NaturalGas(kBtu)"] > 0)
        | (df["NaturalGas(therms)"] > 0)
    ).astype(int)

    samples_df = df[FEATURE_COLUMNS].sample(
        n=min(n_samples, len(df)),
        random_state=42,
    )

    samples = samples_df.to_dict(orient="records")

    return samples


def main() -> None:
    samples = generate_sample_inputs()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        json.dump(samples, file, ensure_ascii=False, indent=2)

    print(f"{len(samples)} exemples générés dans {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
