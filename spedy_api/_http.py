from __future__ import annotations

from typing import TYPE_CHECKING, Any

import requests

from .exceptions import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    SpedyServerError,
    ValidationError,
)

if TYPE_CHECKING:
    from .client import SpedyClient


def request(
    client: SpedyClient,
    method: str,
    path: str,
    *,
    json: dict | None = None,
    params: dict | None = None,
    files: dict | None = None,
    raw: bool = False,
) -> Any:
    """
    Execute an authenticated request against the Spedy API.

    Set ``raw=True`` for endpoints that return binary content (XML, PDF).
    Those endpoints don't require the API key, so a plain session is used.
    """
    url = client.base_url.rstrip("/") + "/" + path.lstrip("/")

    if raw:
        resp = requests.get(url)
    else:
        resp = client.session.request(
            method,
            url,
            json=json,
            params=params,
            files=files,
        )

    _raise_for_status(resp)

    if raw:
        return resp.content

    if resp.status_code == 204 or not resp.content:
        return None

    return resp.json()


def _raise_for_status(resp: requests.Response) -> None:
    status = resp.status_code

    if status < 400:
        return

    if status == 400:
        try:
            body = resp.json()
            errors = body.get("errors", [{"message": resp.text}])
        except Exception:
            errors = [{"message": resp.text}]
        raise ValidationError(errors)

    if status == 403:
        raise AuthenticationError("Invalid API key or insufficient permissions.")

    if status == 404:
        raise NotFoundError("Resource not found.")

    if status == 429:
        raise RateLimitError(
            remaining=resp.headers.get("x-rate-limit-remaining"),
            reset=resp.headers.get("x-rate-limit-reset"),
        )

    if status >= 500:
        raise SpedyServerError(status, resp.text)

    resp.raise_for_status()
