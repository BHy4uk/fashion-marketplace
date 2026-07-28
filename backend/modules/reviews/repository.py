"""Reviews Infrastructure — ReviewRepository (Mongo).

Optimistic concurrency + embedded-events atomic outbox. A unique compound index
(order_id, author_id, recipient_id) enforces INV-005 / §19: at most one review from
an author to a recipient per order, with deterministic failure under concurrency."""
from __future__ import annotations

from dataclasses import asdict

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from buildingblocks.domain import DomainError
from buildingblocks.outbox import register_event_collection, to_embedded

from .domain import Review, ReviewResponse

COLLECTION = "reviews"


def _to_doc(r: Review) -> dict:
    return {
        "_id": r.id, "order_id": r.order_id, "author_id": r.author_id,
        "recipient_id": r.recipient_id, "rating": r.rating, "comment": r.comment,
        "status": r.status,
        "response": asdict(r.response) if r.response else None,
        "audit": {"created_at": r.audit.created_at, "created_by": r.audit.created_by,
                  "updated_at": r.audit.updated_at, "updated_by": r.audit.updated_by},
        "version": r.version,
    }


def _from_doc(d: dict) -> Review:
    from buildingblocks.domain import AuditInfo
    a = d.get("audit", {})
    resp = d.get("response")
    return Review(
        id=d["_id"], order_id=d["order_id"], author_id=d["author_id"],
        recipient_id=d["recipient_id"], rating=d["rating"], comment=d.get("comment"),
        status=d.get("status", "Published"),
        response=ReviewResponse(**resp) if resp else None,
        audit=AuditInfo(**a) if a else AuditInfo(), version=d.get("version", 0))


class ReviewRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.col = db[COLLECTION]

    async def by_id(self, rid: str) -> Review | None:
        doc = await self.col.find_one({"_id": rid})
        return _from_doc(doc) if doc else None

    async def add(self, r: Review) -> None:
        doc = _to_doc(r)
        doc["pending_events"] = to_embedded(r.pull_events())
        try:
            await self.col.insert_one(doc)
        except DuplicateKeyError:
            raise DomainError("DUPLICATE_REVIEW",
                              "You have already reviewed this participant for this order", 409)

    async def save(self, r: Review) -> None:
        expected = r.version
        r.version += 1
        doc = _to_doc(r)
        update = {"$set": {k: v for k, v in doc.items() if k != "_id"}}
        events = to_embedded(r.pull_events())
        if events:
            update["$push"] = {"pending_events": {"$each": events}}
        res = await self.col.update_one({"_id": r.id, "version": expected}, update)
        if res.matched_count == 0:
            raise DomainError("CONCURRENCY_CONFLICT", "Stale update detected", 409)


register_event_collection(COLLECTION)
