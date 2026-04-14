from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .. import _http

if TYPE_CHECKING:
    from ..client import SpedyClient


class BaseResource:
    def __init__(self, client: SpedyClient) -> None:
        self._client = client

    def _get(self, path: str, params: dict | None = None) -> Any:
        return _http.request(self._client, "GET", path, params=params)

    def _post(self, path: str, json: dict | None = None, files: dict | None = None) -> Any:
        return _http.request(self._client, "POST", path, json=json, files=files)

    def _put(self, path: str, json: dict | None = None) -> Any:
        return _http.request(self._client, "PUT", path, json=json)

    def _delete(self, path: str, json: dict | None = None) -> Any:
        return _http.request(self._client, "DELETE", path, json=json)

    def _get_raw(self, path: str) -> bytes:
        return _http.request(self._client, "GET", path, raw=True)
