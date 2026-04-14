from __future__ import annotations

from ._base import BaseResource


class ProductInvoicesResource(BaseResource):
    _path = "/product-invoices"

    def create(self, data: dict) -> dict:
        return self._post(self._path, json=data)

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        effective_date_start: str | None = None,
        effective_date_end: str | None = None,
        transaction_id: str | None = None,
        receiver_federal_tax_number: str | None = None,
    ) -> dict:
        params: dict = {"page": page, "pageSize": page_size}
        if effective_date_start:
            params["effectiveDateStart"] = effective_date_start
        if effective_date_end:
            params["effectiveDateEnd"] = effective_date_end
        if transaction_id:
            params["transactionId"] = transaction_id
        if receiver_federal_tax_number:
            params["receiverFederalTaxNumber"] = receiver_federal_tax_number
        return self._get(self._path, params=params)

    def get(self, id: str) -> dict:
        return self._get(f"{self._path}/{id}")

    def cancel(self, id: str, justification: str) -> dict:
        return self._delete(f"{self._path}/{id}", json={"justification": justification})

    def add_correction(self, id: str, description: str) -> dict:
        return self._post(f"{self._path}/{id}/corrections", json={"description": description})

    def issue(self, id: str) -> dict:
        return self._post(f"{self._path}/{id}/issue")

    def check_status(self, id: str) -> dict:
        return self._post(f"{self._path}/{id}/check-status")

    def resend_email(self, id: str) -> dict:
        return self._post(f"{self._path}/{id}/resend-email")

    def get_xml(self, id: str) -> bytes:
        return self._get_raw(f"{self._path}/{id}/xml")

    def get_pdf(self, id: str) -> bytes:
        return self._get_raw(f"{self._path}/{id}/pdf")

    def list_disablements(self, page: int = 1, page_size: int = 20) -> dict:
        return self._get(
            f"{self._path}/disablement",
            params={"page": page, "pageSize": page_size},
        )

    def create_disablement(self, data: dict) -> dict:
        return self._post(f"{self._path}/disablement", json=data)
