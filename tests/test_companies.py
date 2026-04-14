import pytest
import responses

from spedy_api.exceptions import NotFoundError

BASE = "https://sandbox-api.spedy.com.br/v1"

COMPANY_PAYLOAD = {
    "name": "Minha Empresa",
    "legalName": "Minha Empresa Ltda",
    "federalTaxNumber": "12345678000195",
    "email": "contato@minhaempresa.com.br",
    "address": {
        "street": "Av. Paulista",
        "number": "1000",
        "district": "Bela Vista",
        "postalCode": "01310100",
        "city": {"code": "3550308"},
    },
    "taxRegime": "simplesNacional",
    "economicActivities": [{"code": "6201500", "isMain": True}],
}

COMPANY_RESPONSE = {
    "id": "uuid-da-empresa",
    "name": "Minha Empresa",
    "legalName": "Minha Empresa Ltda",
    "federalTaxNumber": "12345678000195",
    "taxRegime": "simplesNacional",
    "apiCredentials": {"apiKey": "CHAVE-API-DA-NOVA-EMPRESA"},
}


class TestCreate:
    def test_returns_company_with_api_key(self, client, mocked):
        mocked.add(responses.POST, f"{BASE}/companies", json=COMPANY_RESPONSE, status=200)

        result = client.companies.create(COMPANY_PAYLOAD)

        assert result["id"] == "uuid-da-empresa"
        assert result["apiCredentials"]["apiKey"] == "CHAVE-API-DA-NOVA-EMPRESA"

    def test_sends_api_key_header(self, client, mocked):
        mocked.add(responses.POST, f"{BASE}/companies", json=COMPANY_RESPONSE, status=200)

        client.companies.create(COMPANY_PAYLOAD)

        assert mocked.calls[0].request.headers["X-Api-Key"] == "test-api-key"

    def test_sends_payload_as_json(self, client, mocked):
        import json

        mocked.add(responses.POST, f"{BASE}/companies", json=COMPANY_RESPONSE, status=200)

        client.companies.create(COMPANY_PAYLOAD)

        sent = json.loads(mocked.calls[0].request.body)
        assert sent["federalTaxNumber"] == "12345678000195"


class TestList:
    def test_returns_paginated_response(self, client, mocked):
        body = {
            "items": [COMPANY_RESPONSE],
            "totalCount": 1,
            "pageCount": 1,
            "pageSize": 20,
            "hasNext": False,
        }
        mocked.add(responses.GET, f"{BASE}/companies", json=body, status=200)

        result = client.companies.list()

        assert result["totalCount"] == 1
        assert result["items"][0]["id"] == "uuid-da-empresa"

    def test_default_pagination_params(self, client, mocked):
        mocked.add(responses.GET, f"{BASE}/companies", json={}, status=200)

        client.companies.list()

        qs = mocked.calls[0].request.url
        assert "page=1" in qs
        assert "pageSize=20" in qs

    def test_custom_pagination_params(self, client, mocked):
        mocked.add(responses.GET, f"{BASE}/companies", json={}, status=200)

        client.companies.list(page=3, page_size=5)

        qs = mocked.calls[0].request.url
        assert "page=3" in qs
        assert "pageSize=5" in qs


class TestGet:
    def test_returns_company(self, client, mocked):
        mocked.add(
            responses.GET,
            f"{BASE}/companies/uuid-da-empresa",
            json=COMPANY_RESPONSE,
            status=200,
        )

        result = client.companies.get("uuid-da-empresa")

        assert result["id"] == "uuid-da-empresa"

    def test_raises_not_found(self, client, mocked):
        mocked.add(
            responses.GET,
            f"{BASE}/companies/nonexistent",
            status=404,
        )

        with pytest.raises(NotFoundError):
            client.companies.get("nonexistent")


class TestUpdate:
    def test_returns_updated_company(self, client, mocked):
        updated = {**COMPANY_RESPONSE, "name": "Novo Nome"}
        mocked.add(
            responses.PUT,
            f"{BASE}/companies/uuid-da-empresa",
            json=updated,
            status=200,
        )

        result = client.companies.update("uuid-da-empresa", {"name": "Novo Nome"})

        assert result["name"] == "Novo Nome"

    def test_sends_put_request(self, client, mocked):
        mocked.add(
            responses.PUT,
            f"{BASE}/companies/uuid-da-empresa",
            json=COMPANY_RESPONSE,
            status=200,
        )

        client.companies.update("uuid-da-empresa", {"name": "X"})

        assert mocked.calls[0].request.method == "PUT"


class TestDelete:
    def test_returns_success(self, client, mocked):
        mocked.add(
            responses.DELETE,
            f"{BASE}/companies/uuid-da-empresa",
            json={"success": True},
            status=200,
        )

        result = client.companies.delete("uuid-da-empresa")

        assert result["success"] is True

    def test_sends_delete_request(self, client, mocked):
        mocked.add(
            responses.DELETE,
            f"{BASE}/companies/uuid-da-empresa",
            json={"success": True},
            status=200,
        )

        client.companies.delete("uuid-da-empresa")

        assert mocked.calls[0].request.method == "DELETE"


class TestUploadCertificate:
    def test_uploads_pfx_as_multipart(self, client, mocked, tmp_path):
        pfx_file = tmp_path / "cert.pfx"
        pfx_file.write_bytes(b"fake-pfx-content")

        mocked.add(
            responses.POST,
            f"{BASE}/companies/uuid-da-empresa/certificates",
            json={"success": True},
            status=200,
        )

        result = client.companies.upload_certificate(
            "uuid-da-empresa", str(pfx_file), "s3cr3t"
        )

        assert result["success"] is True
        content_type = mocked.calls[0].request.headers["Content-Type"]
        assert "multipart/form-data" in content_type

    def test_raises_not_found_for_unknown_company(self, client, mocked, tmp_path):
        pfx_file = tmp_path / "cert.pfx"
        pfx_file.write_bytes(b"fake-pfx-content")

        mocked.add(
            responses.POST,
            f"{BASE}/companies/nonexistent/certificates",
            status=404,
        )

        with pytest.raises(NotFoundError):
            client.companies.upload_certificate(
                "nonexistent", str(pfx_file), "s3cr3t"
            )


class TestUpdateSettings:
    def test_sends_put_to_settings_endpoint(self, client, mocked):
        mocked.add(
            responses.PUT,
            f"{BASE}/companies/uuid-da-empresa/settings",
            json={"success": True},
            status=200,
        )

        result = client.companies.update_settings("uuid-da-empresa", {"serie": "1"})

        assert result["success"] is True
        assert mocked.calls[0].request.method == "PUT"
        assert "/settings" in mocked.calls[0].request.url
