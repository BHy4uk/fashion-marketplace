"""Offers API — /api/offers (thin controllers, authz delegated to domain/service)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

from buildingblocks.deps import get_current_user, get_db

from .service import OfferService

router = APIRouter(prefix="/api/offers", tags=["offers"])


class CreateOfferReq(BaseModel):
    listing_id: str
    amount: int = Field(gt=0, description="Minor units, matches listing currency")


class AmountReq(BaseModel):
    amount: int = Field(gt=0)


def _out(offer):
    return {"offer_id": offer.id, "status": offer.status, "awaiting": offer.awaiting,
            "current_amount": offer.current_amount, "listing_id": offer.listing_id}


@router.post("")
async def create(req: CreateOfferReq, user: dict = Depends(get_current_user),
                 db: AsyncIOMotorDatabase = Depends(get_db)):
    offer = await OfferService(db).create(user["_id"], req.listing_id, req.amount)
    return _out(offer)


@router.get("")
async def my_offers(box: str = Query("buyer", pattern="^(buyer|seller)$"),
                    user: dict = Depends(get_current_user),
                    db: AsyncIOMotorDatabase = Depends(get_db)):
    return {"items": await OfferService(db).list_for_user(user["_id"], box)}


@router.get("/listing/{listing_id}")
async def listing_offers(listing_id: str, user: dict = Depends(get_current_user),
                         db: AsyncIOMotorDatabase = Depends(get_db)):
    return {"items": await OfferService(db).list_for_listing(listing_id, user["_id"])}


@router.get("/{offer_id}")
async def detail(offer_id: str, user: dict = Depends(get_current_user),
                 db: AsyncIOMotorDatabase = Depends(get_db)):
    return {"offer": await OfferService(db).get(offer_id, user["_id"])}


@router.post("/{offer_id}/counter")
async def counter(offer_id: str, req: AmountReq, user: dict = Depends(get_current_user),
                  db: AsyncIOMotorDatabase = Depends(get_db)):
    return _out(await OfferService(db).counter(offer_id, user["_id"], req.amount))


@router.post("/{offer_id}/accept")
async def accept(offer_id: str, user: dict = Depends(get_current_user),
                 db: AsyncIOMotorDatabase = Depends(get_db)):
    return _out(await OfferService(db).accept(offer_id, user["_id"]))


@router.post("/{offer_id}/reject")
async def reject(offer_id: str, user: dict = Depends(get_current_user),
                 db: AsyncIOMotorDatabase = Depends(get_db)):
    return _out(await OfferService(db).reject(offer_id, user["_id"]))


@router.post("/{offer_id}/cancel")
async def cancel(offer_id: str, user: dict = Depends(get_current_user),
                 db: AsyncIOMotorDatabase = Depends(get_db)):
    return _out(await OfferService(db).cancel(offer_id, user["_id"]))
