"""Listings Contracts — the ONLY sanctioned cross-module view of a Listing.

Exposes an availability snapshot for Commerce modules (Offers/Orders) without
leaking the aggregate internals or the listings collection."""
from __future__ import annotations

from dataclasses import dataclass

from motor.motor_asyncio import AsyncIOMotorDatabase

# States in which a listing may receive offers / be purchased (DOMAIN-002 §13, BR-020)
OFFERABLE_STATES = {"Published"}


@dataclass(frozen=True)
class ListingSnapshot:
    id: str
    seller_id: str
    state: str
    price_amount: int
    currency: str
    allow_offers: bool

    @property
    def is_available(self) -> bool:
        return self.state in OFFERABLE_STATES


class ListingContract:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def snapshot(self, listing_id: str) -> ListingSnapshot | None:
        d = await self.db.listings.find_one(
            {"_id": listing_id},
            {"seller_id": 1, "state": 1, "price": 1, "allow_offers": 1})
        if not d:
            return None
        return ListingSnapshot(
            id=d["_id"], seller_id=d["seller_id"], state=d["state"],
            price_amount=d["price"]["amount"], currency=d["price"]["currency"],
            allow_offers=d.get("allow_offers", True))

    async def detail(self, listing_id: str) -> dict | None:
        """Minimal content view for AI enrichment (only the fields the task needs, §22)."""
        d = await self.db.listings.find_one(
            {"_id": listing_id},
            {"title": 1, "description": 1, "seller_id": 1, "state": 1, "price": 1})
        if not d:
            return None
        return {"id": d["_id"], "title": d.get("title", ""),
                "description": d.get("description", ""), "seller_id": d["seller_id"],
                "state": d.get("state"), "price_amount": d.get("price", {}).get("amount")}
