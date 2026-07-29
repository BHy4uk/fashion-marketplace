"""Moderation API — /api/moderation.

Report submission is open to any authenticated user. All Case inspection and actions
are restricted to moderators/admins (§13, §20 — moderation data is confidential)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

from buildingblocks.deps import get_current_user, get_db, require_roles

from .service import ModerationService

router = APIRouter(prefix="/api/moderation", tags=["moderation"])
_staff = require_roles("moderator", "admin")


class ReportReq(BaseModel):
    target_type: str = Field(pattern="^(listing|review|message|user)$")
    target_id: str
    reason: str = Field(min_length=1, max_length=500)
    note: str | None = Field(default=None, max_length=2000)
    target_context: dict | None = None


class EvidenceReq(BaseModel):
    kind: str
    ref: str
    note: str | None = None


class CommentReq(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class DecisionReq(BaseModel):
    action: str
    reason: str = Field(min_length=1, max_length=1000)
    policy_ref: str | None = None


class DismissReq(BaseModel):
    reason: str | None = "no_violation"


# ---- reporter (any authenticated user) ----
@router.post("/reports")
async def submit_report(req: ReportReq, user: dict = Depends(get_current_user),
                        db: AsyncIOMotorDatabase = Depends(get_db)):
    c = await ModerationService(db).submit_report(
        user, req.target_type, req.target_id, req.reason, req.note, req.target_context)
    return {"case_id": c.id, "status": c.status}


# ---- moderator / admin ----
@router.get("/cases")
async def list_cases(status: str | None = None, user: dict = Depends(_staff),
                     db: AsyncIOMotorDatabase = Depends(get_db)):
    return {"items": await ModerationService(db).list_cases(status)}


@router.get("/stats")
async def stats(user: dict = Depends(_staff), db: AsyncIOMotorDatabase = Depends(get_db)):
    return await ModerationService(db).stats()


@router.get("/cases/{case_id}")
async def get_case(case_id: str, user: dict = Depends(_staff),
                   db: AsyncIOMotorDatabase = Depends(get_db)):
    return await ModerationService(db).get_case(case_id)


@router.post("/cases/{case_id}/assign")
async def assign(case_id: str, user: dict = Depends(_staff),
                 db: AsyncIOMotorDatabase = Depends(get_db)):
    c = await ModerationService(db).assign(case_id, user)
    return {"id": c.id, "status": c.status, "assigned_to": c.assigned_to}


@router.post("/cases/{case_id}/investigate")
async def investigate(case_id: str, user: dict = Depends(_staff),
                      db: AsyncIOMotorDatabase = Depends(get_db)):
    c = await ModerationService(db).investigate(case_id, user)
    return {"id": c.id, "status": c.status}


@router.post("/cases/{case_id}/evidence")
async def add_evidence(case_id: str, req: EvidenceReq, user: dict = Depends(_staff),
                       db: AsyncIOMotorDatabase = Depends(get_db)):
    c = await ModerationService(db).add_evidence(case_id, user, req.kind, req.ref, req.note)
    return {"id": c.id, "evidence": len(c.evidence)}


@router.post("/cases/{case_id}/comment")
async def comment(case_id: str, req: CommentReq, user: dict = Depends(_staff),
                  db: AsyncIOMotorDatabase = Depends(get_db)):
    c = await ModerationService(db).comment(case_id, user, req.text)
    return {"id": c.id, "comments": len(c.comments)}


@router.post("/cases/{case_id}/decision")
async def record_decision(case_id: str, req: DecisionReq, user: dict = Depends(_staff),
                          db: AsyncIOMotorDatabase = Depends(get_db)):
    c = await ModerationService(db).record_decision(case_id, user, req.action, req.reason, req.policy_ref)
    return {"id": c.id, "status": c.status, "decisions": len(c.decisions)}


@router.post("/cases/{case_id}/close")
async def close(case_id: str, user: dict = Depends(_staff),
                db: AsyncIOMotorDatabase = Depends(get_db)):
    c = await ModerationService(db).close(case_id, user)
    return {"id": c.id, "status": c.status}


@router.post("/cases/{case_id}/dismiss")
async def dismiss(case_id: str, req: DismissReq, user: dict = Depends(_staff),
                  db: AsyncIOMotorDatabase = Depends(get_db)):
    c = await ModerationService(db).dismiss(case_id, user, req.reason or "no_violation")
    return {"id": c.id, "status": c.status}
