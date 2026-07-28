"""Payments Application — checkout/capture, webhook, refund, escrow release.

Reads Orders ONLY via OrderContract. Escrow lives entirely here; Orders learns of
money outcomes through domain events (PaymentCaptured / PaymentRefunded)."""
from __future__ import annotations

import os
from datetime import timedelta

from motor.motor_asyncio import AsyncIOMotorDatabase

from buildingblocks.domain import DomainError
from modules.orders.contracts import OrderContract

from .domain import Payment
from .provider import build_provider
from .repository import PaymentRepository


def _hold() -> timedelta:
    return timedelta(hours=int(os.environ.get("PAYOUT_HOLD_HOURS", "72")))  # Q3


class PaymentService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.repo = PaymentRepository(db)
        self.orders = OrderContract(db)
        self.provider = build_provider()

    async def checkout(self, order_id: str, user: dict) -> dict:
        snap = await self.orders.snapshot(order_id)
        if not snap:
            raise DomainError("ORDER_NOT_FOUND", "Order not found", 404)
        if user["_id"] != snap.buyer_id:
            raise DomainError("UNAUTHORIZED_ACCESS", "Only the buyer may pay", 403)

        # Idempotent: an already-captured/settled payment short-circuits regardless of
        # the order's current status (e.g. order already Paid).
        existing = await self.repo.by_order(order_id)
        if existing and existing.status in ("Captured", "Settled"):
            return {"payment_id": existing.id, "status": existing.status, "redirect": None}

        if snap.status != "AwaitingPayment":
            raise DomainError("ORDER_NOT_PAYABLE",
                              f"Order in {snap.status} cannot be paid", 409)

        payment = existing or Payment.create(
            order_id=order_id, buyer_id=snap.buyer_id, seller_id=snap.seller_id,
            amount=snap.total, currency=snap.currency, provider=self.provider.name)
        if not existing:
            payment.initiate()
            await self.repo.add(payment)

        result = await self.provider.create_checkout(
            order_id=order_id, amount=f"{snap.total / 100:.2f}", currency=snap.currency,
            description=f"ARCHIVE order {order_id}", hold=True)

        # Sandbox settles synchronously so the escrow flow is fully testable without keys.
        if result.get("auto_settle"):
            payment.authorize(provider_ref="sandbox")
            payment.capture(provider_ref="sandbox")
            await self.repo.save(payment)
            return {"payment_id": payment.id, "status": payment.status, "redirect": None}

        # LiqPay: return the hosted-checkout data; webhook completes the payment.
        return {"payment_id": payment.id, "status": payment.status,
                "checkout_url": result.get("checkout_url"),
                "data": result.get("data"), "signature": result.get("signature")}

    async def handle_webhook(self, data: str, signature: str) -> dict:
        event = await self.provider.verify_callback(data, signature)  # raises on bad sig
        order_id = event.get("order_id")
        status = event.get("status")
        payment = await self.repo.by_order(order_id)
        if not payment:
            raise DomainError("PAYMENT_NOT_FOUND", "Unknown payment", 404)
        ref = event.get("payment_id") or event.get("transaction_id")
        if status in ("success", "hold_wait", "hold_completion", "subscribed") and payment.status == "PendingAuthorization":
            payment.authorize(provider_ref=str(ref))
            payment.capture(provider_ref=str(ref))
            await self.repo.save(payment)
        elif status in ("failure", "error") and payment.status == "PendingAuthorization":
            payment.fail(reason=str(event.get("err_description", status)))
            await self.repo.save(payment)
        elif status in ("reversed", "refund") and payment.status in ("Authorized", "Captured"):
            payment.refund(provider_ref=str(ref))
            await self.repo.save(payment)
        return {"ok": True}

    async def refund_for_order(self, order_id: str, reason: str = "order_canceled") -> None:
        payment = await self.repo.by_order(order_id)
        if payment and payment.status in ("Authorized", "Captured"):
            await self.provider.refund(order_id)
            payment.refund(reason=reason)
            await self.repo.save(payment)

    async def schedule_release_for_order(self, order_id: str) -> None:
        payment = await self.repo.by_order(order_id)
        if payment and payment.status == "Captured" and payment.held and payment.release_at is None:
            payment.schedule_release(_hold())
            await self.repo.save(payment)

    async def release_due(self) -> int:
        from buildingblocks.domain import utc_now
        cur = self.db.payments.find({"status": "Captured", "held": True,
                                     "release_at": {"$lte": utc_now()}})
        count = 0
        async for d in cur:
            payment = await self.repo.by_id(d["_id"])
            if payment and payment.is_release_due():
                await self.provider.capture_hold(payment.order_id)  # finalize with provider
                payment.release(provider_ref="release")
                try:
                    await self.repo.save(payment)
                    count += 1
                except DomainError:
                    pass
        return count

    async def get_for_order(self, order_id: str, user: dict) -> dict | None:
        snap = await self.orders.snapshot(order_id)
        if not snap:
            raise DomainError("ORDER_NOT_FOUND", "Order not found", 404)
        if user.get("role") not in ("admin", "moderator") and \
           user["_id"] not in (snap.buyer_id, snap.seller_id):
            raise DomainError("UNAUTHORIZED_ACCESS", "Not a participant", 403)
        payment = await self.repo.by_order(order_id)
        if not payment:
            return None
        return {"id": payment.id, "order_id": payment.order_id, "status": payment.status,
                "amount": payment.amount, "currency": payment.currency,
                "provider": payment.provider, "held": payment.held,
                "release_at": payment.release_at,
                "transactions": [{"kind": t.kind, "amount": t.amount, "at": t.at}
                                 for t in payment.transactions]}
