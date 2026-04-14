from __future__ import annotations

from ._base import BaseResource


class CompaniesResource(BaseResource):
    _path = "/companies"

    def create(self, data: dict) -> dict:
        return self._post(self._path, json=data)

    def list(self, page: int = 1, page_size: int = 20) -> dict:
        return self._get(self._path, params={"page": page, "pageSize": page_size})

    def get(self, id: str) -> dict:
        return self._get(f"{self._path}/{id}")

    def update(self, id: str, data: dict) -> dict:
        return self._put(f"{self._path}/{id}", json=data)

    def delete(self, id: str) -> dict:
        return self._delete(f"{self._path}/{id}")

    def upload_certificate(self, id: str, pfx_path: str, password: str) -> dict:
        with open(pfx_path, "rb") as f:
            files = {
                "file": (pfx_path, f, "application/x-pkcs12"),
                "password": (None, password),
            }
            return self._post(f"{self._path}/{id}/certificates", files=files)

    def update_settings(self, id: str, data: dict) -> dict:
        return self._put(f"{self._path}/{id}/settings", json=data)
