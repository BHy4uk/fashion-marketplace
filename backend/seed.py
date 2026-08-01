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
    "si_tee":     "https://images.unsplash.com/photo-1618354691373-d851c5c3a990?auto=format&fit=crop&w=800&q=80",
    "lj":         "https://images.unsplash.com/photo-1551028719-00167b16eac5?auto=format&fit=crop&w=800&q=80",
    "sneaker":    "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=800&q=80",
    "bag":        "https://images.unsplash.com/photo-1584917865442-de89df76afd3?auto=format&fit=crop&w=800&q=80",
    "hoodie":     "https://images.unsplash.com/photo-1556821840-3a63f95609a7?auto=format&fit=crop&w=800&q=80",
    "denim":      "https://images.unsplash.com/photo-1578932750294-f5075e85f44a?auto=format&fit=crop&w=800&q=80",
    "coat":       "https://images.unsplash.com/photo-1591047139829-d91aecb6caea?auto=format&fit=crop&w=800&q=80",
    "trousers":   "https://images.unsplash.com/photo-1506629082955-511b1aa562c8?auto=format&fit=crop&w=800&q=80",
    "boots":      "https://images.unsplash.com/photo-1542013936693-884638332954?auto=format&fit=crop&w=800&q=80",
    "backpack":   "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=800&q=80",
    "belt":       "https://images.unsplash.com/photo-1594938298603-c8148c4bcd99?auto=format&fit=crop&w=800&q=80",
    "tee_white":  "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=800&q=80",
    "cap":        "https://images.unsplash.com/photo-1588850561407-ed78c282e89b?auto=format&fit=crop&w=800&q=80",
    "dress":      "https://images.unsplash.com/photo-1585487000160-6ebcfceb0d03?auto=format&fit=crop&w=800&q=80",
    "nb_sneaker": "https://images.unsplash.com/photo-1539185441755-769473a23570?auto=format&fit=crop&w=800&q=80",
    "luxury_bag": "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?auto=format&fit=crop&w=800&q=80",
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
    await db.notifications.create_index([("event_id", 1), ("recipient_id", 1)], unique=True)
    await db.notifications.create_index([("recipient_id", 1), ("read", 1)])
    await db.notifications.create_index([("recipient_id", 1), ("audit.created_at", -1)])
    await db.moderation_cases.create_index([("target_type", 1), ("target_id", 1), ("status", 1)])
    await db.moderation_cases.create_index([("status", 1), ("priority", -1), ("audit.updated_at", -1)])
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
        dict(title="Stone Island Shadow Project Bomber", price_amount=1450000,
             category="outerwear", brand="Stone Island", gender="Men", size="L",
             color="Olive", condition="LIKE_NEW", material="Nylon",
             images=[{"url": _IMG["coat"]}, {"url": _IMG["si_tee"]}],
             description="Iconic Shadow Project bomber in olive nylon. Worn 3 times. No flaws. Comes with dust bag."),
        dict(title="Maison Margiela Tabi Boots — Black", price_amount=2200000,
             category="footwear", brand="Maison Margiela", gender="Unisex", size="42",
             color="Black", condition="GENTLY_USED", material="Leather",
             images=[{"url": _IMG["boots"]}],
             description="Split-toe ankle boots in smooth black leather. Minor sole wear, upper is pristine."),
        dict(title="Acne Studios Oversized Tee — White", price_amount=320000,
             category="tops", brand="Acne Studios", gender="Unisex", size="S",
             color="White", condition="LIKE_NEW", material="Cotton",
             images=[{"url": _IMG["tee_white"]}],
             description="Relaxed-fit crew neck in heavyweight cotton. Worn once, washed on cold."),
        dict(title="Bottega Veneta Arco Tote — Sand", price_amount=3800000,
             category="bags", brand="Bottega Veneta", gender="Women",
             color="Sand", condition="GENTLY_USED", material="Leather",
             images=[{"url": _IMG["luxury_bag"]}, {"url": _IMG["bag"]}],
             description="Intrecciato weave tote in sand calfskin. Light interior wear, no exterior marks."),
        dict(title="Carhartt WIP Active Jacket — Black", price_amount=480000,
             category="outerwear", brand="Carhartt WIP", gender="Men", size="M",
             color="Black", condition="USED", material="Cotton Canvas",
             images=[{"url": _IMG["lj"]}],
             description="Classic Carhartt chore coat in black duck canvas. Worn regularly but well cared for."),
        dict(title="New Balance 990v5 — Grey", price_amount=760000,
             category="footwear", brand="New Balance", gender="Unisex", size="43",
             color="Grey", condition="LIKE_NEW", material="Suede/Mesh",
             images=[{"url": _IMG["nb_sneaker"]}, {"url": _IMG["sneaker"]}],
             description="Made in USA 990v5 in grey. Worn twice, box and extra laces included."),
        dict(title="Rick Owens Drawstring Trousers", price_amount=890000,
             category="bottoms", brand="Rick Owens", gender="Men", size="46",
             color="Black", condition="GENTLY_USED", material="Viscose",
             images=[{"url": _IMG["trousers"]}],
             description="Drape trousers with elasticated waist. Dropped crotch silhouette. Minor wear."),
        dict(title="Prada Re-Edition 2000 Bag — Black", price_amount=2900000,
             category="bags", brand="Prada", gender="Women",
             color="Black", condition="LIKE_NEW", material="Re-Nylon",
             images=[{"url": _IMG["backpack"]}, {"url": _IMG["bag"]}],
             description="Mini hobo bag in Re-Nylon with enamel triangle logo. Barely used, with dust bag."),
        dict(title="Supreme Box Logo Hoodie — Black FW22", price_amount=1100000,
             category="hoodies", brand="Supreme", gender="Unisex", size="XL",
             color="Black", condition="LIKE_NEW", material="Cotton Fleece",
             images=[{"url": _IMG["hoodie"]}],
             description="FW22 box logo pullover hoody. Worn once. No pilling or fade."),
        dict(title="Carhartt WIP Newel Denim Jacket", price_amount=340000,
             category="outerwear", brand="Carhartt WIP", gender="Unisex", size="M",
             color="Blue", condition="USED", material="Denim",
             images=[{"url": _IMG["denim"]}],
             description="Classic denim chore jacket in mid-wash. Intentional fading, great lived-in patina."),
        dict(title="Arc'teryx Atom LT Hoody — Cobalt", price_amount=1250000,
             category="outerwear", brand="Arc'teryx", gender="Men", size="S",
             color="Cobalt", condition="GENTLY_USED", material="Coreloft",
             images=[{"url": _IMG["coat"]}, {"url": _IMG["hoodie"]}],
             description="Insulated mid-layer in Coreloft. Light packable warmth. Excellent condition."),
        dict(title="Comme des Garçons PLAY Tee — Polka", price_amount=280000,
             category="tops", brand="Comme des Garçons", gender="Unisex", size="M",
             color="White", condition="GENTLY_USED", material="Cotton",
             images=[{"url": _IMG["tee_white"]}],
             description="Classic CDG Play tee with heart logo. Washed cold, no shrink. Great condition."),
    ]
    for d in demo:
        listing = await svc.create_draft(seller, d)
        await svc.publish(listing.id, seller)
