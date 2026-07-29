"""Reviews Application — eligibility-checked creation, responses, moderation, queries.

Reads Orders ONLY via OrderContract and Identity ONLY via IdentityContract (no
cross-module DB access). Reviews emits reputation-input events; it NEVER writes to
identity_users — Identity reacts to ReviewPublished and updates reputation itself (§11).
"""
from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorDatabase

from buildingblocks.domain import DomainError
from modules.identity.contracts import IdentityContract
from modules.orders.contracts import OrderContract

from .domain import Review
from .repository import ReviewRepository

COLLECTION = "reviews"


class ReviewService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.repo = ReviewRepository(db)
        self.orders = OrderContract(db)
        self.identity = IdentityContract(db)

    # ---- creation (publish immediately) ----
    async def create(self, order_id: str, author: dict, rating: int,
                     comment: str | None = None) -> Review:
        recipient_id = await self._recipient_for(order_id, author["_id"])
        review = Review.create(order_id=order_id, author_id=author["_id"],
                               recipient_id=recipient_id, rating=rating, comment=comment)
        await self.repo.add(review)          # unique index -> deterministic duplicate failure
        return review

    async def _recipient_for(self, order_id: str, author_id: str) -> str:
        snap = await self.orders.snapshot(order_id)
        if not snap:
            raise DomainError("ORDER_NOT_FOUND", "Order not found", 404)
        if snap.status != "Completed":
            raise DomainError("ORDER_NOT_COMPLETED",
                              "Reviews can only be left on completed orders", 409)
        if author_id == snap.buyer_id:
            return snap.seller_id
        if author_id == snap.seller_id:
            return snap.buyer_id
        raise DomainError("UNAUTHORIZED_REVIEWER", "Only order participants may review", 403)

    async def eligibility(self, order_id: str, user: dict) -> dict:
        snap = await self.orders.snapshot(order_id)
        if not snap:
            raise DomainError("ORDER_NOT_FOUND", "Order not found", 404)
        uid = user["_id"]
        is_participant = uid in (snap.buyer_id, snap.seller_id)
        recipient_id = (snap.seller_id if uid == snap.buyer_id else
                        snap.buyer_id if uid == snap.seller_id else None)
        existing = None
        if is_participant:
            existing = await self.db[COLLECTION].find_one(
                {"order_id": order_id, "author_id": uid}, {"_id": 1})
        return {"order_id": order_id, "order_status": snap.status,
                "is_participant": is_participant,
                "recipient_id": recipient_id,
                "can_review": bool(is_participant and snap.status == "Completed" and not existing),
                "already_reviewed": bool(existing)}

    # ---- responses (recipient only, one, immutable) ----
    async def respond(self, review_id: str, user: dict, comment: str) -> Review:
        review = await self._load(review_id)
        if user["_id"] != review.recipient_id and user.get("role") != "admin":
            raise DomainError("UNAUTHORIZED_ACCESS",
                              "Only the review recipient may respond", 403)
        review.add_response(user["_id"], comment)
        await self.repo.save(review)
        return review

    # ---- moderation (moderator/admin) ----
    async def hide(self, review_id: str, user: dict) -> Review:
        review = await self._load(review_id)
        review.hide(actor=user["_id"])
        await self.repo.save(review)
        return review

    async def unhide(self, review_id: str, user: dict) -> Review:
        review = await self._load(review_id)
        review.unhide(actor=user["_id"])
        await self.repo.save(review)
        return review

    async def remove(self, review_id: str, user: dict, reason: str = "moderation") -> Review:
        review = await self._load(review_id)
        review.remove(actor=user["_id"], reason=reason)
        await self.repo.save(review)
        return review

    # ---- queries ----
    async def for_user(self, user_id: str) -> dict:
        """Public: published reviews RECEIVED by a user + a summary."""
        cur = self.db[COLLECTION].find(
            {"recipient_id": user_id, "status": "Published"}).sort("audit.created_at", -1)
        items = [await self._view(d) async for d in cur]
        summary = await self.identity.summary(user_id)
        return {"items": items,
                "average_rating": (summary or {}).get("reputation", {}).get("average_rating", 0),
                "completed_reviews": (summary or {}).get("reputation", {}).get("completed_reviews", 0)}

    async def for_order(self, order_id: str, user: dict) -> list[dict]:
        snap = await self.orders.snapshot(order_id)
        if not snap:
            raise DomainError("ORDER_NOT_FOUND", "Order not found", 404)
        is_staff = user.get("role") in ("admin", "moderator")
        if not is_staff and user["_id"] not in (snap.buyer_id, snap.seller_id):
            raise DomainError("UNAUTHORIZED_ACCESS", "Not a participant", 403)
        q = {"order_id": order_id}
        if not is_staff:
            q["status"] = {"$ne": "Removed"}   # participants never see removed reviews
        cur = self.db[COLLECTION].find(q).sort("audit.created_at", -1)
        return [await self._view(d) async for d in cur]

    # ---- helpers ----
    async def _load(self, review_id: str) -> Review:
        r = await self.repo.by_id(review_id)
        if not r:
            raise DomainError("REVIEW_NOT_FOUND", "Review not found", 404)
        return r

    async def _view(self, d: dict) -> dict:
        author = await self.identity.summary(d["author_id"])
        resp = d.get("response")
        return {
            "id": d["_id"], "order_id": d["order_id"], "author_id": d["author_id"],
            "author_name": (author or {}).get("display_name"),
            "recipient_id": d["recipient_id"], "rating": d["rating"],
            "comment": d.get("comment"), "status": d.get("status", "Published"),
            "created_at": d.get("audit", {}).get("created_at"),
            "response": ({"comment": resp["comment"], "author_id": resp["author_id"],
                          "at": resp.get("at")} if resp else None),
        }
