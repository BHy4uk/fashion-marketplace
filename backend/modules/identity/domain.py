"""Identity Domain — User aggregate (DOMAIN-001).

Pure domain: no FastAPI, no Mongo. Owns the account lifecycle state machine,
invariants, reputation, and domain events. Reputation is owned here (Q7).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from buildingblocks.domain import AggregateRoot, AuditInfo, DomainError, new_id, utc_now

# User lifecycle state machine (DOMAIN-001 §6)
VALID_TRANSITIONS = {
    "Registered": {"EmailPending", "Active"},
    "EmailPending": {"Active", "Deleted"},
    "Active": {"Suspended", "Deleted"},
    "Suspended": {"Active", "Deleted"},
    "Deleted": set(),
}

ROLES = {"user", "moderator", "admin"}


@dataclass
class Reputation:
    """Reputation inputs owned by Identity; formula is replaceable (Q7)."""

    average_rating: float = 0.0
    completed_reviews: int = 0

    def apply_review(self, rating: int) -> None:
        total = self.average_rating * self.completed_reviews + rating
        self.completed_reviews += 1
        self.average_rating = round(total / self.completed_reviews, 2)


@dataclass
class Profile:
    display_name: str
    bio: str = ""
    avatar_file_id: str | None = None
    location: str = ""


class User(AggregateRoot):
    def __init__(self, id, email, password_hash, profile, role="user",
                 state="EmailPending", email_verified=False, reputation=None,
                 audit=None, version=0):
        super().__init__(id, version)
        self.email = email
        self.password_hash = password_hash
        self.profile = profile
        self.role = role
        self.state = state
        self.email_verified = email_verified
        self.reputation = reputation or Reputation()
        self.audit = audit or AuditInfo()

    # ---- factory ----
    @classmethod
    def register(cls, email: str, password_hash: str, display_name: str) -> "User":
        email = email.strip().lower()
        if not email or "@" not in email:
            raise DomainError("INVALID_EMAIL", "A valid email is required", 422)
        if not display_name.strip():
            raise DomainError("INVALID_DISPLAY_NAME", "Display name is required", 422)
        user = cls(
            id=new_id(), email=email, password_hash=password_hash,
            profile=Profile(display_name=display_name.strip()),
            state="EmailPending",
        )
        user._raise("UserRegistered", {"user_id": user.id, "email": email})
        return user

    # ---- state transitions (never assign state directly) ----
    def _transition(self, target: str) -> None:
        if target not in VALID_TRANSITIONS[self.state]:
            raise DomainError(
                "INVALID_STATE_TRANSITION",
                f"Cannot move user from {self.state} to {target}", 409)
        self.state = target
        self.audit.updated_at = utc_now()

    def verify_email(self) -> None:
        if self.email_verified:
            return
        self.email_verified = True
        self._transition("Active")
        self._raise("EmailVerified", {"user_id": self.id})

    def activate_directly(self) -> None:
        """MVP convenience: skip email step for seeded/admin accounts."""
        self.email_verified = True
        if self.state != "Active":
            self.state = "Active"

    def suspend(self, reason: str) -> None:
        self._transition("Suspended")
        self._raise("UserSuspended", {"user_id": self.id, "reason": reason})

    def apply_review(self, rating: int) -> None:
        self.reputation.apply_review(rating)
        self._raise("ReputationUpdated", {
            "user_id": self.id,
            "average_rating": self.reputation.average_rating,
            "completed_reviews": self.reputation.completed_reviews,
        })
