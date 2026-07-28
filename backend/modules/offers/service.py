"""Offers Application — use cases + creation rules + expiration sweeper.

Reads Listings/Identity ONLY through their published contracts (no cross-module
DB access). Enforces §8 creation rules and §17 application validation."""
from __future__ import annotations

import os
from datetime import timedelta

from motor.motor_asyncio import AsyncIOMotorDatabase

from buildingblocks.domain import DomainError
from buildingblocks.money import Money
from modules.identity.contracts import IdentityContract
from modules.listings.contracts import ListingContract

from .domain import Offer
from .repository import OfferRepository


def _validity() -> timedelta:
    return timedelta(hours=int(os.environ.get("OFFER_VALIDITY_HOURS", "48")))


class OfferService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.repo = OfferRepository(db)
        self.listings = ListingContract(db)
        self.identity = IdentityContract(db)

    async def create(self, buyer_id: str, listing_id: str, amount: int) -> Offer:
        snap = await self.listings.snapshot(listing_id)
        if not snap:
            raise DomainError("LISTING_NOT_FOUND", "Listing not found", 404)
        if not snap.is_available:                                   # INV-010 / §8
            code = "LISTING_SOLD" if snap.state in ("Sold", "Reserved") else "LISTING_NOT_AVAILABLE"
            raise DomainError(code, "This listing is not available for offers", 409)
        if not snap.allow_offers:
            raise DomainError("OFFERS_DISABLED", "This listing does not accept offers", 409)
        if buyer_id == snap.seller_id:
            raise DomainError("CANNOT_OFFER_OWN_LISTING",
                              "You cannot make an offer on your own listing", 422)  # INV-004
        if not await self.identity.is_active(buyer_id):
            raise DomainError("BUYER_INACTIVE", "Your account is not active", 403)
        if not await self.identity.is_active(snap.seller_id):
            raise DomainError("SELLER_INACTIVE", "The seller is not active", 409)

        price = Money(amount=amount, currency=snap.currency)        # valid currency = listing currency
        offer = Offer.open(listing_id, buyer_id, snap.seller_id, price, _validity())
        await self.repo.add(offer)
        return offer

    async def _load_participant(self, offer_id: str, user_id: str) -> Offer:
        offer = await self.repo.by_id(offer_id)
        if not offer:
            raise DomainError("OFFER_NOT_FOUND", "Offer not found", 404)
        offer._require_participant(user_id)                          # authz (§22)
        return offer

    async def counter(self, offer_id: str, user_id: str, amount: int) -> Offer:
        offer = await self._load_participant(offer_id, user_id)
        offer.counter(user_id, Money(amount, offer.currency), _validity())
        await self.repo.save(offer)
        return offer

    async def accept(self, offer_id: str, user_id: str) -> Offer:
        offer = await self._load_participant(offer_id, user_id)
        offer.accept(user_id)                                        # validates turn/state/expiry
        await self.repo.acquire_acceptance_lock(offer)               # atomic exactly-one (INV-005)
        await self.repo.save(offer)                                  # then persist + emit OfferAccepted
        return offer

    async def reject(self, offer_id: str, user_id: str) -> Offer:
        offer = await self._load_participant(offer_id, user_id)
        offer.reject(user_id)
        await self.repo.save(offer)
        return offer

    async def cancel(self, offer_id: str, user_id: str) -> Offer:
        offer = await self._load_participant(offer_id, user_id)
        offer.cancel(user_id)
        await self.repo.save(offer)
        return offer

    # ---- queries (participants only, §22) ----
    async def get(self, offer_id: str, user_id: str) -> dict:
        offer = await self._load_participant(offer_id, user_id)
        return await self._view(offer)

    async def list_for_user(self, user_id: str, box: str) -> list[dict]:
        q = {"buyer_id": user_id} if box == "buyer" else {"seller_id": user_id}
        cur = self.db.offers.find(q).sort("audit.updated_at", -1)
        return [await self._view_doc(d) async for d in cur]

    async def list_for_listing(self, listing_id: str, seller_id: str) -> list[dict]:
        snap = await self.listings.snapshot(listing_id)
        if not snap or snap.seller_id != seller_id:
            raise DomainError("FORBIDDEN", "Only the listing owner may view its offers", 403)
        cur = self.db.offers.find({"listing_id": listing_id}).sort("audit.updated_at", -1)
        return [await self._view_doc(d) async for d in cur]

    async def _view(self, offer: Offer) -> dict:
        return await self._view_doc({
            "_id": offer.id, "listing_id": offer.listing_id, "buyer_id": offer.buyer_id,
            "seller_id": offer.seller_id, "currency": offer.currency,
            "status": offer.status, "awaiting": offer.awaiting,
            "current_amount": offer.current_amount, "accepted_amount": offer.accepted_amount,
            "expires_at": offer.expires_at,
            "revisions": [{"actor": r.actor, "amount": r.amount, "currency": r.currency,
                           "kind": r.kind, "created_at": r.created_at} for r in offer.revisions],
        })

    async def _view_doc(self, d: dict) -> dict:
        buyer = await self.identity.summary(d["buyer_id"])
        return {
            "id": d["_id"], "listing_id": d["listing_id"],
            "buyer_id": d["buyer_id"], "seller_id": d["seller_id"],
            "buyer_name": buyer["display_name"] if buyer else None,
            "currency": d["currency"], "status": d["status"], "awaiting": d.get("awaiting"),
            "current_amount": d.get("current_amount"), "accepted_amount": d.get("accepted_amount"),
            "expires_at": d.get("expires_at"),
            "revisions": [{"actor": r["actor"], "amount": r["amount"], "currency": r["currency"],
                           "kind": r["kind"],
                           "created_at": r.get("created_at")} for r in d.get("revisions", [])],
        }

    # ---- background expiration (§12, §19) ----
    async def expire_due(self) -> int:
        from buildingblocks.domain import utc_now
        due = self.db.offers.find({"status": "Active", "expires_at": {"$lte": utc_now()}})
        count = 0
        async for d in due:
            offer = await self.repo.by_id(d["_id"])
            if offer and offer.status == "Active" and offer.is_expired():
                offer.expire()
                try:
                    await self.repo.save(offer)
                    count += 1
                except DomainError:
                    pass  # concurrent update; will be retried next sweep
        return count
