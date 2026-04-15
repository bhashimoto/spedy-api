from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import List


def _snake_to_camel(s: str) -> str:
    parts = s.split("_")
    return parts[0] + "".join(w.capitalize() for w in parts[1:])


def _to_dict(obj) -> dict:
    def _convert(value):
        if isinstance(value, dict):
            return {_snake_to_camel(k): _convert(v) for k, v in value.items() if v is not None}
        if isinstance(value, list):
            return [_convert(i) for i in value]
        return value
    return _convert(dataclasses.asdict(obj))


@dataclass
class City:
    code: str
    name: str | None = None
    state: str | None = None


@dataclass
class Address:
    street: str
    number: str
    district: str
    postal_code: str
    city: City


@dataclass
class Receiver:
    name: str
    federal_tax_number: str
    address: Address
    email: str | None = None


@dataclass
class ServiceInvoiceTotals:
    invoice_amount: float
    iss_rate: float
    iss_amount: float
    iss_withheld: bool
    pis_rate: float | None = None
    pis_amount: float | None = None
    pis_withheld: bool | None = None
    cofins_rate: float | None = None
    cofins_amount: float | None = None
    cofins_withheld: bool | None = None
    ir_rate: float | None = None
    ir_amount: float | None = None
    ir_withheld: bool | None = None
    net_amount: float | None = None


_VALID_TAXATION_TYPES = frozenset(
    ["taxationInMunicipality", "taxationOutsideMunicipality", "exemption", "exportation"]
)


@dataclass
class ServiceInvoice:
    effective_date: str
    description: str
    federal_service_code: str
    city_service_code: str
    taxation_type: str
    receiver: Receiver
    total: ServiceInvoiceTotals
    integration_id: str | None = None
    send_email_to_customer: bool = False
    nbs_code: str | None = None
    status: str = "enqueued"

    def is_valid(self) -> bool:
        if not self.effective_date:
            return False
        if not self.description:
            return False
        if not self.federal_service_code:
            return False
        if not self.city_service_code:
            return False
        if self.taxation_type not in _VALID_TAXATION_TYPES:
            return False
        if self.integration_id is not None and len(self.integration_id) > 36:
            return False

        r = self.receiver
        if not r.name or not r.federal_tax_number:
            return False
        addr = r.address
        if not addr.street or not addr.number or not addr.district or not addr.postal_code:
            return False
        if not addr.city.code:
            return False

        t = self.total
        if t.invoice_amount <= 0:
            return False
        if t.iss_rate < 0 or t.iss_amount < 0:
            return False

        return True

    def to_dict(self) -> dict:
        return _to_dict(self)


# ── Product Invoice (NF-e) ───────────────────────────────────────────────────

_VALID_OPERATION_TYPES = frozenset(["incoming", "outgoing"])
_VALID_DESTINATIONS = frozenset(["internal", "interstate", "international"])
_VALID_PRESENCE_TYPES = frozenset(
    ["none", "presence", "internet", "telephone", "delivery", "othersNonPresenceOperation"]
)


@dataclass
class IcmsTax:
    origin: int
    csosn: int | None = None      # Simples Nacional
    cst: int | None = None        # Regime Normal
    base_tax_modality: int | None = None
    base_tax: float | None = None
    base_tax_reduction: float | None = None
    rate: float | None = None
    amount: float | None = None
    sn_credit_rate: float | None = None    # CSOSN 101
    sn_credit_amount: float | None = None  # CSOSN 101
    st_retention_amount: float | None = None       # CSOSN 500 / CST 60
    base_st_retention_amount: float | None = None


@dataclass
class PisCofinsTax:
    cst: int
    base_tax: float | None = None
    rate: float | None = None
    amount: float | None = None


@dataclass
class ItemTaxes:
    icms: IcmsTax
    pis: PisCofinsTax
    cofins: PisCofinsTax


@dataclass
class ProductInvoiceItem:
    code: str
    description: str
    ncm: str
    cfop: int
    unit: str
    quantity: float
    unit_amount: float
    total_amount: float
    taxes: ItemTaxes
    unit_tax: str | None = None
    quantity_tax: float | None = None
    unit_tax_amount: float | None = None
    makeup_total: bool = True


@dataclass
class Payment:
    method: str
    amount: float


@dataclass
class ProductInvoiceTotals:
    invoice_amount: float
    product_amount: float
    icms_base_tax: float | None = None
    icms_amount: float | None = None
    pis_amount: float | None = None
    cofins_amount: float | None = None


@dataclass
class ProductInvoice:
    effective_date: str
    operation_type: str
    destination: str
    presence_type: str
    operation_nature: str
    is_final_customer: bool
    receiver: Receiver
    items: List[ProductInvoiceItem]
    payments: List[Payment]
    total: ProductInvoiceTotals
    integration_id: str | None = None
    send_email_to_customer: bool = False
    status: str = "enqueued"

    def is_valid(self) -> bool:
        if not self.effective_date:
            return False
        if self.operation_type not in _VALID_OPERATION_TYPES:
            return False
        if self.destination not in _VALID_DESTINATIONS:
            return False
        if self.presence_type not in _VALID_PRESENCE_TYPES:
            return False
        if not self.operation_nature:
            return False
        if self.integration_id is not None and len(self.integration_id) > 36:
            return False

        r = self.receiver
        if not r.name or not r.federal_tax_number:
            return False
        addr = r.address
        if not addr.street or not addr.number or not addr.district or not addr.postal_code:
            return False
        if not addr.city.code:
            return False

        if not self.items:
            return False
        for item in self.items:
            if not item.code or not item.description or not item.ncm:
                return False
            if not item.cfop or item.quantity <= 0 or item.unit_amount <= 0 or item.total_amount <= 0:
                return False
            if not item.unit:
                return False
            icms = item.taxes.icms
            if icms.csosn is None and icms.cst is None:
                return False

        if not self.payments:
            return False
        for payment in self.payments:
            if not payment.method or payment.amount <= 0:
                return False

        if self.total.invoice_amount <= 0 or self.total.product_amount <= 0:
            return False

        return True

    def to_dict(self) -> dict:
        return _to_dict(self)
