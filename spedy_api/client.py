from __future__ import annotations

import requests

from .resources.companies import CompaniesResource
from .resources.product_invoices import ProductInvoicesResource
from .resources.service_invoices import ServiceInvoicesResource

_BASE_URLS = {
    "production": "https://api.spedy.com.br/v1",
    "sandbox": "https://sandbox-api.spedy.com.br/v1",
}


class SpedyClient:
    """
    Synchronous client for the Spedy API.

    Usage::

        client = SpedyClient(api_key="YOUR_KEY")                  # production
        client = SpedyClient(api_key="YOUR_KEY", environment="sandbox")
    """

    def __init__(
        self,
        api_key: str,
        environment: str = "production",
        base_url: str | None = None,
    ) -> None:
        if base_url:
            self.base_url = base_url
        else:
            if environment not in _BASE_URLS:
                raise ValueError(f"environment must be one of {list(_BASE_URLS)}; got {environment!r}")
            self.base_url = _BASE_URLS[environment]

        self.session = requests.Session()
        self.session.headers["X-Api-Key"] = api_key

        self.companies = CompaniesResource(self)
        self.service_invoices = ServiceInvoicesResource(self)
        self.product_invoices = ProductInvoicesResource(self)
