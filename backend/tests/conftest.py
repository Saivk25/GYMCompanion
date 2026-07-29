"""Shared pytest fixtures for the backend test suite."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client() -> TestClient:
    """A TestClient against a freshly constructed app (not the module-level
    singleton), so each test gets an independent instance."""
    return TestClient(create_app())
