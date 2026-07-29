"""Shipping event handlers — Shipping reacts to the Order lifecycle:
  - OrderPaid -> create a Shipment (Pending) for the paid order.
Shipping never calls Orders directly; it only emits shipment events Orders reacts to."""
from __future__ import annotations

from buildingblocks.mongo import get_db
from buildingblocks.outbox import subscribe

from .service import ShippingService


async def on_order_paid(event: dict) -> None:
    await ShippingService(get_db()).create_for_order(event["payload"]["order_id"])


def register() -> None:
    subscribe("OrderPaid", on_order_paid)
