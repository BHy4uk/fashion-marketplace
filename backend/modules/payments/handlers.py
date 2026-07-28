"""Payments event handlers — Payments reacts to Order lifecycle:
  - OrderCompleted  -> schedule the escrow payout release (+hold window)
  - OrderCanceled   -> refund/void any captured payment
Payments never mutates Orders; it only emits money events Orders reacts to."""
from __future__ import annotations

from buildingblocks.mongo import get_db
from buildingblocks.outbox import subscribe

from .service import PaymentService


async def on_order_completed(event: dict) -> None:
    await PaymentService(get_db()).schedule_release_for_order(event["payload"]["order_id"])


async def on_order_canceled(event: dict) -> None:
    await PaymentService(get_db()).refund_for_order(event["payload"]["order_id"])


def register() -> None:
    subscribe("OrderCompleted", on_order_completed)
    subscribe("OrderCanceled", on_order_canceled)
