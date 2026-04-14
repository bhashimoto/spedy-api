import json

import pytest
import responses

from spedy_api.exceptions import NotFoundError, ValidationError

BASE = "https://sandbox-api.spedy.com.br/v1"

INVOICE_PAYLOAD = {
    "effectiveDate": "2024-01-15T10:00:00",
    "status": "enqueued",
    "sendEmailToCustomer": True,
    "description": "Prestação de serviços de consultoria em TI",
    "federalServiceCode": "1.07",
    "cityServiceCode": "0107",
    "taxationType": "taxationInMunicipality",
    "receiver": {
        "name": "Empresa Contratante Ltda",
        "federalTaxNumber": "98765432000100",
        "email": "fiscal@contratante.com.br",
        "address": {
            "street": "Av. dos Negócios",
            "number": "300",
            "district": "Itaim Bibi",
            "postalCode": "04538133",
            "city": {"code": "3550308"},
        },
    },
    "total": {
        "invoiceAmount": 3000.00,
        "issRate": 0.05,
        "issAmount": 150.00,
        "issWithheld": False,
    },
}

INVOICE_RESPONSE = {
    "id": "uuid-da-nota",
    "integrationId": "OS-0001",
    "status": "enqueued",
    "model": "serviceInvoice",
    "environmentType": "development",
    "number": None,
    "issuedOn": None,
    "amount": 3000.00,
    "processingDetail": {"status": "processing", "message": None, "code": None},
}


class TestCreate:
    def test_returns_invoice(self, client, mocked):
        mocked.add(responses.POST, f"{BASE}/service-invoices", json=INVOICE_RESPONSE, status=200)

        result = client.service_invoices.create(INVOICE_PAYLOAD)

        assert result["id"] == "uuid-da-nota"
        assert result["status"] == "enqueued"

    def test_sends_json_body(self, client, mocked):
        mocked.add(responses.POST, f"{BASE}/service-invoices", json=INVOICE_RESPONSE, status=200)

        client.service_invoices.create(INVOICE_PAYLOAD)

        sent = json.loads(mocked.calls[0].request.body)
        assert sent["federalServiceCode"] == "1.07"
        assert sent["total"]["invoiceAmount"] == 3000.00

    def test_raises_validation_error(self, client, mocked):
        mocked.add(
            responses.POST,
            f"{BASE}/service-invoices",
            json={"errors": [{"message": "Campo inválido: receiver.federalTaxNumber"}]},
            status=400,
        )

        with pytest.raises(ValidationError) as exc_info:
            client.service_invoices.create({})

        assert "receiver.federalTaxNumber" in str(exc_info.value)


class TestList:
    def test_returns_paginated_response(self, client, mocked):
        body = {
            "items": [INVOICE_RESPONSE],
            "totalCount": 1,
            "pageCount": 1,
            "pageSize": 20,
            "hasNext": False,
        }
        mocked.add(responses.GET, f"{BASE}/service-invoices", json=body, status=200)

        result = client.service_invoices.list()

        assert result["totalCount"] == 1
        assert result["items"][0]["id"] == "uuid-da-nota"

    def test_default_pagination_params(self, client, mocked):
        mocked.add(responses.GET, f"{BASE}/service-invoices", json={}, status=200)

        client.service_invoices.list()

        qs = mocked.calls[0].request.url
        assert "page=1" in qs
        assert "pageSize=20" in qs

    def test_date_filters_included_when_provided(self, client, mocked):
        mocked.add(responses.GET, f"{BASE}/service-invoices", json={}, status=200)

        client.service_invoices.list(
            effective_date_start="2024-01-01",
            effective_date_end="2024-01-31",
        )

        qs = mocked.calls[0].request.url
        assert "effectiveDateStart=2024-01-01" in qs
        assert "effectiveDateEnd=2024-01-31" in qs

    def test_date_filters_omitted_when_not_provided(self, client, mocked):
        mocked.add(responses.GET, f"{BASE}/service-invoices", json={}, status=200)

        client.service_invoices.list()

        qs = mocked.calls[0].request.url
        assert "effectiveDateStart" not in qs
        assert "effectiveDateEnd" not in qs


class TestGet:
    def test_returns_invoice(self, client, mocked):
        authorized = {**INVOICE_RESPONSE, "status": "authorized", "number": 15}
        mocked.add(
            responses.GET,
            f"{BASE}/service-invoices/uuid-da-nota",
            json=authorized,
            status=200,
        )

        result = client.service_invoices.get("uuid-da-nota")

        assert result["status"] == "authorized"
        assert result["number"] == 15

    def test_raises_not_found(self, client, mocked):
        mocked.add(
            responses.GET,
            f"{BASE}/service-invoices/nonexistent",
            status=404,
        )

        with pytest.raises(NotFoundError):
            client.service_invoices.get("nonexistent")


