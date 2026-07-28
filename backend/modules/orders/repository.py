"""Orders Infrastructure — OrderRepository (Mongo).

Optimistic concurrency + embedded-events outbox. A unique per-listing lock
(`order_listing_locks`, _id = listing_id) guarantees only one ACTIVE order per
listing under concurrency (§21). A unique index on offer_id makes creation from
the OfferAccepted event idempotent (at-least-once delivery safe).
"""
from __future__ import annotations

from dataclasses import asdict

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from buildingblocks.domain import DomainError
from buildingblocks.outbox import register_event_collection, to_embedded

from .domain import Order, OrderItem, OrderStatusEntry

COLLECTION = "orders"
LISTING_LOCK = "order_listing_locks"   # _id = listing_id (only one active order)


def _to_doc(o: Order) -> dict:
    return {
        "_id": o.id, "order_number": o.order_number, "buyer_id": o.buyer_id,
        "seller_id": o.seller_id, "listing_id": o.listing_id, "offer_id": o.offer_id,
        "items": [asdict(i) for i in o.items], "currency": o.currency,
        "subtotal": o.subtotal, "platform_fee": o.platform_fee, "total": o.total,
        "status": o.status, "payment_ids": o.payment_ids, "shipment_ids": o.shipment_ids,
        "status_history": [asdict(h) for h in o.status_history],
        "audit": {"created_at": o.audit.created_at, "created_by": o.audit.created_by,
                  "updated_at": o.audit.updated_at, "updated_by": o.audit.updated_by},
        "version": o.version,
    }


def _from_doc(d: dict) -> Order:
    from buildingblocks.domain import AuditInfo
    a = d.get("audit", {})
    return Order(
        id=d["_id"], order_number=d["order_number"], buyer_id=d["buyer_id"],
        seller_id=d["seller_id"], listing_id=d["listing_id"], offer_id=d.get("offer_id"),
        items=[OrderItem(**i) for i in d["items"]], currency=d["currency"],
        subtotal=d["subtotal"], platform_fee=d["platform_fee"], total=d["total"],
        status=d["status"], payment_ids=d.get("payment_ids", []),
        shipment_ids=d.get("shipment_ids", []),
        status_history=[OrderStatusEntry(**h) for h in d.get("status_history", [])],
        audit=AuditInfo(**a) if a else AuditInfo(), version=d.get("version", 0))


class OrderRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.col = db[COLLECTION]

    async def by_id(self, order_id: str) -> Order | None:
        doc = await self.col.find_one({"_id": order_id})
        return _from_doc(doc) if doc else None

    async def by_offer(self, offer_id: str) -> Order | None:
        doc = await self.col.find_one({"offer_id": offer_id})
        return _from_doc(doc) if doc else None

    async def acquire_listing_lock(self, listing_id: str, order_id: str) -> None:
        try:
            await self.db[LISTING_LOCK].insert_one({"_id": listing_id, "order_id": order_id})
        except DuplicateKeyError:
            raise DomainError("ORDER_ALREADY_EXISTS",
                              "An active order already exists for this listing", 409)

    async def release_listing_lock(self, listing_id: str, order_id: str) -> None:
        await self.db[LISTING_LOCK].delete_one({"_id": listing_id, "order_id": order_id})

    async def add(self, o: Order) -> None:
        doc = _to_doc(o)
        doc["pending_events"] = to_embedded(o.pull_events())
        try:
            await self.col.insert_one(doc)
        except DuplicateKeyError:
            raise DomainError("ORDER_ALREADY_EXISTS", "Order already exists for this offer", 409)

    async def save(self, o: Order) -> None:
        expected = o.version
        o.version += 1
        doc = _to_doc(o)
        update = {"$set": {k: v for k, v in doc.items() if k != "_id"}}
        events = to_embedded(o.pull_events())
        if events:
            update["$push"] = {"pending_events": {"$each": events}}
        res = await self.col.update_one({"_id": o.id, "version": expected}, update)
        if res.matched_count == 0:
            raise DomainError("CONCURRENCY_CONFLICT", "Stale update detected", 409)


register_event_collection(COLLECTION)
