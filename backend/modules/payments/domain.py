"""Payments Domain — Payment aggregate (DOMAIN-006).

Owns the MONEY lifecycle and ESCROW (holds funds, then releases the seller payout
after the configured hold window). Never mutates Orders — it emits events that
Orders reacts to. Pure domain: no framework, no provider, no DB.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from buildingblocks.domain import AggregateRoot, AuditInfo, DomainError, new_id, utc_now

# Money lifecycle incl. escrow (Captured = funds held; Settled = released to seller).
VALID_TRANSITIONS = {
    "Created": {"PendingAuthorization", "Canceled"},
    "PendingAuthorization": {"Authorized", "Failed"},
    "Authorized": {"Captured", "Canceled", "Refunded"},
    "Captured": {"Settled", "Refunded"},         # held -> released, or refunded (dispute)
    "Settled": set(),
    "Failed": set(),
    "Canceled": set(),
    "Refunded": set(),
}


@dataclass(frozen=True)
class PaymentTransaction:
    """Immutable, append-only ledger entry (DOMAIN-006)."""
    kind: str                 # authorize | capture | settle | refund | void | fail
    amount: int
    currency: str
    provider_ref: str | None = None
    at: datetime = field(default_factory=utc_now)
    tx_id: str = field(default_factory=new_id)


class Payment(AggregateRoot):
    def __init__(self, id, order_id, buyer_id, seller_id, amount, currency, provider,
                 status="Created", transactions=None, held=False, release_at=None,
                 refunded_amount=0, audit=None, version=0):
        super().__init__(id, version)
        self.order_id = order_id
        self.buyer_id = buyer_id
        self.seller_id = seller_id
        self.amount = amount               # captured amount (minor units, immutable)
        self.currency = currency
        self.provider = provider
        self.status = status
        self.transactions: list[PaymentTransaction] = transactions or []
        self.held = held                   # escrow hold active
        self.release_at = release_at       # payout release time (set on order completion)
        self.refunded_amount = refunded_amount
        self.audit = audit or AuditInfo(created_by=buyer_id)

    @classmethod
    def create(cls, *, order_id, buyer_id, seller_id, amount, currency, provider) -> "Payment":
        p = cls(id=new_id(), order_id=order_id, buyer_id=buyer_id, seller_id=seller_id,
                amount=amount, currency=currency, provider=provider, status="Created")
        p._raise("PaymentCreated", p._payload())
        return p

    def _transition(self, target: str) -> None:
        if target not in VALID_TRANSITIONS[self.status]:
            raise DomainError("INVALID_PAYMENT_STATE",
                              f"Cannot move payment from {self.status} to {target}", 409)
        self.status = target
        self.audit.updated_at = utc_now()

    def _payload(self) -> dict:
        return {"payment_id": self.id, "order_id": self.order_id, "buyer_id": self.buyer_id,
                "seller_id": self.seller_id, "amount": self.amount, "currency": self.currency}

    def initiate(self) -> None:
        self._transition("PendingAuthorization")
        self._raise("PaymentInitiated", self._payload())

    def authorize(self, provider_ref: str | None = None) -> None:
        self._transition("Authorized")
        self.transactions.append(PaymentTransaction("authorize", self.amount, self.currency, provider_ref))
        self._raise("PaymentAuthorized", self._payload())

    def capture(self, provider_ref: str | None = None) -> None:
        """Immediate capture into escrow (funds held). Confirmed policy (Q3)."""
        self._transition("Captured")
        self.held = True
        self.transactions.append(PaymentTransaction("capture", self.amount, self.currency, provider_ref))
        self._raise("PaymentCaptured", self._payload())

    def schedule_release(self, hold: timedelta) -> None:
        """Called when the Order is Completed. Sets the payout release time (escrow
        belongs to Payments; Orders knows nothing about payout scheduling)."""
        if self.status != "Captured" or not self.held:
            return
        self.release_at = utc_now() + hold
        self._raise("PaymentReleaseScheduled",
                    {**self._payload(), "release_at": self.release_at.isoformat()})

    def is_release_due(self, now: datetime | None = None) -> bool:
        now = now or utc_now()
        if self.release_at is None:
            return False
        release_at = self.release_at
        if release_at.tzinfo is None:                 # Mongo may return naive UTC
            release_at = release_at.replace(tzinfo=timezone.utc)
        return self.status == "Captured" and self.held and now >= release_at

    def release(self, provider_ref: str | None = None) -> None:
        self._transition("Settled")
        self.held = False
        self.transactions.append(PaymentTransaction("settle", self.amount, self.currency, provider_ref))
        self._raise("PaymentReleased", self._payload())          # payout to seller

    def refund(self, provider_ref: str | None = None, reason: str = "dispute") -> None:
        if self.status not in ("Authorized", "Captured"):
            raise DomainError("REFUND_NOT_ALLOWED",
                              f"A {self.status} payment cannot be refunded", 409)
        self._transition("Refunded")
        self.held = False
        self.refunded_amount = self.amount
        self.transactions.append(PaymentTransaction("refund", self.amount, self.currency, provider_ref))
        self._raise("PaymentRefunded", {**self._payload(), "reason": reason})

    def fail(self, reason: str) -> None:
        self._transition("Failed")
        self.transactions.append(PaymentTransaction("fail", self.amount, self.currency, reason))
        self._raise("PaymentFailed", {**self._payload(), "reason": reason})
