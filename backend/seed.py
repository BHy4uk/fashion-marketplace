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
    "af1": "https://images.unsplash.com/photo-1508125673219-7cec6bc90159?crop=entropy&cs=srgb&fm=jpg&q=85&w=1000",
    "suede": "https://images.unsplash.com/photo-1591370409347-2fd43b7842de?crop=entropy&cs=srgb&fm=jpg&q=85&w=1000",
    "sneakerlot": "https://images.unsplash.com/photo-1495555961986-6d4c1ecb7be3?crop=entropy&cs=srgb&fm=jpg&q=85&w=1000",
    "handbag": "https://images.unsplash.com/photo-1575202332411-b01fe9ace7a8?crop=entropy&cs=srgb&fm=jpg&q=85&w=1000",
    "backpack": "https://images.unsplash.com/photo-1575201046471-082b5c1a1e79?crop=entropy&cs=srgb&fm=jpg&q=85&w=1000",
    "flatlay": "https://images.unsplash.com/photo-1614676471928-2ed0ad1061a4?crop=entropy&cs=srgb&fm=jpg&q=85&w=1000",
    "belt": "https://images.unsplash.com/photo-1603805752838-aa579d77da72?crop=entropy&cs=srgb&fm=jpg&q=85&w=1000",
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
    await db.shipments.create_index("order_id", unique=True)
    await db.shipments.create_index("status")
    await db.shipments.create_index("tracking_number")
    await db.reviews.create_index([("order_id", 1), ("author_id", 1), ("recipient_id", 1)],
                                  unique=True)
    await db.reviews.create_index([("recipient_id", 1), ("status", 1), ("audit.created_at", -1)])
    await db.reviews.create_index("order_id")
    await db.conversations.create_index("dedup_key", unique=True)
    await db.conversations.create_index([("participants", 1), ("last_message_at", -1)])
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
        dict(title="Nike Air Force 1 — White", price_amount=420000,
             category="footwear", brand="Nike", gender="Unisex", size="42",
             color="White", condition="LIKE_NEW", material="Leather", style="Streetwear",
             images=[{"url": _IMG["af1"]}, {"url": _IMG["sneakerlot"]}],
             description="Worn twice. Box included. No flaws. Ships from Kyiv."),
        dict(title="Suede Court Sneakers — Brown", price_amount=380000,
             category="footwear", brand="New Balance", gender="Unisex", size="43",
             color="Brown", condition="GENTLY_USED", material="Suede",
             images=[{"url": _IMG["suede"]}],
             description="Premium suede uppers. Minor creasing, tons of life left."),
        dict(title="Grey Leather Handbag — Full Grain", price_amount=560000,
             category="bags", brand="Bottega Veneta", gender="Women", color="Grey",
             condition="LIKE_NEW", material="Leather",
             images=[{"url": _IMG["handbag"]}],
             description="Structured full-grain leather handbag. Barely used."),
        dict(title="Powder Blue Mini Backpack", price_amount=310000,
             category="backpacks", brand="Prada", gender="Women", color="Blue",
             condition="GENTLY_USED", material="Leather",
             images=[{"url": _IMG["backpack"]}],
             description="Compact everyday backpack. Light wear on corners."),
        dict(title="Autumn Knit & Trouser Set", price_amount=250000,
             category="tops", brand="Acne Studios", gender="Women", size="M",
             color="Rust", condition="USED", material="Wool", season="Autumn",
             images=[{"url": _IMG["flatlay"]}],
             description="Cosy knit paired with tailored trousers. Beautifully aged."),
        dict(title="Full-Grain Leather Belt", price_amount=90000,
             category="belts", brand="Other", gender="Unisex", color="Black",
             condition="LIKE_NEW", material="Leather",
             images=[{"url": _IMG["belt"]}],
             description="Minimal black leather belt, brushed hardware. Timeless."),
    ]
    for d in demo:
        listing = await svc.create_draft(seller, d)
        await svc.publish(listing.id, seller)
