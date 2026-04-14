import json

import pytest
import responses

from spedy_api.exceptions import NotFoundError, ValidationError

BASE = "https://sandbox-api.spedy.com.br/v1"

INVOICE_PAYLOAD = {
    "isFinalCustomer": False,
    "effectiveDate": "2024-01-15T10:00:00",
    "status": "enqueued",
    "operationType": "outgoing",
    "destination": "internal",
    "presenceType": "internet",
    "operationNature": "Venda de Mercadoria",
    "receiver": {
        "name": "Cliente Comercial Ltda",
        "federalTaxNumber": "98765432000100",
        "address": {"city": {"code": "3550308"}},
    },
    "items": [
        {
            "code": "PROD-001",
            "description": "Produto Físico Exemplo",
            "ncm": "84713012",
            "cfop": 5102,
            "unit": "UN",
            "quantity": 2,
            "unitAmount": 500.00,
            "totalAmount": 1000.00,
            "taxes": {"icms": {"origin": 0, "csosn": 400}, "pis": {"cst": 7}, "cofins": {"cst": 7}},
        }
    ],
    "payments": [{"method": "01", "amount": 1000.00}],
    "total": {"invoiceAmount": 1000.00, "productAmount": 1000.00},
}

INVOICE_RESPONSE = {
    "id": "uuid-da-nota",
    "status": "enqueued",
    "model": "productInvoice",
    "environmentType": "development",
    "number": None,
    "issuedOn": None,
    "amount": 1000.00,
    "processingDetail": {"status": "processing", "message": None, "code": None},
}


class TestCreate:
    def test_returns_invoice(self, client, mocked):
        mocked.add(responses.POST, f"{BASE}/product-invoices", json=INVOICE_RESPONSE, status=200)

        result = client.product_invoices.create(INVOICE_PAYLOAD)

        assert result["id"] == "uuid-da-nota"
        assert result["status"] == "enqueued"

    def test_sends_json_body(self, client, mocked):
        mocked.add(responses.POST, f"{BASE}/product-invoices", json=INVOICE_RESPONSE, status=200)

        client.product_invoices.create(INVOICE_PAYLOAD)

        sent = json.loads(mocked.calls[0].request.body)
        assert sent["items"][0]["cfop"] == 5102
        assert sent["total"]["invoiceAmount"] == 1000.00

    def test_raises_validation_error(self, client, mocked):
        mocked.add(
            responses.POST,
            f"{BASE}/product-invoices",
            json={"errors": [{"message": "Campo obrigatório: items"}]},
            status=400,
        )

        with pytest.raises(ValidationError) as exc_info:
            client.product_invoices.create({})

        assert "items" in str(exc_info.value)


class TestList:
    def test_returns_paginated_response(self, client, mocked):
        body = {
            "items": [INVOICE_RESPONSE],
            "totalCount": 1,
            "pageCount": 1,
            "pageSize": 20,
            "hasNext": False,
        }
        mocked.add(responses.GET, f"{BASE}/product-invoices", json=body, status=200)

        result = client.product_invoices.list()

        assert result["totalCount"] == 1
        assert result["items"][0]["id"] == "uuid-da-nota"

    def test_default_pagination_params(self, client, mocked):
        mocked.add(responses.GET, f"{BASE}/product-invoices", json={}, status=200)

        client.product_invoices.list()

        qs = mocked.calls[0].request.url
        assert "page=1" in qs
        assert "pageSize=20" in qs

    def test_date_filters_included_when_provided(self, client, mocked):
        mocked.add(responses.GET, f"{BASE}/product-invoices", json={}, status=200)

        client.product_invoices.list(
            effective_date_start="2024-01-01",
            effective_date_end="2024-01-31",
        )

        qs = mocked.calls[0].request.url
        assert "effectiveDateStart=2024-01-01" in qs
        assert "effectiveDateEnd=2024-01-31" in qs

    def test_transaction_id_filter(self, client, mocked):
        mocked.add(responses.GET, f"{BASE}/product-invoices", json={}, status=200)

        client.product_invoices.list(transaction_id="TXN-001")

        assert "transactionId=TXN-001" in mocked.calls[0].request.url

    def test_receiver_tax_number_filter(self, client, mocked):
        mocked.add(responses.GET, f"{BASE}/product-invoices", json={}, status=200)

        client.product_invoices.list(receiver_federal_tax_number="98765432000100")

        assert "receiverFederalTaxNumber=98765432000100" in mocked.calls[0].request.url

    def test_optional_filters_omitted_when_not_provided(self, client, mocked):
        mocked.add(responses.GET, f"{BASE}/product-invoices", json={}, status=200)

        client.product_invoices.list()

        qs = mocked.calls[0].request.url
        assert "effectiveDateStart" not in qs
        assert "transactionId" not in qs
        assert "receiverFederalTaxNumber" not in qs


class TestGet:
    def test_returns_invoice(self, client, mocked):
        authorized = {
            **INVOICE_RESPONSE,
            "status": "authorized",
            "number": 42,
            "accessKey": "35240112345678000195550010000000421000000000",
        }
        mocked.add(
            responses.GET,
            f"{BASE}/product-invoices/uuid-da-nota",
            json=authorized,
            status=200,
        )

        result = client.product_invoices.get("uuid-da-nota")

        assert result["status"] == "authorized"
        assert result["number"] == 42

    def test_raises_not_found(self, client, mocked):
        mocked.add(
            responses.GET,
            f"{BASE}/product-invoices/nonexistent",
            status=404,
        )

        with pytest.raises(NotFoundError):
            client.product_invoices.get("nonexistent")


