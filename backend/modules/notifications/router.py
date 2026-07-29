"""Notifications API — /api/notifications (list, unread count, read, preferences)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from buildingblocks.deps import get_current_user, get_db

from .service import NotificationService

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class PrefsReq(BaseModel):
    email_enabled: bool = True
    in_app_enabled: bool = True
    muted_types: list[str] = []


@router.get("")
async def my_notifications(user: dict = Depends(get_current_user),
                           db: AsyncIOMotorDatabase = Depends(get_db)):
    return {"items": await NotificationService(db).list_for_user(user["_id"])}


@router.get("/unread-count")
async def unread_count(user: dict = Depends(get_current_user),
                       db: AsyncIOMotorDatabase = Depends(get_db)):
    return {"count": await NotificationService(db).unread_count(user["_id"])}


@router.post("/{notification_id}/read")
async def read(notification_id: str, user: dict = Depends(get_current_user),
               db: AsyncIOMotorDatabase = Depends(get_db)):
    await NotificationService(db).mark_read(notification_id, user)
    return {"ok": True}


@router.post("/read-all")
async def read_all(user: dict = Depends(get_current_user),
                   db: AsyncIOMotorDatabase = Depends(get_db)):
    n = await NotificationService(db).mark_all_read(user["_id"])
    return {"marked": n}


@router.get("/preferences")
async def get_prefs(user: dict = Depends(get_current_user),
                    db: AsyncIOMotorDatabase = Depends(get_db)):
    return await NotificationService(db).get_prefs(user["_id"])


@router.put("/preferences")
async def set_prefs(req: PrefsReq, user: dict = Depends(get_current_user),
                    db: AsyncIOMotorDatabase = Depends(get_db)):
    return await NotificationService(db).set_prefs(user["_id"], req.model_dump())
