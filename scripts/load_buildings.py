"""
Load Seattle building energy data into PostgreSQL.

This script reads the raw 2016 Building Energy Benchmarking CSV file
and inserts the useful building reference data into the PostgreSQL
`buildings` table.

It is designed to be idempotent:
running it multiple times updates existing buildings based on
OSEBuildingID instead of creating duplicates.
"""

from pathlib import Path
from typing import Any

import pandas as pd
import psycopg2
from psycopg2.extras import Json, execute_values


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = PROJECT_ROOT / "data" / "raw" / "2016_Building_Energy_Benchmarking.csv"
ENV_PATH = PROJECT_ROOT / ".env"


def load_env(env_path: Path) -> dict[str, str]:
    """Load simple KEY=VALUE pairs from a .env file."""
    env_vars: dict[str, str] = {}

    if not env_path.exists():
        raise FileNotFoundError(
            f"Missing .env file at {env_path}. "
            "Create it from .env.example before running this script."
        )

    for line in env_path.read_text().splitlines():
        line = line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        env_vars[key.strip()] = value.strip()

    return env_vars


def clean_value(value: Any) -> Any:
    """Convert pandas/numpy values into PostgreSQL-friendly Python values."""
    if pd.isna(value):
        return None

    if hasattr(value, "item"):
        return value.item()

    return value


def clean_raw_record(record: dict[str, Any]) -> dict[str, Any]:
    """Clean a full CSV row before storing it as JSONB."""
    return {key: clean_value(value) for key, value in record.items()}


def build_records(df: pd.DataFrame) -> list[tuple[Any, ...]]:
    """Transform the raw dataframe into records matching the buildings table."""
    records = []

    for _, row in df.iterrows():
        raw_record = clean_raw_record(row.to_dict())

        records.append(
            (
                clean_value(row.get("OSEBuildingID")),
                clean_value(row.get("BuildingType")),
                clean_value(row.get("PrimaryPropertyType")),
                clean_value(row.get("PropertyName")),
                clean_value(row.get("Address")),
                clean_value(row.get("City")),
                clean_value(row.get("State")),
                clean_value(row.get("ZipCode")),
                clean_value(row.get("Neighborhood")),
                clean_value(row.get("Latitude")),
                clean_value(row.get("Longitude")),
                clean_value(row.get("YearBuilt")),
                clean_value(row.get("NumberofBuildings")),
                clean_value(row.get("NumberofFloors")),
                clean_value(row.get("PropertyGFATotal")),
                clean_value(row.get("PropertyGFAParking")),
                clean_value(row.get("PropertyGFABuilding(s)")),
                clean_value(row.get("SiteEnergyUse(kBtu)")),
                clean_value(row.get("TotalGHGEmissions")),
                Json(raw_record),
            )
        )

    return records


def main() -> None:
    """Load building records into PostgreSQL."""
    env = load_env(ENV_PATH)

    connection_params = {
        "host": env.get("POSTGRES_HOST", "localhost"),
        "port": env.get("POSTGRES_PORT", "5432"),
        "dbname": env["POSTGRES_DB"],
        "user": env["POSTGRES_USER"],
        "password": env["POSTGRES_PASSWORD"],
    }

    print(f"Reading CSV file: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)

    print(f"Rows found in CSV: {len(df)}")
    records = build_records(df)

    insert_query = """
        INSERT INTO buildings (
            ose_building_id,
            building_type,
            primary_property_type,
            property_name,
            address,
            city,
            state,
            zip_code,
            neighborhood,
            latitude,
            longitude,
            year_built,
            number_of_buildings,
            number_of_floors,
            property_gfa_total,
            property_gfa_parking,
            property_gfa_buildings,
            site_energy_use_kbtu,
            total_ghg_emissions,
            raw_data
        )
        VALUES %s
        ON CONFLICT (ose_building_id)
        DO UPDATE SET
            building_type = EXCLUDED.building_type,
            primary_property_type = EXCLUDED.primary_property_type,
            property_name = EXCLUDED.property_name,
            address = EXCLUDED.address,
            city = EXCLUDED.city,
            state = EXCLUDED.state,
            zip_code = EXCLUDED.zip_code,
            neighborhood = EXCLUDED.neighborhood,
            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude,
            year_built = EXCLUDED.year_built,
            number_of_buildings = EXCLUDED.number_of_buildings,
            number_of_floors = EXCLUDED.number_of_floors,
            property_gfa_total = EXCLUDED.property_gfa_total,
            property_gfa_parking = EXCLUDED.property_gfa_parking,
            property_gfa_buildings = EXCLUDED.property_gfa_buildings,
            site_energy_use_kbtu = EXCLUDED.site_energy_use_kbtu,
            total_ghg_emissions = EXCLUDED.total_ghg_emissions,
            raw_data = EXCLUDED.raw_data;
    """

    with psycopg2.connect(**connection_params) as conn:
        with conn.cursor() as cur:
            execute_values(cur, insert_query, records, page_size=500)

            cur.execute("SELECT COUNT(*) FROM buildings;")
            count = cur.fetchone()[0]

    print(f"Buildings loaded in PostgreSQL: {count}")


if __name__ == "__main__":
    main()