class TestCancel:
    def test_sends_delete_with_justification(self, client, mocked):
        mocked.add(
            responses.DELETE,
            f"{BASE}/product-invoices/uuid-da-nota",
            json={"success": True},
            status=200,
        )

        result = client.product_invoices.cancel(
            "uuid-da-nota", "Emitida com dados incorretos do destinatário"
        )

        assert result["success"] is True
        sent = json.loads(mocked.calls[0].request.body)
        assert sent["justification"] == "Emitida com dados incorretos do destinatário"
        assert mocked.calls[0].request.method == "DELETE"


class TestAddCorrection:
    def test_posts_correction_description(self, client, mocked):
        mocked.add(
            responses.POST,
            f"{BASE}/product-invoices/uuid-da-nota/corrections",
            json={"success": True},
            status=200,
        )
        description = "Correção: informação complementar incluída nos dados adicionais"

        result = client.product_invoices.add_correction("uuid-da-nota", description)

        assert result["success"] is True
        sent = json.loads(mocked.calls[0].request.body)
        assert sent["description"] == description
        assert "/corrections" in mocked.calls[0].request.url


class TestIssue:
    def test_posts_to_issue_endpoint(self, client, mocked):
        mocked.add(
            responses.POST,
            f"{BASE}/product-invoices/uuid-da-nota/issue",
            json={"status": "enqueued"},
            status=200,
        )

        result = client.product_invoices.issue("uuid-da-nota")

        assert result["status"] == "enqueued"
        assert "/issue" in mocked.calls[0].request.url


class TestCheckStatus:
    def test_posts_to_check_status_endpoint(self, client, mocked):
        mocked.add(
            responses.POST,
            f"{BASE}/product-invoices/uuid-da-nota/check-status",
            json={"status": "authorized"},
            status=200,
        )

        result = client.product_invoices.check_status("uuid-da-nota")

        assert result["status"] == "authorized"
        assert "/check-status" in mocked.calls[0].request.url


class TestResendEmail:
    def test_posts_to_resend_email_endpoint(self, client, mocked):
        mocked.add(
            responses.POST,
            f"{BASE}/product-invoices/uuid-da-nota/resend-email",
            json={"success": True},
            status=200,
        )

        result = client.product_invoices.resend_email("uuid-da-nota")

        assert result["success"] is True
        assert "/resend-email" in mocked.calls[0].request.url


class TestGetXml:
    def test_returns_bytes(self, client, mocked):
        xml_content = b"<?xml version='1.0'?><nfeProc/>"
        mocked.add(
            responses.GET,
            f"{BASE}/product-invoices/uuid-da-nota/xml",
            body=xml_content,
            status=200,
        )

        result = client.product_invoices.get_xml("uuid-da-nota")

        assert isinstance(result, bytes)
        assert result == xml_content

    def test_does_not_send_api_key_header(self, client, mocked):
        mocked.add(
            responses.GET,
            f"{BASE}/product-invoices/uuid-da-nota/xml",
            body=b"<xml/>",
            status=200,
        )

        client.product_invoices.get_xml("uuid-da-nota")

        assert "X-Api-Key" not in mocked.calls[0].request.headers


class TestGetPdf:
    def test_returns_bytes(self, client, mocked):
        pdf_content = b"%PDF-1.4 fake danfe"
        mocked.add(
            responses.GET,
            f"{BASE}/product-invoices/uuid-da-nota/pdf",
            body=pdf_content,
            status=200,
        )

        result = client.product_invoices.get_pdf("uuid-da-nota")

        assert isinstance(result, bytes)
        assert result == pdf_content

    def test_does_not_send_api_key_header(self, client, mocked):
        mocked.add(
            responses.GET,
            f"{BASE}/product-invoices/uuid-da-nota/pdf",
            body=b"%PDF",
            status=200,
        )

        client.product_invoices.get_pdf("uuid-da-nota")

        assert "X-Api-Key" not in mocked.calls[0].request.headers


class TestListDisablements:
    def test_returns_paginated_response(self, client, mocked):
        body = {"items": [], "totalCount": 0, "pageCount": 0, "pageSize": 20, "hasNext": False}
        mocked.add(
            responses.GET,
            f"{BASE}/product-invoices/disablement",
            json=body,
            status=200,
        )

        result = client.product_invoices.list_disablements()

        assert result["totalCount"] == 0
        assert "/disablement" in mocked.calls[0].request.url

    def test_default_pagination_params(self, client, mocked):
        mocked.add(
            responses.GET,
            f"{BASE}/product-invoices/disablement",
            json={},
            status=200,
        )

        client.product_invoices.list_disablements()

        qs = mocked.calls[0].request.url
        assert "page=1" in qs
        assert "pageSize=20" in qs


class TestCreateDisablement:
    def test_posts_disablement_data(self, client, mocked):
        payload = {
            "serie": "1",
            "numberStart": 10,
            "numberEnd": 15,
            "justification": "Números não utilizados em virtude de erro no sistema emissor",
        }
        mocked.add(
            responses.POST,
            f"{BASE}/product-invoices/disablement",
            json={"success": True},
            status=200,
        )

        result = client.product_invoices.create_disablement(payload)

        assert result["success"] is True
        sent = json.loads(mocked.calls[0].request.body)
        assert sent["serie"] == "1"
        assert sent["numberStart"] == 10
        assert sent["numberEnd"] == 15
