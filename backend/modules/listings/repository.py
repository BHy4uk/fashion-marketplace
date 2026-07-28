"""Listings Infrastructure — ListingRepository (Mongo) + read-model queries.

Write side loads/saves the aggregate with optimistic concurrency. Read side
(search/browse) queries projections directly (CQRS-lite, STD-003 §17)."""
from __future__ import annotations

from dataclasses import asdict

from motor.motor_asyncio import AsyncIOMotorDatabase

from buildingblocks.domain import DomainError
from buildingblocks.outbox import register_event_collection, to_embedded

from .domain import Attributes, Listing, ListingImage, Money

COLLECTION = "listings"


def _to_doc(l: Listing) -> dict:
    return {
        "_id": l.id, "seller_id": l.seller_id, "title": l.title,
        "description": l.description, "slug": l.slug,
        "price": asdict(l.price), "attributes": asdict(l.attributes),
        "images": [asdict(i) for i in l.images], "state": l.state,
        "allow_offers": l.allow_offers,
        "audit": {"created_at": l.audit.created_at, "created_by": l.audit.created_by,
                  "updated_at": l.audit.updated_at, "updated_by": l.audit.updated_by},
        "version": l.version,
    }


def _from_doc(d: dict) -> Listing:
    from buildingblocks.domain import AuditInfo
    a = d.get("audit", {})
    return Listing(
        id=d["_id"], seller_id=d["seller_id"], title=d["title"],
        description=d["description"], price=Money(**d["price"]),
        attributes=Attributes(**d["attributes"]),
        images=[ListingImage(**i) for i in d.get("images", [])],
        state=d["state"], allow_offers=d.get("allow_offers", True), slug=d.get("slug"),
        audit=AuditInfo(**a) if a else AuditInfo(), version=d.get("version", 0))


class ListingRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.col = db[COLLECTION]

    async def by_id(self, listing_id: str) -> Listing | None:
        doc = await self.col.find_one({"_id": listing_id})
        return _from_doc(doc) if doc else None

    async def add(self, l: Listing) -> None:
        doc = _to_doc(l)
        doc["pending_events"] = to_embedded(l.pull_events())
        await self.col.insert_one(doc)

    async def save(self, l: Listing) -> None:
        expected = l.version
        l.version += 1
        doc = _to_doc(l)
        update = {"$set": {k: v for k, v in doc.items() if k != "_id"}}
        events = to_embedded(l.pull_events())
        if events:
            update["$push"] = {"pending_events": {"$each": events}}
        res = await self.col.update_one({"_id": l.id, "version": expected}, update)
        if res.matched_count == 0:
            raise DomainError("CONCURRENCY_CONFLICT", "Stale update detected", 409)


register_event_collection(COLLECTION)
