from __future__ import annotations

from ._base import BaseResource


class ServiceInvoicesResource(BaseResource):
    _path = "/service-invoices"

    def create(self, data: dict) -> dict:
        return self._post(self._path, json=data)

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        effective_date_start: str | None = None,
        effective_date_end: str | None = None,
    ) -> dict:
        params: dict = {"page": page, "pageSize": page_size}
        if effective_date_start:
            params["effectiveDateStart"] = effective_date_start
        if effective_date_end:
            params["effectiveDateEnd"] = effective_date_end
        return self._get(self._path, params=params)

    def get(self, id: str) -> dict:
        return self._get(f"{self._path}/{id}")

    def cancel(self, id: str, justification: str) -> dict:
        return self._delete(f"{self._path}/{id}", json={"justification": justification})

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

    def list_cities(
        self,
        code: str | None = None,
        state: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        params: dict = {"page": page, "pageSize": page_size}
        if code:
            params["code"] = code
        if state:
            params["state"] = state
        return self._get(f"{self._path}/cities", params=params)
