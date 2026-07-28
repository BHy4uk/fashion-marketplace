"""Shipping provider abstraction + adapters (DOC-000 §13, DOMAIN-007).

IShippingProvider is the ONLY carrier abstraction the Shipping domain/application
depends on. Adding a carrier (UPS / DHL / FedEx / Meest / Ukrposhta) means writing
one new adapter here — the Shipment aggregate, the choreography, and Orders never
change. The active carrier is selected via the SHIPPING_PROVIDER config value.

Ships with:
  - SandboxShippingProvider: deterministic, no external calls (default; enables full
    local testing of the fulfilment + escrow loop without any carrier credentials).
  - NovaPoshtaProvider: real Nova Poshta API v2.0 (InternetDocument.save for the
    express waybill; TrackingDocument.getStatusDocuments for tracking).

Provider status strings are NORMALIZED to a small vocabulary the domain understands:
  pending | in_transit | delivered | returned | canceled
so carrier-specific status codes never leak past this layer.
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any

import httpx

from buildingblocks.domain import new_id, utc_now


class IShippingProvider(ABC):
    name: str

    @abstractmethod
    async def create_shipment(self, *, order_id: str, to_address: dict, from_address: dict,
                              parcel: dict, description: str) -> dict[str, Any]:
        """Register a waybill with the carrier. Returns:
        {tracking_number, label_url, carrier_ref, estimated_delivery}."""
        ...

    @abstractmethod
    async def get_tracking(self, *, tracking_number: str, carrier_ref: str | None = None,
                           phone: str | None = None) -> dict[str, Any]:
        """Return {status (normalized), description, location, carrier_code}."""
        ...

    @abstractmethod
    async def cancel_shipment(self, *, carrier_ref: str) -> dict[str, Any]:
        ...


class SandboxShippingProvider(IShippingProvider):
    """No-network carrier. Deterministic label + tracking so the fulfilment state
    machine and cross-domain choreography can be validated without credentials.
    Tracking reports `in_transit`; delivery is finalized by the buyer's explicit
    confirmation endpoint (mirrors real buyer-protection UX)."""
    name = "sandbox"

    async def create_shipment(self, *, order_id, to_address, from_address, parcel, description):
        return {"tracking_number": f"SBX{new_id()[:12].upper()}",
                "label_url": None, "carrier_ref": f"sbxref_{new_id()[:8]}",
                "estimated_delivery": (utc_now() + timedelta(days=3)).isoformat()}

    async def get_tracking(self, *, tracking_number, carrier_ref=None, phone=None):
        return {"status": "in_transit", "description": "Parcel moving to recipient city",
                "location": None, "carrier_code": "sandbox"}

    async def cancel_shipment(self, *, carrier_ref):
        return {"status": "canceled", "carrier_ref": carrier_ref}


# Nova Poshta StatusCode -> normalized domain status (createIT tracking reference).
_NP_STATUS = {
    "1": "pending", "3": "pending",
    "4": "in_transit", "41": "in_transit", "5": "in_transit", "6": "in_transit",
    "7": "in_transit", "8": "in_transit", "14": "in_transit",
    "101": "in_transit", "104": "in_transit", "105": "in_transit",
    "9": "delivered", "10": "delivered", "11": "delivered",
    "2": "canceled",
    "102": "returned", "103": "returned", "106": "returned", "108": "returned",
}


class NovaPoshtaProvider(IShippingProvider):
    """Nova Poshta adapter (API v2.0). Same JSON envelope for every call:
    {apiKey, modelName, calledMethod, methodProperties}. Note: NP returns HTTP 200
    with success:false on business errors — always inspect `success`."""
    name = "novaposhta"
    API_URL = "https://api.novaposhta.ua/v2.0/json/"

    def __init__(self, *, api_key, sender_city, sender_ref, sender_address,
                 sender_contact, sender_phone):
        self.api_key = api_key
        self.sender_city = sender_city
        self.sender_ref = sender_ref
        self.sender_address = sender_address
        self.sender_contact = sender_contact
        self.sender_phone = sender_phone

    async def _post(self, model: str, method: str, props: dict) -> dict:
        body = {"apiKey": self.api_key, "modelName": model,
                "calledMethod": method, "methodProperties": props}
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(self.API_URL, json=body)
            r.raise_for_status()
            data = r.json()
        if not data.get("success"):
            raise RuntimeError(f"NovaPoshta error: {data.get('errors') or data.get('warnings')}")
        return data

    async def create_shipment(self, *, order_id, to_address, from_address, parcel, description):
        props = {
            "PayerType": "Recipient", "PaymentMethod": "Cash",
            "DateTime": datetime.now().strftime("%d.%m.%Y"), "CargoType": "Cargo",
            "Weight": str(parcel.get("weight", "1")), "ServiceType": "WarehouseWarehouse",
            "SeatsAmount": "1", "Description": description,
            "Cost": str(parcel.get("cost", "500")),
            "CitySender": self.sender_city, "Sender": self.sender_ref,
            "SenderAddress": self.sender_address, "ContactSender": self.sender_contact,
            "SendersPhone": self.sender_phone,
            "CityRecipient": to_address.get("city_ref"),
            "Recipient": to_address.get("recipient_ref"),
            "RecipientAddress": to_address.get("address_ref"),
            "ContactRecipient": to_address.get("contact_ref"),
            "RecipientsPhone": to_address.get("phone"),
        }
        data = await self._post("InternetDocument", "save", props)
        d = data["data"][0]
        return {"tracking_number": d["IntDocNumber"], "label_url": None,
                "carrier_ref": d["Ref"], "estimated_delivery": d.get("EstimatedDeliveryDate")}

    async def get_tracking(self, *, tracking_number, carrier_ref=None, phone=None):
        docs = [{"DocumentNumber": tracking_number}]
        if phone:
            docs[0]["Phone"] = phone
        data = await self._post("TrackingDocument", "getStatusDocuments", {"Documents": docs})
        d = data["data"][0]
        code = str(d.get("StatusCode"))
        return {"status": _NP_STATUS.get(code, "in_transit"),
                "description": d.get("Status"),
                "location": d.get("CityRecipient") or d.get("WarehouseRecipient"),
                "carrier_code": code}

    async def cancel_shipment(self, *, carrier_ref):
        await self._post("InternetDocument", "delete", {"DocumentRefs": [carrier_ref]})
        return {"status": "canceled", "carrier_ref": carrier_ref}


def build_provider() -> IShippingProvider:
    choice = os.environ.get("SHIPPING_PROVIDER", "sandbox").lower()
    if choice == "novaposhta":
        key = os.environ.get("NOVAPOSHTA_API_KEY")
        if not key:
            raise RuntimeError("SHIPPING_PROVIDER=novaposhta but NOVAPOSHTA_API_KEY is not configured")
        return NovaPoshtaProvider(
            api_key=key,
            sender_city=os.environ.get("NOVAPOSHTA_SENDER_CITY", ""),
            sender_ref=os.environ.get("NOVAPOSHTA_SENDER_REF", ""),
            sender_address=os.environ.get("NOVAPOSHTA_SENDER_ADDRESS", ""),
            sender_contact=os.environ.get("NOVAPOSHTA_SENDER_CONTACT", ""),
            sender_phone=os.environ.get("NOVAPOSHTA_SENDER_PHONE", ""))
    return SandboxShippingProvider()
