"""Analytics Application — seller + marketplace reporting read models (read-only).

All money values are in minor units (kopiykas/cents). Revenue is recognised on
completed orders; GMV counts orders that reached payment or beyond."""
from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorDatabase

# Order statuses that represent captured value (buyer has paid; funds in escrow+).
_PAID_STATES = ["Paid", "PreparingShipment", "Shipped", "Delivered", "Completed"]
_COMPLETED = "Completed"


class AnalyticsService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    # ---- seller dashboard ----
    async def seller_overview(self, seller_id: str) -> dict:
        listings = self.db.listings
        orders = self.db.orders

        listings_by_state = {
            d["_id"]: d["count"] async for d in listings.aggregate([
                {"$match": {"seller_id": seller_id, "state": {"$ne": "SoftDeleted"}}},
                {"$group": {"_id": "$state", "count": {"$sum": 1}}}])
        }
        active_listings = listings_by_state.get("Published", 0) + listings_by_state.get("Reserved", 0)

        gross_sales = await orders.count_documents(
            {"seller_id": seller_id, "status": {"$in": _PAID_STATES}})
        completed = await orders.count_documents(
            {"seller_id": seller_id, "status": _COMPLETED})

        revenue = await self._sum(orders, {"seller_id": seller_id, "status": _COMPLETED}, "subtotal")
        fees = await self._sum(orders, {"seller_id": seller_id, "status": _COMPLETED}, "platform_fee")
        pending_payout = await self._sum(
            self.db.payments,
            {"seller_id": seller_id, "held": True,
             "status": {"$in": ["Captured", "ReleaseScheduled"]}}, "amount")

        offers_received = await self.db.offers.count_documents({"seller_id": seller_id})
        offers_accepted = await self.db.offers.count_documents(
            {"seller_id": seller_id, "status": "Accepted"})

        ratings = await self.db.reviews.aggregate([
            {"$match": {"recipient_id": seller_id, "state": "Published"}},
            {"$group": {"_id": None, "avg": {"$avg": "$rating"}, "count": {"$sum": 1}}}]).to_list(1)
        rating = ratings[0] if ratings else {}

        return {
            "listings": {"total": sum(listings_by_state.values()), "active": active_listings,
                         "by_state": listings_by_state},
            "sales": {"orders": gross_sales, "completed": completed,
                      "net_revenue": revenue, "platform_fees": fees},
            "escrow": {"pending_payout": pending_payout},
            "offers": {"received": offers_received, "accepted": offers_accepted},
            "reputation": {"average_rating": round(rating.get("avg", 0), 2) if rating.get("avg") else None,
                           "reviews": rating.get("count", 0)},
        }

    # ---- marketplace (staff) dashboard ----
    async def marketplace_overview(self) -> dict:
        orders = self.db.orders
        orders_by_status = {
            d["_id"]: d["count"] async for d in orders.aggregate([
                {"$group": {"_id": "$status", "count": {"$sum": 1}}}])
        }
        gmv = await self._sum(orders, {"status": {"$in": _PAID_STATES}}, "total")
        completed_value = await self._sum(orders, {"status": _COMPLETED}, "total")
        platform_fees = await self._sum(orders, {"status": _COMPLETED}, "platform_fee")

        total_users = await self.db.identity_users.count_documents({"state": {"$ne": "Deleted"}})
        listings_by_state = {
            d["_id"]: d["count"] async for d in self.db.listings.aggregate([
                {"$group": {"_id": "$state", "count": {"$sum": 1}}}])
        }

        open_cases = await self.db.moderation_cases.count_documents(
            {"status": {"$in": ["Created", "UnderReview", "Investigation", "DecisionMade"]}})
        ai_fraud_signals = await self.db.moderation_cases.count_documents({"reports.reason": "ai_fraud_signal"})

        top_brands = [{"value": d["_id"], "count": d["count"]}
                      async for d in self.db.listings.aggregate([
                          {"$match": {"attributes.brand": {"$nin": ["", None]}}},
                          {"$group": {"_id": "$attributes.brand", "count": {"$sum": 1}}},
                          {"$sort": {"count": -1}}, {"$limit": 8}])]
        top_categories = [{"value": d["_id"], "count": d["count"]}
                          async for d in self.db.listings.aggregate([
                              {"$match": {"attributes.category": {"$nin": ["", None]}}},
                              {"$group": {"_id": "$attributes.category", "count": {"$sum": 1}}},
                              {"$sort": {"count": -1}}, {"$limit": 8}])]

        return {
            "gmv": {"total": gmv, "completed_value": completed_value, "platform_fees": platform_fees},
            "orders": {"total": sum(orders_by_status.values()), "by_status": orders_by_status},
            "users": {"total": total_users},
            "listings": {"total": sum(listings_by_state.values()), "by_state": listings_by_state},
            "trust_safety": {"open_cases": open_cases, "ai_fraud_signals": ai_fraud_signals},
            "top_brands": top_brands, "top_categories": top_categories,
        }

    async def _sum(self, col, match: dict, field: str) -> int:
        res = await col.aggregate([
            {"$match": match},
            {"$group": {"_id": None, "total": {"$sum": f"${field}"}}}]).to_list(1)
        return int(res[0]["total"]) if res else 0
