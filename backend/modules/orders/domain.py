"""Orders Domain — Order aggregate (DOMAIN-005).

An Order is the immutable commercial agreement resulting from an accepted purchase.
Owns ONLY: purchase lifecycle, purchased items, buyer/seller, totals, current status,
optional Offer reference, and references to Payment(s)/Shipment(s).

Explicitly does NOT own (per directive & spec §2/§23): payment authorization, escrow,
shipping provider logic, carrier tracking, review scoring. It merely reacts to events.
Pure domain: no framework, no DB.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from buildingblocks.domain import AggregateRoot, AuditInfo, DomainError, new_id, utc_now
from buildingblocks.money import Money

# Lifecycle (DOMAIN-005 §6, §8). An Order can never return to a previous state (INV-006).
VALID_TRANSITIONS = {
    "Created": {"AwaitingPayment"},
    "AwaitingPayment": {"Paid", "Canceled"},
    "Paid": {"PreparingShipment", "Refunded"},
    "PreparingShipment": {"Shipped"},
    "Shipped": {"Delivered"},
    "Delivered": {"Completed", "Closed"},
    "Completed": set(),
    "Canceled": set(),
    "Refunded": set(),
    "Closed": set(),
}


@dataclass(frozen=True)
class OrderItem:
    listing_id: str
    title: str
    unit_price: int          # minor units
    currency: str
    item_id: str = field(default_factory=new_id)


@dataclass(frozen=True)
class OrderStatusEntry:
    """Immutable state-history entry (INV-008)."""
    from_status: str | None
    to_status: str
    reason: str | None = None
    actor: str | None = None
    at: datetime = field(default_factory=utc_now)


def _order_number() -> str:
    # Non-sequential, does not expose business volume (§22).
    return f"ARC-{new_id()[:10].upper()}"


class Order(AggregateRoot):
    def __init__(self, id, order_number, buyer_id, seller_id, listing_id,
                 items, currency, subtotal, platform_fee, total, status="Created",
                 offer_id=None, payment_ids=None, shipment_ids=None,
                 status_history=None, audit=None, version=0):
        super().__init__(id, version)
        self.order_number = order_number
        self.buyer_id = buyer_id
        self.seller_id = seller_id
        self.listing_id = listing_id
        self.items: list[OrderItem] = items
        self.currency = currency
        self.subtotal = subtotal           # buyer-paid item total (immutable, INV-005)
        self.platform_fee = platform_fee   # seller-paid fee (immutable)
        self.total = total                 # amount the buyer pays (immutable)
        self.status = status
        self.offer_id = offer_id
        self.payment_ids: list[str] = payment_ids or []
        self.shipment_ids: list[str] = shipment_ids or []
        self.status_history: list[OrderStatusEntry] = status_history or []
        self.audit = audit or AuditInfo(created_by=buyer_id)

    # ---- factory (§7): created directly into AwaitingPayment per confirmed flow ----
    @classmethod
    def create_from_offer(cls, *, buyer_id, seller_id, listing_id, offer_id,
                          title, amount, currency, fee_percent: int) -> "Order":
        item = OrderItem(listing_id=listing_id, title=title,
                         unit_price=amount, currency=currency)
        fee = round(amount * fee_percent / 100)          # seller-paid platform fee (Q4)
        order = cls(
            id=new_id(), order_number=_order_number(), buyer_id=buyer_id,
            seller_id=seller_id, listing_id=listing_id, items=[item], currency=currency,
            subtotal=amount, platform_fee=fee, total=amount, status="Created",
            offer_id=offer_id)
        order._record(None, "Created", actor=buyer_id, reason="offer_accepted")
        order._raise("OrderCreated", order._payload())
        # Buyer must pay to leave AwaitingPayment (BR-042 read as: cannot progress past
        # AwaitingPayment without payment authorization). The agreement exists now.
        order._transition("AwaitingPayment", actor="system")
        return order

    # ---- state machine ----
    def _transition(self, target: str, actor: str | None = None,
                    reason: str | None = None) -> None:
        if target not in VALID_TRANSITIONS[self.status]:
            raise DomainError("INVALID_ORDER_STATE",
                              f"Cannot move order from {self.status} to {target}", 409)
        prev = self.status
        self.status = target
        self._record(prev, target, actor=actor, reason=reason)
        self.audit.updated_at = utc_now()

    def _record(self, frm, to, actor=None, reason=None) -> None:
        self.status_history.append(
            OrderStatusEntry(from_status=frm, to_status=to, actor=actor, reason=reason))

    def _payload(self) -> dict:
        return {"order_id": self.id, "order_number": self.order_number,
                "buyer_id": self.buyer_id, "seller_id": self.seller_id,
                "listing_id": self.listing_id, "offer_id": self.offer_id,
                "amount": self.total, "currency": self.currency,
                "platform_fee": self.platform_fee}

    # ---- transitions driven by this domain (cancel) and by external events ----
    def cancel(self, actor: str, reason: str = "buyer_canceled") -> None:
        if self.status != "AwaitingPayment":
            raise DomainError("CANCELLATION_NOT_ALLOWED",
                              f"An order in {self.status} cannot be canceled", 409)
        self._transition("Canceled", actor=actor, reason=reason)
        self._raise("OrderCanceled", self._payload())

    # Reactions to Payments/Shipping domain events (invoked by event handlers, Phase 6).
    def mark_paid(self, payment_id: str) -> None:
        self._transition("Paid", actor="payments", reason="payment_captured")
        if payment_id and payment_id not in self.payment_ids:
            self.payment_ids.append(payment_id)
        self._raise("OrderPaid", {**self._payload(), "payment_id": payment_id})

    def prepare_shipment(self) -> None:
        self._transition("PreparingShipment", actor="seller")
        self._raise("OrderPrepared", self._payload())

    def mark_shipped(self, shipment_id: str) -> None:
        self._transition("Shipped", actor="shipping", reason="shipment_dispatched")
        if shipment_id and shipment_id not in self.shipment_ids:
            self.shipment_ids.append(shipment_id)
        self._raise("OrderShipped", {**self._payload(), "shipment_id": shipment_id})

    def mark_delivered(self) -> None:
        self._transition("Delivered", actor="shipping", reason="shipment_delivered")
        self._raise("OrderDelivered", self._payload())

    def complete(self) -> None:
        self._transition("Completed", actor="system", reason="delivery_confirmed")
        self._raise("OrderCompleted", self._payload())

    def refund(self, reason: str = "refunded") -> None:
        self._transition("Refunded", actor="payments", reason=reason)
        self._raise("OrderRefunded", self._payload())

    def close(self, actor: str, reason: str = "administrative") -> None:
        self._transition("Closed", actor=actor, reason=reason)
        self._raise("OrderClosed", self._payload())
