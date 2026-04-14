import pytest
import responses as responses_lib

from spedy_api import SpedyClient

PROD_URL = "https://api.spedy.com.br/v1"
SANDBOX_URL = "https://sandbox-api.spedy.com.br/v1"
TEST_API_KEY = "test-api-key"


@pytest.fixture
def client():
    return SpedyClient(api_key=TEST_API_KEY, environment="sandbox")


@pytest.fixture
def mocked():
    """Activate responses mocking for the duration of a test."""
    with responses_lib.RequestsMock() as rsps:
        yield rsps
