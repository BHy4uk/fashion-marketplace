"""Listings event handlers — react to Order lifecycle events.

Listings owns its own availability: it reserves itself when an Order is created
(§9) and releases the reservation if that Order is canceled. Choreography keeps
Orders from ever mutating a Listing directly."""
from __future__ import annotations

from buildingblocks.mongo import get_db
from buildingblocks.outbox import subscribe

from .service import ListingService


async def on_order_created(event: dict) -> None:
    await ListingService(get_db()).reserve_for_order(event["payload"]["listing_id"])


async def on_order_canceled(event: dict) -> None:
    await ListingService(get_db()).release_reservation(event["payload"]["listing_id"])


def register() -> None:
    subscribe("OrderCreated", on_order_created)
    subscribe("OrderCanceled", on_order_canceled)
