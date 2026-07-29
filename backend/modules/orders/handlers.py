"""Orders event handlers — subscribe Orders to cross-domain events.

Orders is created ONLY in reaction to OfferAccepted (event-driven; Offers and
Orders never call each other directly)."""
from __future__ import annotations

from buildingblocks.mongo import get_db
from buildingblocks.outbox import subscribe

from .service import OrderService


async def on_offer_accepted(event: dict) -> None:
    await OrderService(get_db()).create_from_offer_accepted(event["payload"])


async def on_payment_captured(event: dict) -> None:
    p = event["payload"]
    await OrderService(get_db()).mark_paid(p["order_id"], p["payment_id"])


async def on_payment_refunded(event: dict) -> None:
    await OrderService(get_db()).mark_refunded(event["payload"]["order_id"])


# ---- reactions to Shipping domain events (Orders holds NO carrier logic) ----
async def on_shipment_created(event: dict) -> None:
    await OrderService(get_db()).begin_preparation(event["payload"]["order_id"])


async def on_shipment_dispatched(event: dict) -> None:
    p = event["payload"]
    await OrderService(get_db()).mark_shipped(p["order_id"], p["shipment_id"])


async def on_shipment_delivered(event: dict) -> None:
    await OrderService(get_db()).mark_delivered_complete(event["payload"]["order_id"])


def register() -> None:
    subscribe("OfferAccepted", on_offer_accepted)
    subscribe("PaymentCaptured", on_payment_captured)
    subscribe("PaymentRefunded", on_payment_refunded)
    subscribe("ShipmentCreated", on_shipment_created)
    subscribe("ShipmentDispatched", on_shipment_dispatched)
    subscribe("ShipmentDelivered", on_shipment_delivered)
