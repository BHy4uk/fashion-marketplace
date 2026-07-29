"""Moderation Infrastructure — ModerationCaseRepository (Mongo).

Optimistic concurrency + embedded-events atomic outbox. Indexed to find the OPEN case
for a target (report merging, §9) and to power the moderator queue."""
from __future__ import annotations

from dataclasses import asdict

from motor.motor_asyncio import AsyncIOMotorDatabase

from buildingblocks.domain import DomainError
from buildingblocks.outbox import register_event_collection, to_embedded

from .domain import (CaseComment, Evidence, ModerationCase, ModerationDecision,
                     OPEN_STATES, Report)

COLLECTION = "moderation_cases"


def _to_doc(c: ModerationCase) -> dict:
    return {
        "_id": c.id, "target_type": c.target_type, "target_id": c.target_id,
        "target_context": c.target_context, "status": c.status, "priority": c.priority,
        "assigned_to": c.assigned_to,
        "reports": [asdict(r) for r in c.reports],
        "evidence": [asdict(e) for e in c.evidence],
        "decisions": [asdict(d) for d in c.decisions],
        "comments": [asdict(x) for x in c.comments],
        "audit": {"created_at": c.audit.created_at, "created_by": c.audit.created_by,
                  "updated_at": c.audit.updated_at, "updated_by": c.audit.updated_by},
        "version": c.version,
    }


def _from_doc(d: dict) -> ModerationCase:
    from buildingblocks.domain import AuditInfo
    a = d.get("audit", {})
    return ModerationCase(
        id=d["_id"], target_type=d["target_type"], target_id=d["target_id"],
        target_context=d.get("target_context", {}), status=d.get("status", "Created"),
        priority=d.get("priority", "normal"), assigned_to=d.get("assigned_to"),
        reports=[Report(**r) for r in d.get("reports", [])],
        evidence=[Evidence(**e) for e in d.get("evidence", [])],
        decisions=[ModerationDecision(**x) for x in d.get("decisions", [])],
        comments=[CaseComment(**x) for x in d.get("comments", [])],
        audit=AuditInfo(**a) if a else AuditInfo(), version=d.get("version", 0))


class ModerationCaseRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.col = db[COLLECTION]

    async def by_id(self, cid: str) -> ModerationCase | None:
        doc = await self.col.find_one({"_id": cid})
        return _from_doc(doc) if doc else None

    async def open_case_for(self, target_type: str, target_id: str) -> ModerationCase | None:
        doc = await self.col.find_one(
            {"target_type": target_type, "target_id": target_id,
             "status": {"$in": list(OPEN_STATES)}})
        return _from_doc(doc) if doc else None

    async def add(self, c: ModerationCase) -> None:
        doc = _to_doc(c)
        doc["pending_events"] = to_embedded(c.pull_events())
        await self.col.insert_one(doc)

    async def save(self, c: ModerationCase) -> None:
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
