"""Orders Application — create-from-event (idempotent, atomic) + queries + cancel.

Reads other domains ONLY through their contracts. Order creation is triggered by
the OfferAccepted domain event (event-driven; Orders and Offers stay decoupled).
"""
from __future__ import annotations

import os

from motor.motor_asyncio import AsyncIOMotorDatabase

from buildingblocks.domain import DomainError
from modules.identity.contracts import IdentityContract
from modules.listings.contracts import ListingContract

from .domain import Order
from .repository import OrderRepository


def _fee_percent() -> int:
    return int(os.environ.get("PLATFORM_FEE_PERCENT", "10"))  # seller-paid %, per-country (Q4)


class OrderService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.repo = OrderRepository(db)
        self.listings = ListingContract(db)
        self.identity = IdentityContract(db)

    # ---- event-driven creation (§7, idempotent for at-least-once delivery) ----
    async def create_from_offer_accepted(self, event_payload: dict) -> Order | None:
        offer_id = event_payload["offer_id"]
        existing = await self.repo.by_offer(offer_id)
        if existing:
            return existing                                   # idempotent

        listing_id = event_payload["listing_id"]
        # Atomic per-listing guard (§21). If a lock already exists the order was
        # (or is being) created — treat as idempotent no-op.
        order = Order.create_from_offer(
            buyer_id=event_payload["buyer_id"], seller_id=event_payload["seller_id"],
            listing_id=listing_id, offer_id=offer_id,
            title=event_payload.get("title", "Listing"),
            amount=event_payload["accepted_amount"], currency=event_payload["currency"],
            fee_percent=_fee_percent())
        try:
            await self.repo.acquire_listing_lock(listing_id, order.id)
        except DomainError:
            return await self.repo.by_offer(offer_id)
        try:
            await self.repo.add(order)
        except DomainError:
            await self.repo.release_listing_lock(listing_id, order.id)
            return await self.repo.by_offer(offer_id)
        return order

    # ---- queries (participants + admins only, §22) ----
    async def _load_participant(self, order_id: str, user: dict) -> Order:
        order = await self.repo.by_id(order_id)
        if not order:
            raise DomainError("ORDER_NOT_FOUND", "Order not found", 404)
        if user.get("role") not in ("admin", "moderator") and \
           user["_id"] not in (order.buyer_id, order.seller_id):
            raise DomainError("UNAUTHORIZED_ACCESS", "Not a participant of this order", 403)
        return order

    async def get(self, order_id: str, user: dict) -> dict:
        return await self._view(await self._load_participant(order_id, user))

    async def list_for_user(self, user_id: str, box: str) -> list[dict]:
        q = {"buyer_id": user_id} if box == "buyer" else {"seller_id": user_id}
        cur = self.db.orders.find(q).sort("audit.created_at", -1)
        return [self._view_doc(d) async for d in cur]

    async def cancel(self, order_id: str, user: dict) -> Order:
        order = await self._load_participant(order_id, user)
        if user.get("role") not in ("admin",) and user["_id"] != order.buyer_id:
            raise DomainError("UNAUTHORIZED_ACCESS", "Only the buyer may cancel", 403)
        order.cancel(actor=user["_id"])
        await self.repo.save(order)
        await self.repo.release_listing_lock(order.listing_id, order.id)  # free the listing
        return order

    # ---- reactions to Payment events (idempotent; invoked by event handlers) ----
    async def mark_paid(self, order_id: str, payment_id: str) -> None:
        order = await self.repo.by_id(order_id)
        if order and order.status == "AwaitingPayment":
            order.mark_paid(payment_id)
            await self.repo.save(order)

    async def mark_refunded(self, order_id: str) -> None:
        order = await self.repo.by_id(order_id)
        if order and order.status == "Paid":
            order.refund()
            await self.repo.save(order)

    # ---- reactions to Shipping events (idempotent; invoked by event handlers, Phase 7) ----
    async def begin_preparation(self, order_id: str) -> None:
        order = await self.repo.by_id(order_id)
        if order and order.status == "Paid":
            order.prepare_shipment()
            await self.repo.save(order)

    async def mark_shipped(self, order_id: str, shipment_id: str) -> None:
        order = await self.repo.by_id(order_id)
        if order and order.status == "PreparingShipment":
            order.mark_shipped(shipment_id)
            await self.repo.save(order)

    async def mark_delivered_complete(self, order_id: str) -> None:
        """Delivery confirmed -> Order Delivered then auto-Completed, which triggers the
        escrow payout release in Payments (OrderCompleted). Closes the escrow loop."""
        order = await self.repo.by_id(order_id)
        if order and order.status == "Shipped":
            order.mark_delivered()
            order.complete()
            await self.repo.save(order)

    # ---- views ----
    async def _view(self, o: Order) -> dict:
        return self._view_doc({
            "_id": o.id, "order_number": o.order_number, "buyer_id": o.buyer_id,
            "seller_id": o.seller_id, "listing_id": o.listing_id, "offer_id": o.offer_id,
            "items": [{"listing_id": i.listing_id, "title": i.title,
                       "unit_price": i.unit_price, "currency": i.currency} for i in o.items],
            "currency": o.currency, "subtotal": o.subtotal, "platform_fee": o.platform_fee,
            "total": o.total, "status": o.status, "payment_ids": o.payment_ids,
            "shipment_ids": o.shipment_ids,
            "status_history": [{"from_status": h.from_status, "to_status": h.to_status,
                                "reason": h.reason, "at": h.at} for h in o.status_history],
        })

    def _view_doc(self, d: dict) -> dict:
        return {
            "id": d["_id"], "order_number": d["order_number"],
            "buyer_id": d["buyer_id"], "seller_id": d["seller_id"],
            "listing_id": d["listing_id"], "offer_id": d.get("offer_id"),
            "items": d.get("items", []), "currency": d["currency"],
            "subtotal": d["subtotal"], "platform_fee": d["platform_fee"], "total": d["total"],
            "status": d["status"], "payment_ids": d.get("payment_ids", []),
            "shipment_ids": d.get("shipment_ids", []),
            "status_history": [{"from_status": h.get("from_status"),
                                "to_status": h.get("to_status"), "reason": h.get("reason"),
                                "at": h.get("at")} for h in d.get("status_history", [])],
        }
