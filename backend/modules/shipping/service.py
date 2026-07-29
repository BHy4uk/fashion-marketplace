"""Shipping Application — create-from-event, seller dispatch, tracking refresh,
buyer delivery confirmation, and a background tracking sweeper.

Reads Orders ONLY via OrderContract (no cross-module DB access). Carrier calls go
exclusively through IShippingProvider. Shipping NEVER mutates Orders — it emits
domain events (ShipmentCreated/Dispatched/Delivered/...) that Orders reacts to.
"""
from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorDatabase

from buildingblocks.domain import DomainError
from modules.orders.contracts import OrderContract

from .domain import Shipment
from .provider import build_provider
from .repository import ShipmentRepository


class ShippingService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.repo = ShipmentRepository(db)
        self.orders = OrderContract(db)
        self.provider = build_provider()

    # ---- event-driven creation (reacts to OrderPaid; idempotent) ----
    async def create_for_order(self, order_id: str) -> Shipment | None:
        existing = await self.repo.by_order(order_id)
        if existing:
            return existing
        snap = await self.orders.snapshot(order_id)
        if not snap:
            return None
        shipment = Shipment.create(
            order_id=order_id, buyer_id=snap.buyer_id, seller_id=snap.seller_id,
            listing_id=snap.listing_id, carrier=self.provider.name)
        try:
            await self.repo.add(shipment)
        except DomainError:
            return await self.repo.by_order(order_id)
        return shipment

    # ---- seller dispatch (registers a waybill with the carrier, then dispatches) ----
    async def dispatch(self, shipment_id: str, user: dict,
                       to_address: dict | None = None, parcel: dict | None = None) -> Shipment:
        shipment = await self._load(shipment_id)
        if user["_id"] != shipment.seller_id and user.get("role") != "admin":
            raise DomainError("UNAUTHORIZED_ACCESS", "Only the seller may dispatch", 403)
        if shipment.status != "Pending":
            raise DomainError("SHIPMENT_NOT_DISPATCHABLE",
                              f"A {shipment.status} shipment cannot be dispatched", 409)
        if to_address:
            shipment.to_address = to_address
        if parcel:
            shipment.parcel = parcel
        result = await self.provider.create_shipment(
            order_id=shipment.order_id, to_address=shipment.to_address,
            from_address=shipment.from_address, parcel=shipment.parcel,
            description=f"ARCHIVE order {shipment.order_id}")
        shipment.assign_label(
            tracking_number=result["tracking_number"], label_url=result.get("label_url"),
            carrier_ref=result.get("carrier_ref"),
            estimated_delivery=result.get("estimated_delivery"))
        shipment.dispatch()
        await self.repo.save(shipment)
        return shipment

    # ---- tracking refresh from carrier (advances state; returns True if changed) ----
    async def refresh_tracking(self, shipment: Shipment) -> bool:
        if shipment.status not in ("Dispatched", "InTransit") or not shipment.tracking_number:
            return False
        t = await self.provider.get_tracking(
            tracking_number=shipment.tracking_number, carrier_ref=shipment.carrier_ref,
            phone=(shipment.to_address or {}).get("phone"))
        status = t.get("status")
        changed = False
        if status == "in_transit":
            changed = shipment.mark_in_transit(t.get("description"), t.get("location"),
                                                t.get("carrier_code"))
        elif status == "delivered":
            shipment.mark_delivered(t.get("description"), t.get("location"), t.get("carrier_code"))
            changed = True
        elif status == "returned":
            shipment.mark_returned(t.get("description") or "returned")
            changed = True
        if changed:
            await self.repo.save(shipment)
        return changed

    async def track(self, shipment_id: str, user: dict) -> dict:
        shipment = await self._load_participant(shipment_id, user)
        await self.refresh_tracking(shipment)
        return self._view(shipment)

    # ---- buyer confirms receipt (the delivery trigger that closes the escrow loop) ----
    async def confirm_delivery(self, shipment_id: str, user: dict) -> Shipment:
        shipment = await self._load(shipment_id)
        if user["_id"] != shipment.buyer_id and user.get("role") != "admin":
            raise DomainError("UNAUTHORIZED_ACCESS", "Only the buyer may confirm delivery", 403)
        shipment.mark_delivered(description="Delivery confirmed by buyer")
        await self.repo.save(shipment)
        return shipment

    # ---- background sweeper: poll carrier tracking for in-flight shipments ----
    async def sweep_tracking(self) -> int:
        count = 0
        cur = self.db.shipments.find({"status": {"$in": ["Dispatched", "InTransit"]}})
        async for d in cur:
            shipment = await self.repo.by_id(d["_id"])
            if not shipment:
                continue
            try:
                if await self.refresh_tracking(shipment):
                    count += 1
            except Exception:  # noqa: BLE001 - a carrier hiccup must not stall the sweep
                pass
        return count

    # ---- reads ----
    async def get_for_order(self, order_id: str, user: dict) -> dict | None:
        snap = await self.orders.snapshot(order_id)
        if not snap:
            raise DomainError("ORDER_NOT_FOUND", "Order not found", 404)
        if user.get("role") not in ("admin", "moderator") and \
           user["_id"] not in (snap.buyer_id, snap.seller_id):
            raise DomainError("UNAUTHORIZED_ACCESS", "Not a participant", 403)
        shipment = await self.repo.by_order(order_id)
        return self._view(shipment) if shipment else None

    # ---- helpers ----
    async def _load(self, shipment_id: str) -> Shipment:
        s = await self.repo.by_id(shipment_id)
        if not s:
            raise DomainError("SHIPMENT_NOT_FOUND", "Shipment not found", 404)
        return s

    async def _load_participant(self, shipment_id: str, user: dict) -> Shipment:
        s = await self._load(shipment_id)
        if user.get("role") not in ("admin", "moderator") and \
           user["_id"] not in (s.buyer_id, s.seller_id):
            raise DomainError("UNAUTHORIZED_ACCESS", "Not a participant", 403)
        return s

    def _view(self, s: Shipment) -> dict:
        return {"id": s.id, "order_id": s.order_id, "carrier": s.carrier,
                "status": s.status, "tracking_number": s.tracking_number,
                "label_url": s.label_url, "carrier_ref": s.carrier_ref,
                "estimated_delivery": s.estimated_delivery,
                "buyer_id": s.buyer_id, "seller_id": s.seller_id,
                "tracking_events": [{"status": e.status, "description": e.description,
                                     "location": e.location, "at": e.at}
                                    for e in s.tracking_events]}
