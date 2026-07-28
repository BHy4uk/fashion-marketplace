"""Identity event handlers — Identity reacts to cross-domain events that affect
reputation (which it OWNS, Q7 / DOMAIN-008 §11):
  - ReviewPublished -> apply the rating to the recipient's reputation.
Idempotent (at-least-once delivery safe) via a per-review applied-guard."""
from __future__ import annotations

from buildingblocks.mongo import get_db
from buildingblocks.outbox import subscribe

from .service import IdentityService


async def on_review_published(event: dict) -> None:
    p = event["payload"]
    await IdentityService(get_db()).apply_review(
        p["review_id"], p["recipient_id"], p["rating"])


def register() -> None:
    subscribe("ReviewPublished", on_review_published)
