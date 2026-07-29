"""AI API — advisory enrichment + fraud signals for listings.

- GET  /api/ai/listings/{id}          latest enrichment (owner or staff)
- POST /api/ai/listings/{id}/enrich   (re)run enrichment now (owner or staff)
- GET  /api/ai/listings/{id}/fraud    latest fraud signal (moderator/admin only)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from buildingblocks.deps import get_current_user, get_db, require_roles
from modules.listings.contracts import ListingContract

from .service import AIService

router = APIRouter(prefix="/api/ai", tags=["ai"])

_STAFF = {"admin", "moderator"}


async def _assert_owner_or_staff(db: AsyncIOMotorDatabase, listing_id: str, user: dict) -> None:
    if user.get("role") in _STAFF:
        return
    detail = await ListingContract(db).detail(listing_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Listing not found")
    if detail.get("seller_id") != user["_id"]:
        raise HTTPException(status_code=403, detail="Only the seller or staff may view AI insights")


@router.get("/listings/{listing_id}")
async def get_enrichment(listing_id: str, user: dict = Depends(get_current_user),
                         db: AsyncIOMotorDatabase = Depends(get_db)):
    await _assert_owner_or_staff(db, listing_id, user)
    return {"enrichment": await AIService(db).latest_enrichment(listing_id)}


@router.post("/listings/{listing_id}/enrich")
async def run_enrichment(listing_id: str, user: dict = Depends(get_current_user),
                         db: AsyncIOMotorDatabase = Depends(get_db)):
    await _assert_owner_or_staff(db, listing_id, user)
    svc = AIService(db)
    job = await svc.enrich_listing(listing_id)
    return {"enrichment": svc._job_view(job)}


@router.get("/listings/{listing_id}/fraud")
async def get_fraud(listing_id: str, _: dict = Depends(require_roles("admin", "moderator")),
                    db: AsyncIOMotorDatabase = Depends(get_db)):
    return {"fraud": await AIService(db).latest_fraud(listing_id)}
