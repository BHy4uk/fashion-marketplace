"""Notifications Infrastructure — NotificationRepository + preferences (Mongo).

Optimistic concurrency + embedded-events atomic outbox. A unique index on
(event_id, recipient_id) guarantees IDEMPOTENCY (INV-008/§20): a redelivered business
event can never create a duplicate user notification."""
from __future__ import annotations

from dataclasses import asdict

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from buildingblocks.domain import DomainError
from buildingblocks.outbox import register_event_collection, to_embedded

from .domain import DeliveryAttempt, Notification

COLLECTION = "notifications"
PREFS_COLLECTION = "notification_preferences"

DEFAULT_PREFS = {"email_enabled": True, "in_app_enabled": True, "muted_types": []}


def _to_doc(n: Notification) -> dict:
    return {
        "_id": n.id, "event_id": n.event_id, "event_type": n.event_type,
        "recipient_id": n.recipient_id, "notif_type": n.notif_type,
        "title": n.title, "body": n.body, "channels": n.channels,
        "status": n.status, "read": n.read,
        "deliveries": [asdict(d) for d in n.deliveries],
        "audit": {"created_at": n.audit.created_at, "created_by": n.audit.created_by,
                  "updated_at": n.audit.updated_at, "updated_by": n.audit.updated_by},
        "version": n.version,
    }


def _from_doc(d: dict) -> Notification:
    from buildingblocks.domain import AuditInfo
    a = d.get("audit", {})
    return Notification(
        id=d["_id"], event_id=d["event_id"], event_type=d["event_type"],
        recipient_id=d["recipient_id"], notif_type=d["notif_type"],
        title=d["title"], body=d["body"], channels=d.get("channels", []),
        status=d.get("status", "Created"), read=d.get("read", False),
        deliveries=[DeliveryAttempt(**x) for x in d.get("deliveries", [])],
        audit=AuditInfo(**a) if a else AuditInfo(), version=d.get("version", 0))


class NotificationRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.col = db[COLLECTION]

    async def by_id(self, nid: str) -> Notification | None:
        doc = await self.col.find_one({"_id": nid})
        return _from_doc(doc) if doc else None

    async def add(self, n: Notification) -> None:
        doc = _to_doc(n)
        doc["pending_events"] = to_embedded(n.pull_events())
        try:
            await self.col.insert_one(doc)
        except DuplicateKeyError:
            raise DomainError("DUPLICATE_NOTIFICATION",
                              "Notification already exists for this event + recipient", 409)

    async def save(self, n: Notification) -> None:
        expected = n.version
        n.version += 1
        doc = _to_doc(n)
        update = {"$set": {k: v for k, v in doc.items() if k != "_id"}}
        events = to_embedded(n.pull_events())
        if events:
            update["$push"] = {"pending_events": {"$each": events}}
        res = await self.col.update_one({"_id": n.id, "version": expected}, update)
        if res.matched_count == 0:
            raise DomainError("CONCURRENCY_CONFLICT", "Stale update detected", 409)

    # ---- preferences (INV-007) ----
    async def get_prefs(self, user_id: str) -> dict:
        doc = await self.db[PREFS_COLLECTION].find_one({"_id": user_id})
        if not doc:
            return {**DEFAULT_PREFS, "user_id": user_id}
        return {"user_id": user_id,
                "email_enabled": doc.get("email_enabled", True),
                "in_app_enabled": doc.get("in_app_enabled", True),
                "muted_types": doc.get("muted_types", [])}

    async def set_prefs(self, user_id: str, prefs: dict) -> dict:
        clean = {"email_enabled": bool(prefs.get("email_enabled", True)),
                 "in_app_enabled": bool(prefs.get("in_app_enabled", True)),
                 "muted_types": list(prefs.get("muted_types", []))}
        await self.db[PREFS_COLLECTION].update_one(
            {"_id": user_id}, {"$set": clean}, upsert=True)
        return {"user_id": user_id, **clean}


register_event_collection(COLLECTION)
