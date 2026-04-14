import pytest

from spedy_api import SpedyClient
from spedy_api.exceptions import AuthenticationError, NotFoundError, RateLimitError, SpedyServerError, ValidationError


def test_production_base_url():
    c = SpedyClient(api_key="key")
    assert c.base_url == "https://api.spedy.com.br/v1"


def test_sandbox_base_url():
    c = SpedyClient(api_key="key", environment="sandbox")
    assert c.base_url == "https://sandbox-api.spedy.com.br/v1"


def test_custom_base_url():
    c = SpedyClient(api_key="key", base_url="http://localhost:8000")
    assert c.base_url == "http://localhost:8000"


def test_invalid_environment():
    with pytest.raises(ValueError):
        SpedyClient(api_key="key", environment="staging")


def test_api_key_in_session_headers():
    c = SpedyClient(api_key="my-secret-key")
    assert c.session.headers["X-Api-Key"] == "my-secret-key"


def test_resources_mounted(client):
    assert client.companies is not None
    assert client.service_invoices is not None
    assert client.product_invoices is not None


def test_validation_error_on_400(client, mocked):
    import responses

    mocked.add(
        responses.GET,
        "https://sandbox-api.spedy.com.br/v1/companies/bad-id",
        json={"errors": [{"message": "Campo inválido: id"}]},
        status=400,
    )
    with pytest.raises(ValidationError) as exc_info:
        client.companies.get("bad-id")
    assert "Campo inválido: id" in str(exc_info.value)
    assert exc_info.value.errors[0]["message"] == "Campo inválido: id"


def test_authentication_error_on_403(client, mocked):
    import responses

    mocked.add(
        responses.GET,
        "https://sandbox-api.spedy.com.br/v1/companies/some-id",
        status=403,
    )
    with pytest.raises(AuthenticationError):
        client.companies.get("some-id")


def test_rate_limit_error_on_429(client, mocked):
    import responses

    mocked.add(
        responses.GET,
        "https://sandbox-api.spedy.com.br/v1/companies/some-id",
        status=429,
        headers={
            "x-rate-limit-remaining": "0",
            "x-rate-limit-reset": "2024-01-15T10:01:00Z",
        },
    )
    with pytest.raises(RateLimitError) as exc_info:
        client.companies.get("some-id")
    assert exc_info.value.remaining == "0"
    assert exc_info.value.reset == "2024-01-15T10:01:00Z"


def test_not_found_error_on_404(client, mocked):
    import responses

    mocked.add(
        responses.GET,
        "https://sandbox-api.spedy.com.br/v1/companies/some-id",
        status=404,
    )
    with pytest.raises(NotFoundError):
        client.companies.get("some-id")


def test_server_error_on_500(client, mocked):
    import responses

    mocked.add(
        responses.GET,
        "https://sandbox-api.spedy.com.br/v1/companies/some-id",
        body="Internal Server Error",
        status=500,
    )
    with pytest.raises(SpedyServerError) as exc_info:
        client.companies.get("some-id")
    assert exc_info.value.status_code == 500
