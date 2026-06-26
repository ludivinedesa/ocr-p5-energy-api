"""Integration tests against a real, isolated PostgreSQL database."""

import os
from uuid import uuid4

import psycopg2
import pytest

import app.database as database_module
from app.prediction_repository import (
    create_prediction_request,
    save_prediction_result,
)


TEST_DATABASE = os.getenv(
    "POSTGRES_TEST_DB",
    "ocr_p5_energy_test",
)
RUN_INTEGRATION_TESTS = os.getenv(
    "RUN_DB_INTEGRATION_TESTS",
    "false",
).lower() in {"1", "true", "yes"}

pytestmark = pytest.mark.skipif(
    not RUN_INTEGRATION_TESTS,
    reason=(
        "PostgreSQL integration tests are optional. Set "
        "RUN_DB_INTEGRATION_TESTS=true to run them."
    ),
)


@pytest.fixture(scope="session", autouse=True)
def use_isolated_test_database():
    """Redirect repository calls to the dedicated test database."""
    original_database = database_module.POSTGRES_DB
    database_module.POSTGRES_DB = TEST_DATABASE

    try:
        with database_module.database_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT current_database();")
                current_database = cursor.fetchone()[0]

        if current_database != TEST_DATABASE:
            pytest.fail(
                "The tests are not connected to the expected "
                f"database: {TEST_DATABASE}."
            )

        yield

    except psycopg2.OperationalError as error:
        pytest.fail(
            "Unable to connect to the PostgreSQL test database. "
            "Start Docker and initialize ocr_p5_energy_test. "
            f"Original error: {error}"
        )

    finally:
        database_module.POSTGRES_DB = original_database


@pytest.fixture(autouse=True)
def clean_prediction_tables():
    """Keep every integration test isolated and repeatable."""
    with database_module.database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "TRUNCATE prediction_results, prediction_requests "
                "RESTART IDENTITY CASCADE;"
            )

    yield

    with database_module.database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "TRUNCATE prediction_results, prediction_requests "
                "RESTART IDENTITY CASCADE;"
            )


def test_expected_tables_exist():
    """The test database contains the complete project schema."""
    expected_tables = {
        "buildings",
        "model_versions",
        "prediction_requests",
        "prediction_results",
    }

    with database_module.database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public';
                """
            )
            actual_tables = {row[0] for row in cursor.fetchall()}

    assert expected_tables.issubset(actual_tables)


def test_repository_writes_request_and_result():
    """Repository functions persist a complete prediction flow."""
    input_data = {
        "PrimaryPropertyType": "Hotel",
        "Neighborhood": "DOWNTOWN",
        "YearBuilt": 1927,
    }

    prediction = {
        "predicted_site_energy_use_kbtu": 1313220.69,
        "predicted_site_energy_use_gwh": 0.3849,
        "audit_priority": "priorité normale",
    }

    request_id = create_prediction_request(
        input_data=input_data,
    )

    save_prediction_result(
        request_id=request_id,
        model_version="local-v0.1.0",
        prediction=prediction,
    )

    with database_module.database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    request.status,
                    request.input_data,
                    result.predicted_site_energy_use_kbtu,
                    result.predicted_site_energy_use_gwh,
                    result.audit_priority
                FROM prediction_requests AS request
                JOIN prediction_results AS result
                  ON result.request_id = request.request_id
                WHERE request.request_id = %s;
                """,
                (str(request_id),),
            )
            row = cursor.fetchone()

    assert row is not None
    assert row[0] == "success"
    assert row[1] == input_data
    assert float(row[2]) == pytest.approx(1313220.69)
    assert float(row[3]) == pytest.approx(0.3849)
    assert row[4] == "priorité normale"


def test_invalid_request_status_is_rejected():
    """The CHECK constraint rejects an unsupported status."""
    with pytest.raises(psycopg2.errors.CheckViolation):
        with database_module.database_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO prediction_requests (
                        input_data,
                        status
                    )
                    VALUES (
                        '{}'::jsonb,
                        'invalid_status'
                    );
                    """
                )


def test_unknown_request_foreign_key_is_rejected():
    """A result cannot reference a request that does not exist."""
    with pytest.raises(psycopg2.errors.ForeignKeyViolation):
        with database_module.database_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO prediction_results (
                        request_id,
                        model_version_id,
                        predicted_site_energy_use_kbtu,
                        predicted_site_energy_use_gwh,
                        audit_priority
                    )
                    SELECT
                        %s,
                        model_version_id,
                        1000,
                        0.000293,
                        'priorité normale'
                    FROM model_versions
                    WHERE version = 'local-v0.1.0';
                    """,
                    (str(uuid4()),),
                )


def test_deleting_request_cascades_to_result():
    """Deleting a request deletes its associated result."""
    request_id = create_prediction_request(
        input_data={"test": "cascade"},
    )

    save_prediction_result(
        request_id=request_id,
        model_version="local-v0.1.0",
        prediction={
            "predicted_site_energy_use_kbtu": 1000.0,
            "predicted_site_energy_use_gwh": 0.000293,
            "audit_priority": "priorité normale",
        },
    )

    with database_module.database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM prediction_requests
                WHERE request_id = %s;
                """,
                (str(request_id),),
            )

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM prediction_results
                WHERE request_id = %s;
                """,
                (str(request_id),),
            )

            remaining_results = cursor.fetchone()[0]

    assert remaining_results == 0
