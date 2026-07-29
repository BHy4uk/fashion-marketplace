"""Analytics API — /api/analytics (seller self-service + marketplace staff view)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from buildingblocks.deps import get_current_user, get_db, require_roles

from .service import AnalyticsService

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/seller")
async def seller_analytics(user: dict = Depends(get_current_user),
                           db: AsyncIOMotorDatabase = Depends(get_db)):
    return await AnalyticsService(db).seller_overview(user["_id"])


@router.get("/marketplace")
async def marketplace_analytics(_: dict = Depends(require_roles("admin", "moderator")),
                                db: AsyncIOMotorDatabase = Depends(get_db)):
    return await AnalyticsService(db).marketplace_overview()
