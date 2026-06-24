"""PostgreSQL connection utilities for the OCR P5 API."""

from contextlib import contextmanager
from typing import Generator

import psycopg2
from psycopg2.extensions import connection

from app.config import (
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USER,
)


def get_connection() -> connection:
    """Create and return a new PostgreSQL connection."""
    if not POSTGRES_PASSWORD:
        raise RuntimeError(
            "POSTGRES_PASSWORD is missing. "
            "Define it in the local .env file or environment variables."
        )

    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )


@contextmanager
def database_connection() -> Generator[connection, None, None]:
    """
    Provide a PostgreSQL connection and close it automatically.

    The transaction is committed if no exception occurs.
    It is rolled back automatically by psycopg2 if an exception occurs
    before the context exits.
    """
    conn = get_connection()

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
