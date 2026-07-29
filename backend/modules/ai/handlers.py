"""AI event handlers — auto-enrich + fraud-score a listing when it is published.

Subscribes to ListingPublished flowing through the outbox (choreography). Handlers are
idempotent (at-least-once delivery): a completed job for a subject is not recomputed.
AI is advisory — it produces signals only and never mutates listings/orders/users."""
from __future__ import annotations

import logging

from buildingblocks.mongo import get_db
from buildingblocks.outbox import subscribe

from .repository import AIJobRepository
from .service import AIService

log = logging.getLogger("ai.handlers")


async def on_listing_published(event: dict) -> None:
    payload = event.get("payload", {})
    listing_id = payload.get("listing_id")
    if not listing_id:
        return
    db = get_db()
    repo = AIJobRepository(db)
    svc = AIService(db)
    if not await repo.latest("listing_enrichment", listing_id):
        await svc.enrich_listing(listing_id)
    if not await repo.latest("fraud_analysis", listing_id):
        await svc.score_listing_fraud(listing_id)


def register() -> None:
    subscribe("ListingPublished", on_listing_published)
