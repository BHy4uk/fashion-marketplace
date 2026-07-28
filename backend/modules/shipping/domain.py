"""Shipping Domain — Shipment aggregate (DOMAIN-007).

Owns the PHYSICAL fulfilment lifecycle: carrier assignment, tracking number/label,
and shipment state. Carrier-AGNOSTIC — every carrier interaction happens behind
IShippingProvider (Infrastructure), never in the domain. Orders contains no carrier
logic; it merely reacts to the domain events this aggregate emits. Pure domain:
no framework, no provider, no DB.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from buildingblocks.domain import AggregateRoot, AuditInfo, DomainError, new_id, utc_now

# Carrier-agnostic fulfilment lifecycle. A shipment never moves backwards (append-only history).
VALID_TRANSITIONS = {
    "Pending": {"LabelCreated", "Canceled"},
    "LabelCreated": {"Dispatched", "Canceled"},
    "Dispatched": {"InTransit", "Delivered", "Returned"},
    "InTransit": {"Delivered", "Returned"},
    "Delivered": set(),
    "Returned": set(),
    "Canceled": set(),
}

TERMINAL = {"Delivered", "Returned", "Canceled"}


@dataclass(frozen=True)
class TrackingEvent:
    """Immutable, append-only tracking checkpoint (normalized across carriers)."""
    status: str                        # normalized domain status at this checkpoint
    description: str | None = None
    location: str | None = None
    carrier_code: str | None = None    # raw carrier status code (kept for audit)
    at: datetime = field(default_factory=utc_now)
    event_id: str = field(default_factory=new_id)


class Shipment(AggregateRoot):
    def __init__(self, id, order_id, buyer_id, seller_id, listing_id, carrier,
                 status="Pending", tracking_number=None, label_url=None,
                 carrier_ref=None, to_address=None, from_address=None, parcel=None,
                 estimated_delivery=None, tracking_events=None, audit=None, version=0):
        super().__init__(id, version)
        self.order_id = order_id
        self.buyer_id = buyer_id
        self.seller_id = seller_id
        self.listing_id = listing_id
        self.carrier = carrier                 # provider name (sandbox|novaposhta|ups|...)
        self.status = status
        self.tracking_number = tracking_number
        self.label_url = label_url
        self.carrier_ref = carrier_ref         # opaque provider handle (e.g. NP Ref)
        self.to_address = to_address or {}
        self.from_address = from_address or {}
        self.parcel = parcel or {}
        self.estimated_delivery = estimated_delivery
        self.tracking_events: list[TrackingEvent] = tracking_events or []
        self.audit = audit or AuditInfo(created_by=seller_id)

    @classmethod
    def create(cls, *, order_id, buyer_id, seller_id, listing_id, carrier,
               to_address=None, from_address=None, parcel=None) -> "Shipment":
        s = cls(id=new_id(), order_id=order_id, buyer_id=buyer_id, seller_id=seller_id,
                listing_id=listing_id, carrier=carrier, to_address=to_address,
                from_address=from_address, parcel=parcel, status="Pending")
        s._raise("ShipmentCreated", s._payload())
        return s

    # ---- state machine ----
    def _transition(self, target: str) -> None:
        if target not in VALID_TRANSITIONS[self.status]:
            raise DomainError("INVALID_SHIPMENT_STATE",
                              f"Cannot move shipment from {self.status} to {target}", 409)
        self.status = target
        self.audit.updated_at = utc_now()

    def _checkpoint(self, status, description=None, location=None, carrier_code=None) -> None:
        self.tracking_events.append(
            TrackingEvent(status=status, description=description,
                          location=location, carrier_code=carrier_code))

    def _payload(self, **extra) -> dict:
        return {"shipment_id": self.id, "order_id": self.order_id,
                "buyer_id": self.buyer_id, "seller_id": self.seller_id,
                "listing_id": self.listing_id, "carrier": self.carrier, **extra}

    # ---- transitions (all carrier-agnostic; providers feed normalized inputs) ----
    def assign_label(self, *, tracking_number, label_url=None, carrier_ref=None,
                     estimated_delivery=None) -> None:
        self._transition("LabelCreated")
        self.tracking_number = tracking_number
        self.label_url = label_url
        self.carrier_ref = carrier_ref
        self.estimated_delivery = estimated_delivery
        self._checkpoint("LabelCreated", "Shipping label created")
        self._raise("ShipmentLabelCreated",
                    self._payload(tracking_number=tracking_number, carrier_ref=carrier_ref))

    def dispatch(self) -> None:
        self._transition("Dispatched")
        self._checkpoint("Dispatched", "Handed to carrier")
        self._raise("ShipmentDispatched", self._payload(tracking_number=self.tracking_number))

    def mark_in_transit(self, description=None, location=None, carrier_code=None) -> bool:
        if self.status != "Dispatched":
            return False                       # idempotent: already in transit / terminal
        self._transition("InTransit")
        self._checkpoint("InTransit", description or "In transit", location, carrier_code)
        self._raise("ShipmentInTransit", self._payload())
        return True

    def mark_delivered(self, description=None, location=None, carrier_code=None) -> None:
        self._transition("Delivered")
        self._checkpoint("Delivered", description or "Delivered", location, carrier_code)
        self._raise("ShipmentDelivered", self._payload())

    def mark_returned(self, reason="returned") -> None:
        self._transition("Returned")
        self._checkpoint("Returned", reason)
        self._raise("ShipmentReturned", self._payload(reason=reason))

    def cancel(self, reason="canceled") -> None:
        self._transition("Canceled")
        self._checkpoint("Canceled", reason)
        self._raise("ShipmentCanceled", self._payload(reason=reason))
