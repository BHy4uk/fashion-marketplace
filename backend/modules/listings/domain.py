"""Listings Domain — Listing aggregate (DOMAIN-002).

Central marketplace entity: one listing = one physical item (BR-018). Owns the
lifecycle state machine, publication rules, pricing, structured attributes,
image references, and domain events. Pure domain (no infra/framework).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from buildingblocks.domain import AggregateRoot, AuditInfo, DomainError, new_id, utc_now

# Lifecycle (DOMAIN-002 §6). Skipping states is prohibited (BR-043-style).
VALID_TRANSITIONS = {
    "Draft": {"Ready", "SoftDeleted"},
    "Ready": {"Published", "Draft", "SoftDeleted"},
    "Published": {"Reserved", "Sold", "Archived", "Draft", "SoftDeleted"},
    "Reserved": {"Sold", "Published"},          # release back if order cancelled
    "Sold": {"Archived"},                         # a sold listing never republishes (INV-004)
    "Archived": {"SoftDeleted"},
    "SoftDeleted": set(),
}

CONDITIONS = {"BRAND_NEW", "LIKE_NEW", "GENTLY_USED", "USED", "WELL_WORN"}


@dataclass
class Money:
    amount: int          # minor units (kopiykas/cents) — integer, no float money
    currency: str = "UAH"

    def __post_init__(self):
        if self.amount <= 0:
            raise DomainError("INVALID_PRICE", "Price must be greater than zero", 422)


@dataclass
class Attributes:
    brand: str = ""
    category: str = ""
    gender: str = ""
    size: str = ""
    color: str = ""
    material: str = ""
    condition: str = ""
    season: str = ""
    style: str = ""


@dataclass
class ListingImage:
    file_id: str
    url: str
    position: int = 0
    image_id: str = field(default_factory=new_id)


class Listing(AggregateRoot):
    def __init__(self, id, seller_id, title, description, price, attributes,
                 images=None, state="Draft", allow_offers=True, slug=None,
                 audit=None, version=0):
        super().__init__(id, version)
        self.seller_id = seller_id
        self.title = title
        self.description = description
        self.price = price
        self.attributes = attributes
        self.images: list[ListingImage] = images or []
        self.state = state
        self.allow_offers = allow_offers
        self.slug = slug or self._slugify(title)
        self.audit = audit or AuditInfo(created_by=seller_id)

    @staticmethod
    def _slugify(title: str) -> str:
        base = "".join(c.lower() if c.isalnum() else "-" for c in title).strip("-")
        while "--" in base:
            base = base.replace("--", "-")
        return f"{base[:60]}-{new_id()[:6]}"

    @classmethod
    def create_draft(cls, seller_id, title, description, price: Money,
                     attributes: Attributes, images: list[ListingImage],
                     allow_offers: bool = True) -> "Listing":
        if not title.strip():
            raise DomainError("MISSING_TITLE", "Title is required", 422)
        listing = cls(new_id(), seller_id, title.strip(), description.strip(),
                      price, attributes, images, allow_offers=allow_offers)
        listing._raise("ListingCreated", {"listing_id": listing.id, "seller_id": seller_id})
        return listing

    def _transition(self, target: str) -> None:
        if target not in VALID_TRANSITIONS[self.state]:
            raise DomainError("INVALID_STATE_TRANSITION",
                              f"Cannot move listing from {self.state} to {target}", 409)
        self.state = target
        self.audit.updated_at = utc_now()

    def _assert_publishable(self) -> None:
        # Publication rules (DOMAIN-002 §7, BR-012)
        missing = []
        if not self.title:
            missing.append("title")
        if not self.images:
            missing.append("at least one image")
        if not self.attributes.category:
            missing.append("category")
        if not self.attributes.condition:
            missing.append("condition")
        if self.attributes.condition and self.attributes.condition not in CONDITIONS:
            raise DomainError("INVALID_CONDITION", "Unknown condition value", 422)
        if missing:
            raise DomainError("INCOMPLETE_LISTING",
                              "Missing required fields: " + ", ".join(missing), 422)

    def publish(self, seller_active: bool) -> None:
        if not seller_active:
            raise DomainError("SELLER_INACTIVE", "Seller account is not active", 403)
        self._assert_publishable()
        if self.state == "Draft":
            self._transition("Ready")
        self._transition("Published")
        self._raise("ListingPublished", {
            "listing_id": self.id, "seller_id": self.seller_id,
            "title": self.title, "price": self.price.amount, "currency": self.price.currency,
        })

    def change_price(self, new_price: Money) -> None:
        if self.state in ("Sold", "Archived", "SoftDeleted"):
            raise DomainError("INVALID_STATE_TRANSITION", "Cannot reprice this listing", 409)
        old = self.price.amount
        self.price = new_price
        self.audit.updated_at = utc_now()
        self._raise("ListingPriceChanged", {"listing_id": self.id,
                                             "old": old, "new": new_price.amount})

    def reserve(self) -> None:
        self._transition("Reserved")
        self._raise("ListingReserved", {"listing_id": self.id})

    def release(self) -> None:
        """Reservation released (e.g. the order was canceled): Reserved → Published."""
        self._transition("Published")
        self._raise("ListingReservationReleased", {"listing_id": self.id})

    def mark_sold(self) -> None:
        self._transition("Sold")
        self._raise("ListingSold", {"listing_id": self.id})

    def archive(self) -> None:
        self._transition("Archived")
        self._raise("ListingArchived", {"listing_id": self.id})

    def soft_delete(self) -> None:
        self._transition("SoftDeleted")
        self._raise("ListingDeleted", {"listing_id": self.id})
