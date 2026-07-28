"""Reviews API — /api/reviews.

Create (participant, on completed order), read (public per-user; participant per-order),
recipient response, and moderator/admin moderation (hide/unhide/remove)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

from buildingblocks.deps import get_current_user, get_db, require_roles

from .service import ReviewService

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


class CreateReviewReq(BaseModel):
    order_id: str
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)


class ResponseReq(BaseModel):
    comment: str = Field(min_length=1, max_length=2000)


@router.post("")
async def create_review(req: CreateReviewReq, user: dict = Depends(get_current_user),
                        db: AsyncIOMotorDatabase = Depends(get_db)):
    r = await ReviewService(db).create(req.order_id, user, req.rating, req.comment)
    return {"review_id": r.id, "status": r.status, "recipient_id": r.recipient_id}


@router.get("/eligibility/{order_id}")
async def eligibility(order_id: str, user: dict = Depends(get_current_user),
                      db: AsyncIOMotorDatabase = Depends(get_db)):
    return await ReviewService(db).eligibility(order_id, user)


@router.get("/user/{user_id}")
async def by_user(user_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    return await ReviewService(db).for_user(user_id)


@router.get("/order/{order_id}")
async def by_order(order_id: str, user: dict = Depends(get_current_user),
                   db: AsyncIOMotorDatabase = Depends(get_db)):
    return {"items": await ReviewService(db).for_order(order_id, user)}


@router.post("/{review_id}/response")
async def respond(review_id: str, req: ResponseReq,
                  user: dict = Depends(get_current_user),
                  db: AsyncIOMotorDatabase = Depends(get_db)):
    r = await ReviewService(db).respond(review_id, user, req.comment)
    return {"review_id": r.id, "has_response": r.response is not None}


@router.post("/{review_id}/hide")
async def hide(review_id: str, user: dict = Depends(require_roles("moderator", "admin")),
               db: AsyncIOMotorDatabase = Depends(get_db)):
    r = await ReviewService(db).hide(review_id, user)
    return {"review_id": r.id, "status": r.status}


@router.post("/{review_id}/unhide")
async def unhide(review_id: str, user: dict = Depends(require_roles("moderator", "admin")),
                 db: AsyncIOMotorDatabase = Depends(get_db)):
    r = await ReviewService(db).unhide(review_id, user)
    return {"review_id": r.id, "status": r.status}


@router.post("/{review_id}/remove")
async def remove(review_id: str, user: dict = Depends(require_roles("moderator", "admin")),
                 db: AsyncIOMotorDatabase = Depends(get_db)):
    r = await ReviewService(db).remove(review_id, user)
    return {"review_id": r.id, "status": r.status}
