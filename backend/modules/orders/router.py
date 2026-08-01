"""Orders API — /api/orders (read + buyer cancel). Orders are created via events,
never via a public POST (they originate from an accepted Offer, §7).
Exception: Buy Now flow creates an order directly from a listing."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from buildingblocks.deps import get_current_user, get_db

from .service import OrderService

router = APIRouter(prefix="/api/orders", tags=["orders"])


class BuyNowReq(BaseModel):
    listing_id: str


@router.post("/buy-now")
async def buy_now(req: BuyNowReq, user: dict = Depends(get_current_user),
                  db: AsyncIOMotorDatabase = Depends(get_db)):
    order = await OrderService(db).buy_now(req.listing_id, user)
    return {"order_id": order.id, "order_number": order.order_number,
            "total": order.total, "currency": order.currency, "status": order.status}


@router.get("")
async def my_orders(box: str = Query("buyer", pattern="^(buyer|seller)$"),
                    user: dict = Depends(get_current_user),
                    db: AsyncIOMotorDatabase = Depends(get_db)):
    return {"items": await OrderService(db).list_for_user(user["_id"], box)}


@router.get("/counts")
async def counts(user: dict = Depends(get_current_user),
                 db: AsyncIOMotorDatabase = Depends(get_db)):
    uid = user["_id"]
    buyer = await db.orders.count_documents({"buyer_id": uid, "status": "AwaitingPayment"})
    seller = await db.orders.count_documents(
        {"seller_id": uid, "status": {"$in": ["Paid", "PreparingShipment"]}})
    return {"buyer": buyer, "seller": seller}


@router.get("/{order_id}")
async def detail(order_id: str, user: dict = Depends(get_current_user),
                 db: AsyncIOMotorDatabase = Depends(get_db)):
    return {"order": await OrderService(db).get(order_id, user)}


@router.post("/{order_id}/cancel")
async def cancel(order_id: str, user: dict = Depends(get_current_user),
                 db: AsyncIOMotorDatabase = Depends(get_db)):
    order = await OrderService(db).cancel(order_id, user)
    return {"order_id": order.id, "status": order.status}
