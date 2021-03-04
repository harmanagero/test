import logging

import pytest
from fastapi.testclient import TestClient
from src import __version__
from src.api.api import app


@pytest.fixture
def client():
    client = TestClient(app)
    yield client


def test_request_id_middleware_on_correlationid_passed_assigns_it_as_expected(client):
    client.get("/health", headers={"x-correlation-id": "cor-id-1234"})
    _logger = logging.getLogger()
    assert _logger.agero_extensions.correlation_id == "cor-id-1234"
    assert _logger.agero_extensions.request_id is not None


def test_request_id_middleware_on_correlationid_not_passed_creates_it_as_expected(
    client,
):
    client.get("/health")
    _logger = logging.getLogger()
    assert _logger.agero_extensions.correlation_id is not None
    assert _logger.agero_extensions.request_id is not None
