"""Listings API — /api/listings (thin controllers)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

from buildingblocks.deps import get_current_user, get_db

from .service import ListingService

router = APIRouter(prefix="/api/listings", tags=["listings"])


class ImageIn(BaseModel):
    url: str
    file_id: str | None = None


class CreateListingReq(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str = ""
    price_amount: int = Field(gt=0, description="Minor units, e.g. kopiykas")
    currency: str = "UAH"
    brand: str = ""
    category: str = ""
    gender: str = ""
    size: str = ""
    color: str = ""
    material: str = ""
    condition: str = ""
    season: str = ""
    style: str = ""
    images: list[ImageIn] = []
    allow_offers: bool = True


class PriceReq(BaseModel):
    amount: int = Field(gt=0)


@router.get("")
async def search(
    q: str | None = None, brand: str | None = None, category: str | None = None,
    gender: str | None = None, size: str | None = None, color: str | None = None,
    material: str | None = None, condition: str | None = None,
    min_price: int | None = None, max_price: int | None = None,
    sort: str = "newest", page: int = 1, page_size: int = 24,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await ListingService(db).search(locals())


@router.get("/mine")
async def mine(user: dict = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)):
    return {"items": await ListingService(db).my_listings(user["_id"])}


@router.get("/{id_or_slug}")
async def detail(id_or_slug: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    return {"listing": await ListingService(db).get_public(id_or_slug)}


@router.post("")
async def create(req: CreateListingReq, user: dict = Depends(get_current_user),
                 db: AsyncIOMotorDatabase = Depends(get_db)):
    listing = await ListingService(db).create_draft(user["_id"], req.model_dump())
    return {"listing_id": listing.id, "slug": listing.slug, "state": listing.state}


@router.post("/{listing_id}/publish")
async def publish(listing_id: str, user: dict = Depends(get_current_user),
                  db: AsyncIOMotorDatabase = Depends(get_db)):
    l = await ListingService(db).publish(listing_id, user["_id"])
    return {"listing_id": l.id, "slug": l.slug, "state": l.state}


@router.patch("/{listing_id}/price")
async def change_price(listing_id: str, req: PriceReq, user: dict = Depends(get_current_user),
                       db: AsyncIOMotorDatabase = Depends(get_db)):
    l = await ListingService(db).change_price(listing_id, user["_id"], req.amount)
    return {"listing_id": l.id, "state": l.state, "price": l.price.amount}


@router.delete("/{listing_id}")
async def archive(listing_id: str, user: dict = Depends(get_current_user),
                  db: AsyncIOMotorDatabase = Depends(get_db)):
    l = await ListingService(db).archive(listing_id, user["_id"])
    return {"listing_id": l.id, "state": l.state}