class TestCancel:
    def test_sends_delete_with_justification(self, client, mocked):
        mocked.add(
            responses.DELETE,
            f"{BASE}/service-invoices/uuid-da-nota",
            json={"success": True},
            status=200,
        )

        result = client.service_invoices.cancel("uuid-da-nota", "Serviço não prestado")

        assert result["success"] is True
        sent = json.loads(mocked.calls[0].request.body)
        assert sent["justification"] == "Serviço não prestado"
        assert mocked.calls[0].request.method == "DELETE"


class TestIssue:
    def test_posts_to_issue_endpoint(self, client, mocked):
        mocked.add(
            responses.POST,
            f"{BASE}/service-invoices/uuid-da-nota/issue",
            json={"status": "enqueued"},
            status=200,
        )

        result = client.service_invoices.issue("uuid-da-nota")

        assert result["status"] == "enqueued"
        assert "/issue" in mocked.calls[0].request.url


class TestCheckStatus:
    def test_posts_to_check_status_endpoint(self, client, mocked):
        mocked.add(
            responses.POST,
            f"{BASE}/service-invoices/uuid-da-nota/check-status",
            json={"status": "authorized"},
            status=200,
        )

        result = client.service_invoices.check_status("uuid-da-nota")

        assert result["status"] == "authorized"
        assert "/check-status" in mocked.calls[0].request.url


class TestResendEmail:
    def test_posts_to_resend_email_endpoint(self, client, mocked):
        mocked.add(
            responses.POST,
            f"{BASE}/service-invoices/uuid-da-nota/resend-email",
            json={"success": True},
            status=200,
        )

        result = client.service_invoices.resend_email("uuid-da-nota")

        assert result["success"] is True
        assert "/resend-email" in mocked.calls[0].request.url


class TestGetXml:
    def test_returns_bytes(self, client, mocked):
        xml_content = b"<?xml version='1.0'?><NFS-e/>"
        mocked.add(
            responses.GET,
            f"{BASE}/service-invoices/uuid-da-nota/xml",
            body=xml_content,
            status=200,
        )

        result = client.service_invoices.get_xml("uuid-da-nota")

        assert isinstance(result, bytes)
        assert result == xml_content

    def test_does_not_send_api_key_header(self, client, mocked):
        mocked.add(
            responses.GET,
            f"{BASE}/service-invoices/uuid-da-nota/xml",
            body=b"<xml/>",
            status=200,
        )

        client.service_invoices.get_xml("uuid-da-nota")

        assert "X-Api-Key" not in mocked.calls[0].request.headers


class TestGetPdf:
    def test_returns_bytes(self, client, mocked):
        pdf_content = b"%PDF-1.4 fake"
        mocked.add(
            responses.GET,
            f"{BASE}/service-invoices/uuid-da-nota/pdf",
            body=pdf_content,
            status=200,
        )

        result = client.service_invoices.get_pdf("uuid-da-nota")

        assert isinstance(result, bytes)
        assert result == pdf_content

    def test_does_not_send_api_key_header(self, client, mocked):
        mocked.add(
            responses.GET,
            f"{BASE}/service-invoices/uuid-da-nota/pdf",
            body=b"%PDF",
            status=200,
        )

        client.service_invoices.get_pdf("uuid-da-nota")

        assert "X-Api-Key" not in mocked.calls[0].request.headers


class TestListCities:
    def test_returns_paginated_cities(self, client, mocked):
        body = {
            "items": [{"id": "uuid", "code": "3550308", "name": "São Paulo", "state": "SP"}],
            "totalCount": 1,
            "pageCount": 1,
            "pageSize": 20,
            "hasNext": False,
        }
        mocked.add(responses.GET, f"{BASE}/service-invoices/cities", json=body, status=200)

        result = client.service_invoices.list_cities()

        assert result["items"][0]["code"] == "3550308"

    def test_filters_by_state(self, client, mocked):
        mocked.add(responses.GET, f"{BASE}/service-invoices/cities", json={}, status=200)

        client.service_invoices.list_cities(state="SP")

        assert "state=SP" in mocked.calls[0].request.url

    def test_filters_by_ibge_code(self, client, mocked):
        mocked.add(responses.GET, f"{BASE}/service-invoices/cities", json={}, status=200)

        client.service_invoices.list_cities(code="3550308")

        assert "code=3550308" in mocked.calls[0].request.url

    def test_state_and_code_omitted_when_not_provided(self, client, mocked):
        mocked.add(responses.GET, f"{BASE}/service-invoices/cities", json={}, status=200)

        client.service_invoices.list_cities()

        qs = mocked.calls[0].request.url
        assert "state=" not in qs
        assert "code=" not in qs
