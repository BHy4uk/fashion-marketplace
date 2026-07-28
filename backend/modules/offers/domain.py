"""Offers Domain — Offer aggregate (DOMAIN-004).

Governs price negotiation. Owns lifecycle, counter-offers, immutable negotiation
history, and domain events. Never touches Listings/Orders/Payments/Shipping.
Pure domain: no framework, no DB.

Negotiation turn model (inferred minimally from §7/§9/§15, no invented rules):
the party currently *awaited* may accept / reject / counter; the last proposer
may cancel. Buyer opens the negotiation; seller is awaited first.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from buildingblocks.domain import AggregateRoot, AuditInfo, DomainError, new_id, utc_now
from buildingblocks.money import Money

VALID_TRANSITIONS = {
    "Draft": {"Submitted"},
    "Submitted": {"Active"},
    "Active": {"Accepted", "Rejected", "Expired", "Canceled"},
    "Accepted": set(),
    "Rejected": set(),
    "Expired": set(),
    "Canceled": set(),
}

BUYER = "buyer"
SELLER = "seller"


@dataclass(frozen=True)
class OfferRevision:
    """Immutable entry in the negotiation history (DOMAIN-004 §13)."""
    actor: str            # BUYER | SELLER
    amount: int           # minor units
    currency: str
    kind: str             # "offer" | "counter"
    created_at: datetime = field(default_factory=utc_now)
    revision_id: str = field(default_factory=new_id)


class Offer(AggregateRoot):
    def __init__(self, id, listing_id, buyer_id, seller_id, currency,
                 revisions, status="Draft", awaiting=SELLER, expires_at=None,
                 accepted_amount=None, audit=None, version=0):
        super().__init__(id, version)
        self.listing_id = listing_id
        self.buyer_id = buyer_id
        self.seller_id = seller_id
        self.currency = currency
        self.revisions: list[OfferRevision] = revisions
        self.status = status
        self.awaiting = awaiting              # whose turn: BUYER | SELLER | None
        self.expires_at = expires_at
        self.accepted_amount = accepted_amount
        self.audit = audit or AuditInfo(created_by=buyer_id)

    # ---- helpers ----
    @property
    def current_amount(self) -> int:
        return self.revisions[-1].amount

    def _transition(self, target: str) -> None:
        if target not in VALID_TRANSITIONS[self.status]:
            raise DomainError("INVALID_OFFER_STATE",
                              f"Cannot move offer from {self.status} to {target}", 409)
        self.status = target
        self.audit.updated_at = utc_now()

    def _require_participant(self, user_id: str) -> str:
        if user_id == self.buyer_id:
            return BUYER
        if user_id == self.seller_id:
            return SELLER
        raise DomainError("FORBIDDEN", "Not a participant of this offer", 403)

    def is_expired(self, now: datetime | None = None) -> bool:
        now = now or utc_now()
        return self.expires_at is not None and now >= self.expires_at

    # ---- factory (§8) ----
    @classmethod
    def open(cls, listing_id, buyer_id, seller_id, price: Money,
             validity: timedelta) -> "Offer":
        if buyer_id == seller_id:
            raise DomainError("CANNOT_OFFER_OWN_LISTING",
                              "You cannot make an offer on your own listing", 422)  # INV-004
        offer = cls(
            id=new_id(), listing_id=listing_id, buyer_id=buyer_id, seller_id=seller_id,
            currency=price.currency,
            revisions=[OfferRevision(BUYER, price.amount, price.currency, "offer")],
            status="Draft", awaiting=SELLER,
            expires_at=utc_now() + validity)
        offer._raise("OfferCreated", offer._event_payload())
        # Draft → Submitted → Active (states are traversed, never skipped, §6)
        offer._transition("Submitted")
        offer._raise("OfferSubmitted", offer._event_payload())
        offer._transition("Active")
        return offer

    # ---- negotiation (§7, §9, §10, §11) ----
    def _acting_role(self, user_id: str) -> str:
        role = self._require_participant(user_id)
        if self.status != "Active":
            raise DomainError("INVALID_OFFER_STATE",
                              f"Offer is {self.status} and cannot be negotiated", 409)
        if self.is_expired():
            raise DomainError("OFFER_EXPIRED", "This offer has expired", 409)  # INV-007
        return role

    def counter(self, user_id: str, price: Money, validity: timedelta) -> None:
        role = self._acting_role(user_id)
        if role != self.awaiting:
            raise DomainError("NOT_YOUR_TURN", "It is not your turn to respond", 409)
        if not self.current_price().same_currency(price):
            raise DomainError("CURRENCY_MISMATCH", "Currency cannot change mid-negotiation", 422)
        self.revisions.append(OfferRevision(role, price.amount, price.currency, "counter"))
        self.expires_at = utc_now() + validity            # reset expiration (§7)
        self.awaiting = BUYER if role == SELLER else SELLER
        self.audit.updated_at = utc_now()
        self._raise("CounterOfferCreated", self._event_payload())

    def accept(self, user_id: str) -> None:
        role = self._acting_role(user_id)
        if role != self.awaiting:
            raise DomainError("NOT_YOUR_TURN", "It is not your turn to respond", 409)
        self._transition("Accepted")                       # INV-006 (now immutable)
        self.accepted_amount = self.current_amount
        self.awaiting = None
        self._raise("OfferAccepted", {
            **self._event_payload(),
            "accepted_amount": self.accepted_amount,
            "accepted_by": role,
        })

    def reject(self, user_id: str) -> None:
        role = self._acting_role(user_id)
        if role != self.awaiting:
            raise DomainError("NOT_YOUR_TURN", "It is not your turn to respond", 409)
        self._transition("Rejected")                       # INV-008
        self.awaiting = None
        self._raise("OfferRejected", self._event_payload())

    def cancel(self, user_id: str) -> None:
        role = self._require_participant(user_id)
        if role != BUYER:
            raise DomainError("FORBIDDEN", "Only the buyer may cancel an offer", 403)  # §11
        if self.status != "Active":
            raise DomainError("INVALID_OFFER_STATE", "Only active offers can be canceled", 409)
        self._transition("Canceled")                       # INV-009
        self.awaiting = None
        self._raise("OfferCanceled", self._event_payload())

    def expire(self) -> None:
        if self.status != "Active":
            return
        self._transition("Expired")
        self.awaiting = None
        self._raise("OfferExpired", self._event_payload())

    # ---- helpers ----
    def current_price(self) -> Money:
        return Money(self.current_amount, self.currency)

    def _event_payload(self) -> dict:
        return {"offer_id": self.id, "listing_id": self.listing_id,
                "buyer_id": self.buyer_id, "seller_id": self.seller_id,
                "amount": self.current_amount, "currency": self.currency}
