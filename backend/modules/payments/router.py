"""Payments API — /api/payments (buyer checkout, provider webhook, read)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from buildingblocks.deps import get_current_user, get_db

from .service import PaymentService

router = APIRouter(prefix="/api/payments", tags=["payments"])


class CheckoutReq(BaseModel):
    order_id: str


@router.post("/checkout")
async def checkout(req: CheckoutReq, user: dict = Depends(get_current_user),
                   db: AsyncIOMotorDatabase = Depends(get_db)):
    return await PaymentService(db).checkout(req.order_id, user)


@router.post("/webhook/liqpay")
async def liqpay_webhook(request: Request, db: AsyncIOMotorDatabase = Depends(get_db)):
    form = await request.form()
    return await PaymentService(db).handle_webhook(form.get("data"), form.get("signature"))


@router.get("/order/{order_id}")
async def by_order(order_id: str, user: dict = Depends(get_current_user),
                   db: AsyncIOMotorDatabase = Depends(get_db)):
    return {"payment": await PaymentService(db).get_for_order(order_id, user)}
