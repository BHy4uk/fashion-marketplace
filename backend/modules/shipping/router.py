"""Shipping API — /api/shipments (read + seller dispatch + tracking + buyer confirm).

Shipments are created via events (OrderPaid), never via a public POST."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from buildingblocks.deps import get_current_user, get_db

from .service import ShippingService

router = APIRouter(prefix="/api/shipments", tags=["shipping"])


class DispatchReq(BaseModel):
    to_address: dict | None = None
    parcel: dict | None = None


@router.get("/order/{order_id}")
async def by_order(order_id: str, user: dict = Depends(get_current_user),
                   db: AsyncIOMotorDatabase = Depends(get_db)):
    return {"shipment": await ShippingService(db).get_for_order(order_id, user)}


@router.post("/{shipment_id}/dispatch")
async def dispatch(shipment_id: str, req: DispatchReq,
                   user: dict = Depends(get_current_user),
                   db: AsyncIOMotorDatabase = Depends(get_db)):
    s = await ShippingService(db).dispatch(shipment_id, user, req.to_address, req.parcel)
    return {"shipment_id": s.id, "status": s.status, "tracking_number": s.tracking_number,
            "carrier": s.carrier}


@router.post("/{shipment_id}/track")
async def track(shipment_id: str, user: dict = Depends(get_current_user),
                db: AsyncIOMotorDatabase = Depends(get_db)):
    return {"shipment": await ShippingService(db).track(shipment_id, user)}


@router.post("/{shipment_id}/confirm-delivery")
async def confirm_delivery(shipment_id: str, user: dict = Depends(get_current_user),
                           db: AsyncIOMotorDatabase = Depends(get_db)):
    s = await ShippingService(db).confirm_delivery(shipment_id, user)
    return {"shipment_id": s.id, "status": s.status}
