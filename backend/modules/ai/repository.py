"""AI Infrastructure — AIJobRepository (Mongo) + embedded atomic outbox."""
from __future__ import annotations

from dataclasses import asdict

from motor.motor_asyncio import AsyncIOMotorDatabase

from buildingblocks.domain import DomainError
from buildingblocks.outbox import register_event_collection, to_embedded

from .domain import AIAnalysis, AIExecution, AIJob, AIRecommendation

COLLECTION = "ai_jobs"


def _to_doc(j: AIJob) -> dict:
    return {"_id": j.id, "objective": j.objective, "subject_type": j.subject_type,
            "subject_id": j.subject_id, "status": j.status,
            "executions": [asdict(e) for e in j.executions],
            "analyses": [asdict(a) for a in j.analyses],
            "recommendations": [asdict(r) for r in j.recommendations],
            "audit": {"created_at": j.audit.created_at, "created_by": j.audit.created_by,
                      "updated_at": j.audit.updated_at, "updated_by": j.audit.updated_by},
            "version": j.version}


def _from_doc(d: dict) -> AIJob:
    from buildingblocks.domain import AuditInfo
    a = d.get("audit", {})
    return AIJob(id=d["_id"], objective=d["objective"], subject_type=d["subject_type"],
                 subject_id=d["subject_id"], status=d.get("status", "Created"),
                 executions=[AIExecution(**e) for e in d.get("executions", [])],
                 analyses=[AIAnalysis(**x) for x in d.get("analyses", [])],
                 recommendations=[AIRecommendation(**x) for x in d.get("recommendations", [])],
                 audit=AuditInfo(**a) if a else AuditInfo(), version=d.get("version", 0))


class AIJobRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.col = db[COLLECTION]

    async def by_id(self, jid: str) -> AIJob | None:
        d = await self.col.find_one({"_id": jid})
        return _from_doc(d) if d else None

    async def add(self, j: AIJob) -> None:
        doc = _to_doc(j)
        doc["pending_events"] = to_embedded(j.pull_events())
        await self.col.insert_one(doc)

    async def save(self, j: AIJob) -> None:
        expected = j.version
        j.version += 1
        doc = _to_doc(j)
        update = {"$set": {k: v for k, v in doc.items() if k != "_id"}}
        events = to_embedded(j.pull_events())
        if events:
            update["$push"] = {"pending_events": {"$each": events}}
        res = await self.col.update_one({"_id": j.id, "version": expected}, update)
        if res.matched_count == 0:
            raise DomainError("CONCURRENCY_CONFLICT", "Stale update detected", 409)

    async def latest(self, objective: str, subject_id: str) -> AIJob | None:
        d = await self.col.find_one(
            {"objective": objective, "subject_id": subject_id, "status": "Completed"},
            sort=[("audit.created_at", -1)])
        return _from_doc(d) if d else None


register_event_collection(COLLECTION)
