"""Administration API — platform-owned taxonomy (Q11) + feature flags read.

Taxonomy (categories, brands, sizes, conditions) is seeded by the platform and
managed here. Other modules read it; they never own it (DOMAIN-012)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from buildingblocks.deps import get_db

router = APIRouter(prefix="/api/taxonomy", tags=["taxonomy"])


@router.get("/categories")
async def categories(db: AsyncIOMotorDatabase = Depends(get_db)):
    docs = await db.admin_categories.find().sort("order", 1).to_list(200)
    return {"categories": [{"slug": d["_id"], "name": d["name"],
                            "gender": d.get("gender", [])} for d in docs]}


@router.get("/brands")
async def brands(q: str | None = None, db: AsyncIOMotorDatabase = Depends(get_db)):
    query = {"name": {"$regex": q, "$options": "i"}} if q else {}
    docs = await db.admin_brands.find(query).sort("name", 1).to_list(500)
    return {"brands": [d["name"] for d in docs]}


@router.get("/meta")
async def meta():
    return {
        "conditions": [
            {"value": "BRAND_NEW", "label": "Brand New"},
            {"value": "LIKE_NEW", "label": "Like New"},
            {"value": "GENTLY_USED", "label": "Gently Used"},
            {"value": "USED", "label": "Used"},
            {"value": "WELL_WORN", "label": "Well Worn"},
        ],
        "genders": ["Men", "Women", "Unisex"],
        "currencies": ["UAH", "EUR", "USD"],
        "sizes": ["XXS", "XS", "S", "M", "L", "XL", "XXL",
                  "36", "37", "38", "39", "40", "41", "42", "43", "44", "45"],
    }
