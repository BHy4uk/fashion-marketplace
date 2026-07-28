"""Payments Infrastructure — PaymentRepository (Mongo).

Optimistic concurrency + embedded-events outbox. Unique index on order_id makes
payment creation idempotent (one payment per order for MVP)."""
from __future__ import annotations

from dataclasses import asdict

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from buildingblocks.domain import DomainError
from buildingblocks.outbox import register_event_collection, to_embedded

from .domain import Payment, PaymentTransaction

COLLECTION = "payments"


def _to_doc(p: Payment) -> dict:
    return {
        "_id": p.id, "order_id": p.order_id, "buyer_id": p.buyer_id, "seller_id": p.seller_id,
        "amount": p.amount, "currency": p.currency, "provider": p.provider,
        "status": p.status, "held": p.held, "release_at": p.release_at,
        "refunded_amount": p.refunded_amount,
        "transactions": [asdict(t) for t in p.transactions],
        "audit": {"created_at": p.audit.created_at, "created_by": p.audit.created_by,
                  "updated_at": p.audit.updated_at, "updated_by": p.audit.updated_by},
        "version": p.version,
    }


def _from_doc(d: dict) -> Payment:
    from buildingblocks.domain import AuditInfo
    a = d.get("audit", {})
    return Payment(
        id=d["_id"], order_id=d["order_id"], buyer_id=d["buyer_id"], seller_id=d["seller_id"],
        amount=d["amount"], currency=d["currency"], provider=d["provider"],
        status=d["status"], held=d.get("held", False), release_at=d.get("release_at"),
        refunded_amount=d.get("refunded_amount", 0),
        transactions=[PaymentTransaction(**t) for t in d.get("transactions", [])],
        audit=AuditInfo(**a) if a else AuditInfo(), version=d.get("version", 0))


class PaymentRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.col = db[COLLECTION]

    async def by_id(self, pid: str) -> Payment | None:
        doc = await self.col.find_one({"_id": pid})
        return _from_doc(doc) if doc else None

    async def by_order(self, order_id: str) -> Payment | None:
        doc = await self.col.find_one({"order_id": order_id})
        return _from_doc(doc) if doc else None

    async def add(self, p: Payment) -> None:
        doc = _to_doc(p)
        doc["pending_events"] = to_embedded(p.pull_events())
        try:
            await self.col.insert_one(doc)
        except DuplicateKeyError:
            raise DomainError("PAYMENT_EXISTS", "A payment already exists for this order", 409)

    async def save(self, p: Payment) -> None:
        expected = p.version
        p.version += 1
        doc = _to_doc(p)
        update = {"$set": {k: v for k, v in doc.items() if k != "_id"}}
        events = to_embedded(p.pull_events())
        if events:
            update["$push"] = {"pending_events": {"$each": events}}
        res = await self.col.update_one({"_id": p.id, "version": expected}, update)
        if res.matched_count == 0:
            raise DomainError("CONCURRENCY_CONFLICT", "Stale update detected", 409)


register_event_collection(COLLECTION)
