"""Moderation Application — report intake (with merging + dedup), investigation
workflow, and decision recording with ENFORCEMENT delegated to owning modules.

Moderation references marketplace entities but never owns them (INV-007): enforcement
of a decision is performed by calling the owning module's service (Listings/Reviews/
Messaging/Identity). Reads context via contracts only."""
from __future__ import annotations

import logging

from motor.motor_asyncio import AsyncIOMotorDatabase

from buildingblocks.domain import DomainError
from modules.identity.contracts import IdentityContract

from .domain import (CaseComment, Evidence, ModerationCase, ModerationDecision, Report)
from .repository import COLLECTION, ModerationCaseRepository

log = logging.getLogger("moderation")

# Decision action -> (owning enforcement). Actions with no entry are advisory (NoAction/Warning).
_ENFORCED = {"ListingHidden", "ListingRemoved", "MessageHidden", "ReviewHidden",
             "ReviewRemoved", "TemporarySuspension", "PermanentSuspension"}


class ModerationService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.repo = ModerationCaseRepository(db)
        self.identity = IdentityContract(db)

    # ---- report intake (§9 merge, §15 dedup) ----
    async def submit_report(self, reporter: dict, target_type: str, target_id: str,
                            reason: str, note: str | None = None,
                            target_context: dict | None = None) -> ModerationCase:
        if not reason or not reason.strip():
            raise DomainError("INVALID_REPORT", "A report reason is required", 422)
        report = Report(reporter_id=reporter["_id"], reason=reason.strip(), note=(note or None))
        existing = await self.repo.open_case_for(target_type, target_id)
        if existing:
            if any(r.reporter_id == reporter["_id"] for r in existing.reports):
                raise DomainError("DUPLICATE_REPORT",
                                  "You have already reported this item", 409)  # §15/§16
            existing.add_report(report)
            await self.repo.save(existing)
            return existing
        case = ModerationCase.open(target_type=target_type, target_id=target_id,
                                   target_context=target_context or {}, report=report)
        await self.repo.add(case)
        return case

    # ---- investigation (moderator/admin) ----
    async def assign(self, case_id: str, moderator: dict) -> ModerationCase:
        case = await self._load(case_id)
        case.assign(moderator["_id"])
        await self.repo.save(case)
        return case

    async def investigate(self, case_id: str, moderator: dict) -> ModerationCase:
        case = await self._load(case_id)
        case.start_investigation(moderator["_id"])
        await self.repo.save(case)
        return case

    async def add_evidence(self, case_id: str, moderator: dict, kind: str, ref: str,
                           note: str | None = None) -> ModerationCase:
        case = await self._load(case_id)
        case.add_evidence(Evidence(kind=kind, ref=ref, note=note, added_by=moderator["_id"]))
        await self.repo.save(case)
        return case

    async def comment(self, case_id: str, moderator: dict, text: str) -> ModerationCase:
        if not text or not text.strip():
            raise DomainError("INVALID_COMMENT", "Comment text is required", 422)
        case = await self._load(case_id)
        case.add_comment(CaseComment(author_id=moderator["_id"], text=text.strip()))
        await self.repo.save(case)
        return case

    # ---- decision + enforcement (§11) ----
    async def record_decision(self, case_id: str, moderator: dict, action: str,
                              reason: str, policy_ref: str | None = None) -> ModerationCase:
        if not reason or not reason.strip():
            raise DomainError("INVALID_DECISION", "A decision reason is required", 422)
        case = await self._load(case_id)
        # enforce BEFORE recording so a failed enforcement aborts cleanly (INV-005 stays clean)
        if action in _ENFORCED:
            await self._enforce(case, action, moderator, reason)
        case.record_decision(ModerationDecision(
            action=action, reason=reason.strip(), moderator_id=moderator["_id"],
            policy_ref=policy_ref))
        await self.repo.save(case)
        return case

    async def _enforce(self, case: ModerationCase, action: str, moderator: dict,
                       reason: str) -> None:
        tid = case.target_id
        if action in ("ReviewHidden", "ReviewRemoved"):
            from modules.reviews.service import ReviewService
            svc = ReviewService(self.db)
            await (svc.remove(tid, moderator) if action == "ReviewRemoved" else svc.hide(tid, moderator))
        elif action == "MessageHidden":
            from modules.messaging.service import MessagingService
            conv = case.target_context.get("conversation_id")
            if not conv:
                raise DomainError("EVIDENCE_MISSING", "conversation_id required to hide a message", 422)
            await MessagingService(self.db).hide_message(conv, tid, moderator)
        elif action in ("ListingHidden", "ListingRemoved"):
            from modules.listings.service import ListingService
            await ListingService(self.db).moderate_takedown(tid, remove=(action == "ListingRemoved"))
        elif action in ("TemporarySuspension", "PermanentSuspension"):
            from modules.identity.service import IdentityService
            await IdentityService(self.db).suspend(tid, reason=f"moderation:{action}")

    async def close(self, case_id: str, moderator: dict) -> ModerationCase:
        case = await self._load(case_id)
        case.close(moderator["_id"])
        await self.repo.save(case)
        return case

    async def dismiss(self, case_id: str, moderator: dict, reason: str = "no_violation") -> ModerationCase:
        case = await self._load(case_id)
        case.dismiss(moderator["_id"], reason)
        await self.repo.save(case)
        return case

    # ---- queries (moderator/admin) ----
    async def list_cases(self, status: str | None = None, limit: int = 100) -> list[dict]:
        q = {} if not status else {"status": status}
        cur = self.db[COLLECTION].find(q).sort([("priority", -1), ("audit.updated_at", -1)]).limit(limit)
        return [self._summary(d) async for d in cur]

    async def get_case(self, case_id: str) -> dict:
        case = await self._load(case_id)
        return await self._detail(case)

    async def stats(self) -> dict:
        col = self.db[COLLECTION]
        out = {}
        for s in ("Created", "UnderReview", "Investigation", "DecisionMade", "Closed", "Dismissed"):
            out[s] = await col.count_documents({"status": s})
        out["open"] = out["Created"] + out["UnderReview"] + out["Investigation"] + out["DecisionMade"]
        return out

    # ---- helpers ----
    async def _load(self, case_id: str) -> ModerationCase:
        c = await self.repo.by_id(case_id)
        if not c:
            raise DomainError("MODERATION_CASE_NOT_FOUND", "Case not found", 404)
        return c

    def _summary(self, d: dict) -> dict:
        return {"id": d["_id"], "target_type": d["target_type"], "target_id": d["target_id"],
                "status": d["status"], "priority": d.get("priority", "normal"),
                "reports": len(d.get("reports", [])),
                "decisions": len(d.get("decisions", [])),
                "assigned_to": d.get("assigned_to"),
                "updated_at": d.get("audit", {}).get("updated_at"),
                "created_at": d.get("audit", {}).get("created_at")}

    async def _detail(self, c: ModerationCase) -> dict:
        async def name(uid):
            s = await self.identity.summary(uid)
            return (s or {}).get("display_name") if s else None
        return {
            "id": c.id, "target_type": c.target_type, "target_id": c.target_id,
            "target_context": c.target_context, "status": c.status,
            "priority": c.priority, "assigned_to": c.assigned_to,
            "reports": [{"report_id": r.report_id, "reporter_id": r.reporter_id,
                         "reporter_name": await name(r.reporter_id), "reason": r.reason,
                         "note": r.note, "created_at": r.created_at} for r in c.reports],
            "evidence": [{"evidence_id": e.evidence_id, "kind": e.kind, "ref": e.ref,
                          "note": e.note, "created_at": e.created_at} for e in c.evidence],
            "decisions": [{"decision_id": d.decision_id, "action": d.action, "reason": d.reason,
                           "moderator_id": d.moderator_id, "policy_ref": d.policy_ref,
                           "created_at": d.created_at} for d in c.decisions],
            "comments": [{"comment_id": x.comment_id, "author_id": x.author_id,
                          "author_name": await name(x.author_id), "text": x.text,
                          "created_at": x.created_at} for x in c.comments],
            "created_at": c.audit.created_at, "updated_at": c.audit.updated_at,
        }
