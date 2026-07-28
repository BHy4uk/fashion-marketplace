"""Listings Application — use cases + read-side search (Phase-3 MVP tier via Mongo).

Search rules: only public listings; sold excluded from default results; hidden
never returned (BR-020..024). Read model is derived and rebuildable."""
from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorDatabase

from buildingblocks.domain import DomainError
from modules.identity.contracts import IdentityContract

from .domain import Attributes, Listing, ListingImage, Money
from .repository import ListingRepository


class ListingService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.repo = ListingRepository(db)
        self.identity = IdentityContract(db)

    async def _seller_active(self, seller_id: str) -> bool:
        return await self.identity.is_active(seller_id)

    async def create_draft(self, seller_id: str, data: dict) -> Listing:
        price = Money(amount=data["price_amount"], currency=data.get("currency", "UAH"))
        attrs = Attributes(**{k: data.get(k, "") for k in
                              ("brand", "category", "gender", "size", "color",
                               "material", "condition", "season", "style")})
        images = [ListingImage(file_id=i.get("file_id", i["url"]), url=i["url"], position=n)
                  for n, i in enumerate(data.get("images", []))]
        listing = Listing.create_draft(seller_id, data["title"], data.get("description", ""),
                                       price, attrs, images,
                                       allow_offers=data.get("allow_offers", True))
        await self.repo.add(listing)
        return listing

    async def _owned(self, listing_id: str, seller_id: str) -> Listing:
        l = await self.repo.by_id(listing_id)
        if not l or l.state == "SoftDeleted":
            raise DomainError("LISTING_NOT_FOUND", "Listing not found", 404)
        if l.seller_id != seller_id:
            raise DomainError("FORBIDDEN", "Only the listing owner may modify it", 403)
        return l

    async def publish(self, listing_id: str, seller_id: str) -> Listing:
        l = await self._owned(listing_id, seller_id)
        l.publish(await self._seller_active(seller_id))
        await self.repo.save(l)
        return l

    async def change_price(self, listing_id: str, seller_id: str, amount: int) -> Listing:
        l = await self._owned(listing_id, seller_id)
        l.change_price(Money(amount=amount, currency=l.price.currency))
        await self.repo.save(l)
        return l

    async def remove(self, listing_id: str, seller_id: str) -> Listing:
        """DELETE = soft delete (BR-016). Valid from Draft/Ready/Published/Archived;
        blocked from Reserved/Sold (active order or terminal)."""
        l = await self._owned(listing_id, seller_id)
        l.soft_delete()
        await self.repo.save(l)
        return l

    async def archive(self, listing_id: str, seller_id: str) -> Listing:
        l = await self._owned(listing_id, seller_id)
        l.archive()
        await self.repo.save(l)
        return l

    # ---- event-driven availability (reacts to Order lifecycle, idempotent) ----
    async def reserve_for_order(self, listing_id: str) -> None:
        l = await self.repo.by_id(listing_id)
        if l and l.state == "Published":
            l.reserve()
            await self.repo.save(l)

    async def release_reservation(self, listing_id: str) -> None:
        l = await self.repo.by_id(listing_id)
        if l and l.state == "Reserved":
            l.release()
            await self.repo.save(l)

    async def get_public(self, id_or_slug: str) -> dict:
        doc = await self.db.listings.find_one(
            {"$or": [{"_id": id_or_slug}, {"slug": id_or_slug}]})
        if not doc or doc["state"] in ("SoftDeleted", "Draft", "Ready", "Archived"):
            raise DomainError("LISTING_NOT_FOUND", "Listing not found", 404)
        seller = await self.identity.summary(doc["seller_id"])
        return _view(doc, seller)

    async def my_listings(self, seller_id: str) -> list[dict]:
        cur = self.db.listings.find({"seller_id": seller_id, "state": {"$ne": "SoftDeleted"}})
        return [_view(d) async for d in cur.sort("audit.created_at", -1)]

    async def search(self, params: dict) -> dict:
        q: dict = {"state": {"$in": ["Published", "Reserved"]}}  # sold excluded (BR-022)
        text = (params.get("q") or "").strip()
        if text:
            q["$or"] = [{"title": {"$regex": text, "$options": "i"}},
                        {"description": {"$regex": text, "$options": "i"}},
                        {"attributes.brand": {"$regex": text, "$options": "i"}}]
        for f in ("brand", "category", "gender", "size", "color", "material", "condition"):
            if params.get(f):
                q[f"attributes.{f}"] = params[f]
        if params.get("min_price"):
            q.setdefault("price.amount", {})["$gte"] = int(params["min_price"])
        if params.get("max_price"):
            q.setdefault("price.amount", {})["$lte"] = int(params["max_price"])

        sort_map = {"newest": ("audit.created_at", -1), "price_asc": ("price.amount", 1),
                    "price_desc": ("price.amount", -1)}
        sort_field, sort_dir = sort_map.get(params.get("sort", "newest"),
                                            ("audit.created_at", -1))
        page = max(1, int(params.get("page", 1)))
        size = min(48, max(1, int(params.get("page_size", 24))))
        total = await self.db.listings.count_documents(q)
        cur = (self.db.listings.find(q).sort(sort_field, sort_dir)
               .skip((page - 1) * size).limit(size))
        items = [_view(d) async for d in cur]
        facets = await self._facets(q)
        return {"items": items, "total": total, "page": page, "page_size": size,
                "facets": facets}

    async def _facets(self, base_q: dict) -> dict:
        out = {}
        for field in ("brand", "category", "condition", "size"):
            pipeline = [{"$match": base_q},
                        {"$group": {"_id": f"$attributes.{field}", "count": {"$sum": 1}}},
                        {"$match": {"_id": {"$nin": ["", None]}}},
                        {"$sort": {"count": -1}}, {"$limit": 12}]
            out[field] = [{"value": d["_id"], "count": d["count"]}
                          async for d in self.db.listings.aggregate(pipeline)]
        return out


def _view(doc: dict, seller: dict | None = None) -> dict:
    v = {
        "id": doc["_id"], "slug": doc.get("slug"), "seller_id": doc["seller_id"],
        "title": doc["title"], "description": doc["description"],
        "price": doc["price"], "attributes": doc["attributes"],
        "images": doc.get("images", []), "state": doc["state"],
        "allow_offers": doc.get("allow_offers", True),
        "created_at": doc.get("audit", {}).get("created_at"),
    }
    if seller is not None:
        v["seller"] = {"id": seller["id"], "display_name": seller.get("display_name"),
                       "reputation": seller.get("reputation")}
    return v
