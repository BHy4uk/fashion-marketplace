"""Startup seeding: indexes, admin, taxonomy, demo users + listings.
Idempotent — safe to run on every boot."""
from __future__ import annotations

import os

from motor.motor_asyncio import AsyncIOMotorDatabase

from buildingblocks.domain import utc_now
from buildingblocks.security import hash_password
from modules.identity.domain import User
from modules.identity.repository import UserRepository
from modules.listings.service import ListingService

CATEGORIES = [
    ("outerwear", "Outerwear", ["Men", "Women", "Unisex"]),
    ("tops", "Tops & Tees", ["Men", "Women", "Unisex"]),
    ("hoodies", "Hoodies & Sweatshirts", ["Men", "Women", "Unisex"]),
    ("bottoms", "Trousers & Jeans", ["Men", "Women"]),
    ("dresses", "Dresses", ["Women"]),
    ("footwear", "Footwear", ["Men", "Women", "Unisex"]),
    ("bags", "Bags", ["Men", "Women", "Unisex"]),
    ("backpacks", "Backpacks", ["Unisex"]),
    ("hats", "Hats", ["Unisex"]),
    ("belts", "Belts", ["Unisex"]),
    ("scarves", "Scarves", ["Unisex"]),
    ("accessories", "Accessories", ["Unisex"]),
]
BRANDS = ["Nike", "Adidas", "Stone Island", "Carhartt WIP", "Acne Studios",
          "Comme des Garçons", "Maison Margiela", "Rick Owens", "Balenciaga",
          "Prada", "Gucci", "Bottega Veneta", "The North Face", "Supreme",
          "Palace", "New Balance", "Salomon", "Arc'teryx", "Vintage", "Other"]

_IMG = {
    "sneaker1": "https://images.unsplash.com/photo-1600185365778-7875a359b924?crop=entropy&cs=srgb&fm=jpg&q=85&w=1000",
    "sneaker2": "https://images.unsplash.com/photo-1544441892-83af2e53ea48?crop=entropy&cs=srgb&fm=jpg&q=85&w=1000",
    "bag1": "https://images.unsplash.com/photo-1705909237050-7a7625b47fac?crop=entropy&cs=srgb&fm=jpg&q=85&w=1000",
    "bag2": "https://images.unsplash.com/photo-1605733513597-a8f8341084e6?crop=entropy&cs=srgb&fm=jpg&q=85&w=1000",
    "street1": "https://images.unsplash.com/photo-1624353656309-8be1a6c457be?crop=entropy&cs=srgb&fm=jpg&q=85&w=1000",
    "street2": "https://images.unsplash.com/photo-1532332248682-206cc786359f?crop=entropy&cs=srgb&fm=jpg&q=85&w=1000",
}


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    await db.identity_users.create_index("email", unique=True)
    await db.identity_login_attempts.create_index("last", expireAfterSeconds=3600)
    await db.identity_password_resets.create_index("expires_at", expireAfterSeconds=0)
    await db.listings.create_index([("state", 1), ("audit.created_at", -1)])
    await db.listings.create_index("slug")
    await db.listings.create_index("seller_id")
    await db.offers.create_index([("buyer_id", 1), ("audit.updated_at", -1)])
    await db.offers.create_index([("seller_id", 1), ("audit.updated_at", -1)])
    await db.offers.create_index("listing_id")
    await db.offers.create_index([("status", 1), ("expires_at", 1)])
    await db.orders.create_index("offer_id", unique=True, sparse=True)
    await db.orders.create_index([("buyer_id", 1), ("audit.created_at", -1)])
    await db.orders.create_index([("seller_id", 1), ("audit.created_at", -1)])
    await db.orders.create_index("listing_id")
    await db.payments.create_index("order_id", unique=True)
    await db.payments.create_index([("status", 1), ("held", 1), ("release_at", 1)])
    await db.outbox.create_index([("processed", 1), ("created_at", 1)])


async def seed_taxonomy(db: AsyncIOMotorDatabase) -> None:
    if await db.admin_categories.count_documents({}) == 0:
        await db.admin_categories.insert_many(
            [{"_id": s, "name": n, "gender": g, "order": i}
             for i, (s, n, g) in enumerate(CATEGORIES)])
    if await db.admin_brands.count_documents({}) == 0:
        await db.admin_brands.insert_many([{"_id": b, "name": b} for b in BRANDS])


async def _get_or_create_user(db, email, password, name, role="user") -> str:
    existing = await db.identity_users.find_one({"email": email})
    if existing:
        return existing["_id"]
    user = User.register(email, hash_password(password), name)
    user.role = role
    user.activate_directly()
    await UserRepository(db).add(user)
    return user.id


async def seed_admin_and_demo(db: AsyncIOMotorDatabase) -> None:
    await _get_or_create_user(
        db, os.environ.get("ADMIN_EMAIL", "admin@archivemarket.co"),
        os.environ.get("ADMIN_PASSWORD", "Admin12345"), "Platform Admin", "admin")

    if await db.listings.count_documents({}) > 0:
        return  # demo listings already seeded

    seller = await _get_or_create_user(db, "seller@archivemarket.co", "Seller12345", "Kyiv Archive")
    svc = ListingService(db)
    demo = [
        dict(title="Nike Air Max — White / University Red", price_amount=420000,
             category="footwear", brand="Nike", gender="Men", size="42",
             color="White", condition="LIKE_NEW", material="Leather", style="Streetwear",
             images=[{"url": _IMG["sneaker1"]}, {"url": _IMG["sneaker2"]}],
             description="Worn twice. Box included. No flaws. Ships from Kyiv."),
        dict(title="New Balance 990 — Grey Suede", price_amount=380000,
             category="footwear", brand="New Balance", gender="Unisex", size="43",
             color="Grey", condition="GENTLY_USED", material="Suede",
             images=[{"url": _IMG["sneaker2"]}],
             description="Classic grey 990. Minor creasing, tons of life left."),
        dict(title="Black Leather Tote — Full Grain", price_amount=560000,
             category="bags", brand="Bottega Veneta", gender="Women", color="Black",
             condition="LIKE_NEW", material="Leather",
             images=[{"url": _IMG["bag1"]}, {"url": _IMG["bag2"]}],
             description="Structured full-grain leather tote. Barely used."),
        dict(title="Minimal Leather Handbag", price_amount=310000,
             category="bags", brand="Prada", gender="Women", color="Black",
             condition="GENTLY_USED", material="Leather",
             images=[{"url": _IMG["bag2"]}],
             description="Timeless everyday bag. Light wear on corners."),
        dict(title="Technical Shell Jacket — Signal Orange", price_amount=690000,
             category="outerwear", brand="Arc'teryx", gender="Unisex", size="M",
             color="Orange", condition="LIKE_NEW", material="Gore-Tex", season="Winter",
             images=[{"url": _IMG["street1"]}],
             description="Waterproof shell. High-vis colourway. Immaculate."),
        dict(title="Vintage Wool Overcoat", price_amount=250000,
             category="outerwear", brand="Vintage", gender="Men", size="L",
             color="Camel", condition="USED", material="Wool", season="Winter",
             images=[{"url": _IMG["street2"]}],
             description="Heavyweight wool. Beautifully aged. Timeless silhouette."),
    ]
    for d in demo:
        listing = await svc.create_draft(seller, d)
        await svc.publish(listing.id, seller)
