"""Offers event handlers — release the per-listing acceptance lock if the resulting
Order is canceled, so the listing can be negotiated again. Offers owns this lock."""
from __future__ import annotations

from buildingblocks.mongo import get_db
from buildingblocks.outbox import subscribe

from .service import OfferService


async def on_order_canceled(event: dict) -> None:
    await OfferService(get_db()).release_listing_acceptance(event["payload"]["listing_id"])


def register() -> None:
    subscribe("OrderCanceled", on_order_canceled)
