"""Reviews Domain — Review aggregate (DOMAIN-008).

A Review is post-transaction feedback tied to exactly ONE completed Order, with one
Author and one Recipient (both order participants). Published reviews and their
comments/responses are IMMUTABLE (INV-006, §9, §10). The aggregate provides
reputation INPUTS via events; it never calculates platform reputation (§11, §22).
Pure domain: no framework, no DB.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from buildingblocks.domain import AggregateRoot, AuditInfo, DomainError, new_id, utc_now

RATING_MIN, RATING_MAX = 1, 5
COMMENT_MAX = 2000

# Lifecycle (DOMAIN-008 §6, §12). We publish immediately (single-step, Grailed-style),
# so a Review is born Published. Moderators may Hide/Remove; Hidden may be restored.
VALID_TRANSITIONS = {
    "Published": {"Hidden", "Removed"},
    "Hidden": {"Published", "Removed"},
    "Removed": set(),          # terminal (kept for audit, INV-007)
}


@dataclass(frozen=True)
class ReviewResponse:
    """Recipient's single, immutable response to a Review (§10)."""
    author_id: str
    comment: str
    at: datetime = field(default_factory=utc_now)
    response_id: str = field(default_factory=new_id)


class Review(AggregateRoot):
    def __init__(self, id, order_id, author_id, recipient_id, rating, comment=None,
                 status="Published", response=None, audit=None, version=0):
        super().__init__(id, version)
        self.order_id = order_id
        self.author_id = author_id
        self.recipient_id = recipient_id
        self.rating = rating
        self.comment = comment
        self.status = status
        self.response: ReviewResponse | None = response
        self.audit = audit or AuditInfo(created_by=author_id)

    @classmethod
    def create(cls, *, order_id, author_id, recipient_id, rating, comment=None) -> "Review":
        if not isinstance(rating, int) or not (RATING_MIN <= rating <= RATING_MAX):
            raise DomainError("INVALID_RATING", "Rating must be an integer 1–5", 422)
        if author_id == recipient_id:
            raise DomainError("UNAUTHORIZED_REVIEWER", "Author and recipient must differ", 422)
        comment = (comment or "").strip() or None
        if comment and len(comment) > COMMENT_MAX:
            raise DomainError("COMMENT_TOO_LONG", f"Comment must be at most {COMMENT_MAX} characters", 422)
        r = cls(id=new_id(), order_id=order_id, author_id=author_id,
                recipient_id=recipient_id, rating=rating, comment=comment, status="Published")
        # ReviewPublished carries the reputation input; Identity reacts to it (§11).
        r._raise("ReviewPublished", r._payload(rating=rating))
        return r

    def _transition(self, target: str) -> None:
        if target not in VALID_TRANSITIONS[self.status]:
            raise DomainError("INVALID_REVIEW_STATE",
                              f"Cannot move review from {self.status} to {target}", 409)
        self.status = target
        self.audit.updated_at = utc_now()

    def _payload(self, **extra) -> dict:
        return {"review_id": self.id, "order_id": self.order_id,
                "author_id": self.author_id, "recipient_id": self.recipient_id, **extra}

    def add_response(self, author_id: str, comment: str) -> None:
        if self.status == "Removed":
            raise DomainError("REVIEW_REMOVED", "Cannot respond to a removed review", 409)
        if self.response is not None:
            raise DomainError("RESPONSE_EXISTS", "A response already exists for this review", 409)
        comment = (comment or "").strip()
        if not comment:
            raise DomainError("INVALID_COMMENT", "Response comment is required", 422)
        if len(comment) > COMMENT_MAX:
            raise DomainError("COMMENT_TOO_LONG", f"Response must be at most {COMMENT_MAX} characters", 422)
        self.response = ReviewResponse(author_id=author_id, comment=comment)
        self._raise("ReviewResponseCreated", self._payload(response_author=author_id))

    def hide(self, actor: str) -> None:
        self._transition("Hidden")
        self._raise("ReviewHidden", self._payload(actor=actor))

    def unhide(self, actor: str) -> None:
        self._transition("Published")
        self._raise("ReviewUnhidden", self._payload(actor=actor))

    def remove(self, actor: str, reason: str = "moderation") -> None:
        self._transition("Removed")
        self._raise("ReviewRemoved", self._payload(actor=actor, reason=reason))
