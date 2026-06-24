"""Database operations used to log model predictions."""

from typing import Any, Optional
from uuid import UUID

from psycopg2.extras import Json

from app.database import database_connection


def create_prediction_request(
    input_data: dict[str, Any],
    source: str = "api",
    building_id: Optional[int] = None,
) -> UUID:
    """Insert a pending prediction request and return its UUID."""
    query = """
        INSERT INTO prediction_requests (
            building_id,
            input_data,
            source,
            status
        )
        VALUES (%s, %s, %s, 'pending')
        RETURNING request_id;
    """

    with database_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                query,
                (
                    building_id,
                    Json(input_data),
                    source,
                ),
            )
            request_id = cursor.fetchone()[0]

    return request_id


def save_prediction_result(
    request_id: UUID,
    model_version: str,
    prediction: dict[str, Any],
) -> None:
    """
    Save a prediction result and mark its request as successful.

    The result is linked to the model_versions row matching
    the version returned by the prediction service.
    """
    insert_result_query = """
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
            %s,
            %s,
            %s
        FROM model_versions
        WHERE version = %s
          AND is_active = TRUE;
    """

    update_request_query = """
        UPDATE prediction_requests
        SET status = 'success',
            error_message = NULL
        WHERE request_id = %s;
    """

    with database_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                insert_result_query,
                (
                    str(request_id),
                    prediction["predicted_site_energy_use_kbtu"],
                    prediction["predicted_site_energy_use_gwh"],
                    prediction["audit_priority"],
                    model_version,
                ),
            )

            if cursor.rowcount != 1:
                raise RuntimeError(
                    "No active model version matches "
                    f"the prediction version: {model_version}"
                )

            cursor.execute(
                update_request_query,
                (str(request_id),),
            )


def mark_prediction_request_as_error(
    request_id: UUID,
    error_message: str,
) -> None:
    """Mark an existing prediction request as failed."""
    query = """
        UPDATE prediction_requests
        SET status = 'error',
            error_message = %s
        WHERE request_id = %s;
    """

    with database_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                query,
                (
                    error_message,
                    str(request_id),
                ),
            )
