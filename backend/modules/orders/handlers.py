"""Orders event handlers — subscribe Orders to cross-domain events.

Orders is created ONLY in reaction to OfferAccepted (event-driven; Offers and
Orders never call each other directly)."""
from __future__ import annotations

from buildingblocks.mongo import get_db
from buildingblocks.outbox import subscribe

from .service import OrderService


async def on_offer_accepted(event: dict) -> None:
    await OrderService(get_db()).create_from_offer_accepted(event["payload"])


def register() -> None:
    subscribe("OfferAccepted", on_offer_accepted)
