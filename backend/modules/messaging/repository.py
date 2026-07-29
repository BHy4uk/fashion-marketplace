"""Messaging Infrastructure — ConversationRepository (Mongo).

Optimistic concurrency + embedded-events atomic outbox. A unique index on dedup_key
enforces conversation uniqueness per (context, participant-set) — §9, §15, INV — with
deterministic failure under concurrency."""
from __future__ import annotations

from dataclasses import asdict

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from buildingblocks.domain import DomainError
from buildingblocks.outbox import register_event_collection, to_embedded

from .domain import Conversation, Message, ReadReceipt

COLLECTION = "conversations"


def _to_doc(c: Conversation) -> dict:
    return {
        "_id": c.id, "context_type": c.context_type, "context_id": c.context_id,
        "participants": c.participants, "dedup_key": c.dedup_key, "status": c.status,
        "messages": [asdict(m) for m in c.messages],
        "read_receipts": {uid: asdict(r) for uid, r in c.read_receipts.items()},
        "last_message_at": c.last_message_at,
        "audit": {"created_at": c.audit.created_at, "created_by": c.audit.created_by,
                  "updated_at": c.audit.updated_at, "updated_by": c.audit.updated_by},
        "version": c.version,
    }


def _from_doc(d: dict) -> Conversation:
    from buildingblocks.domain import AuditInfo
    a = d.get("audit", {})
    return Conversation(
        id=d["_id"], context_type=d["context_type"], context_id=d["context_id"],
        participants=d["participants"], dedup_key=d["dedup_key"],
        status=d.get("status", "Active"),
        messages=[Message(**m) for m in d.get("messages", [])],
        read_receipts={uid: ReadReceipt(**r) for uid, r in d.get("read_receipts", {}).items()},
        last_message_at=d.get("last_message_at"),
        audit=AuditInfo(**a) if a else AuditInfo(), version=d.get("version", 0))


class ConversationRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.col = db[COLLECTION]

    async def by_id(self, cid: str) -> Conversation | None:
        doc = await self.col.find_one({"_id": cid})
        return _from_doc(doc) if doc else None

    async def by_dedup_key(self, dedup_key: str) -> Conversation | None:
        doc = await self.col.find_one({"dedup_key": dedup_key})
        return _from_doc(doc) if doc else None

    async def add(self, c: Conversation) -> None:
        doc = _to_doc(c)
        doc["pending_events"] = to_embedded(c.pull_events())
        try:
            await self.col.insert_one(doc)
        except DuplicateKeyError:
            raise DomainError("DUPLICATE_CONVERSATION",
                              "A conversation already exists for this context", 409)

    async def save(self, c: Conversation) -> None:
        expected = c.version
        c.version += 1
        doc = _to_doc(c)
        update = {"$set": {k: v for k, v in doc.items() if k != "_id"}}
        events = to_embedded(c.pull_events())
        if events:
            update["$push"] = {"pending_events": {"$each": events}}
        res = await self.col.update_one({"_id": c.id, "version": expected}, update)
        if res.matched_count == 0:
            raise DomainError("CONCURRENCY_CONFLICT", "Stale update detected", 409)


register_event_collection(COLLECTION)
