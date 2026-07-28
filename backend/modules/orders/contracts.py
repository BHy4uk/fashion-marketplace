"""Orders Contracts — the ONLY sanctioned cross-module view of an Order."""
from __future__ import annotations

from dataclasses import dataclass

from motor.motor_asyncio import AsyncIOMotorDatabase


@dataclass(frozen=True)
class OrderSnapshot:
    id: str
    buyer_id: str
    seller_id: str
    listing_id: str
    total: int
    currency: str
    status: str


class OrderContract:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def snapshot(self, order_id: str) -> OrderSnapshot | None:
        d = await self.db.orders.find_one(
            {"_id": order_id},
            {"buyer_id": 1, "seller_id": 1, "listing_id": 1, "total": 1,
             "currency": 1, "status": 1})
        if not d:
            return None
        return OrderSnapshot(id=d["_id"], buyer_id=d["buyer_id"], seller_id=d["seller_id"],
                             listing_id=d["listing_id"], total=d["total"],
                             currency=d["currency"], status=d["status"])
