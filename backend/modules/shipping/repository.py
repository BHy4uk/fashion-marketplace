"""Shipping Infrastructure — ShipmentRepository (Mongo).

Optimistic concurrency + embedded-events atomic outbox (identical pattern to
Payments/Orders). A unique index on order_id makes shipment creation idempotent
(one shipment per order for MVP)."""
from __future__ import annotations

from dataclasses import asdict

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from buildingblocks.domain import DomainError
from buildingblocks.outbox import register_event_collection, to_embedded

from .domain import Shipment, TrackingEvent

COLLECTION = "shipments"


def _to_doc(s: Shipment) -> dict:
    return {
        "_id": s.id, "order_id": s.order_id, "buyer_id": s.buyer_id,
        "seller_id": s.seller_id, "listing_id": s.listing_id, "carrier": s.carrier,
        "status": s.status, "tracking_number": s.tracking_number,
        "label_url": s.label_url, "carrier_ref": s.carrier_ref,
        "to_address": s.to_address, "from_address": s.from_address, "parcel": s.parcel,
        "estimated_delivery": s.estimated_delivery,
        "tracking_events": [asdict(e) for e in s.tracking_events],
        "audit": {"created_at": s.audit.created_at, "created_by": s.audit.created_by,
                  "updated_at": s.audit.updated_at, "updated_by": s.audit.updated_by},
        "version": s.version,
    }


def _from_doc(d: dict) -> Shipment:
    from buildingblocks.domain import AuditInfo
    a = d.get("audit", {})
    return Shipment(
        id=d["_id"], order_id=d["order_id"], buyer_id=d["buyer_id"],
        seller_id=d["seller_id"], listing_id=d["listing_id"], carrier=d["carrier"],
        status=d["status"], tracking_number=d.get("tracking_number"),
        label_url=d.get("label_url"), carrier_ref=d.get("carrier_ref"),
        to_address=d.get("to_address"), from_address=d.get("from_address"),
        parcel=d.get("parcel"), estimated_delivery=d.get("estimated_delivery"),
        tracking_events=[TrackingEvent(**e) for e in d.get("tracking_events", [])],
        audit=AuditInfo(**a) if a else AuditInfo(), version=d.get("version", 0))


class ShipmentRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.col = db[COLLECTION]

    async def by_id(self, sid: str) -> Shipment | None:
        doc = await self.col.find_one({"_id": sid})
        return _from_doc(doc) if doc else None

    async def by_order(self, order_id: str) -> Shipment | None:
        doc = await self.col.find_one({"order_id": order_id})
        return _from_doc(doc) if doc else None

    async def add(self, s: Shipment) -> None:
        doc = _to_doc(s)
        doc["pending_events"] = to_embedded(s.pull_events())
        try:
            await self.col.insert_one(doc)
        except DuplicateKeyError:
            raise DomainError("SHIPMENT_EXISTS", "A shipment already exists for this order", 409)

    async def save(self, s: Shipment) -> None:
        expected = s.version
        s.version += 1
        doc = _to_doc(s)
        update = {"$set": {k: v for k, v in doc.items() if k != "_id"}}
        events = to_embedded(s.pull_events())
        if events:
            update["$push"] = {"pending_events": {"$each": events}}
        res = await self.col.update_one({"_id": s.id, "version": expected}, update)
        if res.matched_count == 0:
            raise DomainError("CONCURRENCY_CONFLICT", "Stale update detected", 409)


register_event_collection(COLLECTION)
