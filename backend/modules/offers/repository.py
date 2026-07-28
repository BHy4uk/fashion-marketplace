"""Offers Infrastructure — OfferRepository (Mongo) + atomic acceptance lock.

Optimistic concurrency on the offer aggregate (STD-003 §9). The per-listing
acceptance lock (unique _id = listing_id) guarantees exactly-one acceptance under
concurrency (INV-005, §21) and doubles as the hand-off record Orders will consume.
"""
from __future__ import annotations

from dataclasses import asdict

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from buildingblocks.domain import DomainError
from buildingblocks.outbox import persist_events

from .domain import Offer, OfferRevision

COLLECTION = "offers"
ACCEPTANCE = "offer_acceptances"  # _id = listing_id (unique) -> exactly-one acceptance


def _to_doc(o: Offer) -> dict:
    return {
        "_id": o.id, "listing_id": o.listing_id, "buyer_id": o.buyer_id,
        "seller_id": o.seller_id, "currency": o.currency,
        "revisions": [asdict(r) for r in o.revisions],
        "status": o.status, "awaiting": o.awaiting, "expires_at": o.expires_at,
        "accepted_amount": o.accepted_amount, "current_amount": o.current_amount,
        "audit": {"created_at": o.audit.created_at, "created_by": o.audit.created_by,
                  "updated_at": o.audit.updated_at, "updated_by": o.audit.updated_by},
        "version": o.version,
    }


def _from_doc(d: dict) -> Offer:
    from buildingblocks.domain import AuditInfo
    a = d.get("audit", {})
    return Offer(
        id=d["_id"], listing_id=d["listing_id"], buyer_id=d["buyer_id"],
        seller_id=d["seller_id"], currency=d["currency"],
        revisions=[OfferRevision(**r) for r in d["revisions"]],
        status=d["status"], awaiting=d.get("awaiting"), expires_at=d.get("expires_at"),
        accepted_amount=d.get("accepted_amount"),
        audit=AuditInfo(**a) if a else AuditInfo(), version=d.get("version", 0))


class OfferRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.col = db[COLLECTION]

    async def by_id(self, offer_id: str) -> Offer | None:
        doc = await self.col.find_one({"_id": offer_id})
        return _from_doc(doc) if doc else None

    async def add(self, o: Offer) -> None:
        await self.col.insert_one(_to_doc(o))
        await persist_events(self.db, o.pull_events())

    async def save(self, o: Offer) -> None:
        expected = o.version
        o.version += 1
        res = await self.col.replace_one({"_id": o.id, "version": expected}, _to_doc(o))
        if res.matched_count == 0:
            raise DomainError("CONCURRENCY_CONFLICT", "Stale update detected", 409)
        await persist_events(self.db, o.pull_events())

    async def acquire_acceptance_lock(self, offer: Offer) -> None:
        """Atomic winner-takes-all per listing. Must be called BEFORE save on accept."""
        try:
            await self.db[ACCEPTANCE].insert_one({
                "_id": offer.listing_id, "offer_id": offer.id,
                "buyer_id": offer.buyer_id, "seller_id": offer.seller_id,
                "amount": offer.accepted_amount, "currency": offer.currency,
                "created_at": offer.audit.updated_at,
            })
        except DuplicateKeyError:
            raise DomainError("OFFER_ALREADY_ACCEPTED",
                              "Another offer for this listing has already been accepted", 409)
