"""Notifications event handlers — Notifications are created ONLY from completed
business events (DOMAIN-010 §7). Subscribes to the events already flowing through the
outbox. Handlers are idempotent (dedup by event_id + recipient)."""
from __future__ import annotations

from buildingblocks.mongo import get_db
from buildingblocks.outbox import subscribe

from .service import NotificationService

_EVENTS = ["OfferAccepted", "PaymentCaptured", "ShipmentDispatched",
           "ShipmentDelivered", "OrderCompleted", "ReviewPublished", "MessageSent"]


async def on_event(event: dict) -> None:
    await NotificationService(get_db()).handle_event(event)


def register() -> None:
    for evt in _EVENTS:
        subscribe(evt, on_event)
