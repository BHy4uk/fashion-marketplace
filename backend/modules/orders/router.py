"""Orders API — /api/orders (read + buyer cancel). Orders are created via events,
never via a public POST (they originate from an accepted Offer, §7)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from buildingblocks.deps import get_current_user, get_db

from .service import OrderService

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.get("")
async def my_orders(box: str = Query("buyer", pattern="^(buyer|seller)$"),
                    user: dict = Depends(get_current_user),
                    db: AsyncIOMotorDatabase = Depends(get_db)):
    return {"items": await OrderService(db).list_for_user(user["_id"], box)}


@router.get("/{order_id}")
async def detail(order_id: str, user: dict = Depends(get_current_user),
                 db: AsyncIOMotorDatabase = Depends(get_db)):
    return {"order": await OrderService(db).get(order_id, user)}


@router.post("/{order_id}/cancel")
async def cancel(order_id: str, user: dict = Depends(get_current_user),
                 db: AsyncIOMotorDatabase = Depends(get_db)):
    order = await OrderService(db).cancel(order_id, user)
    return {"order_id": order.id, "status": order.status}
