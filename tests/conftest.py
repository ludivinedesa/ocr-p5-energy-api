"""Shared Pytest configuration for deterministic unit tests."""

import os


# Unit and API tests must not depend on a running PostgreSQL instance
# or on values stored in a developer's local .env file.
# Tests that exercise logging explicitly enable it with monkeypatch.
os.environ["DATABASE_LOGGING_ENABLED"] = "false"

# Dummy secret used only by the automated test suite.
os.environ["API_KEY"] = "test-api-key"
