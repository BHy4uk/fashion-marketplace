"""Notifications Domain — Notification aggregate (DOMAIN-010).

A Notification is the INTENT to inform one recipient about a completed business event.
It owns lifecycle + read status + delivery records, but NEVER business logic and NEVER
transport (delivery adapters live in infrastructure, §2, §23). History is immutable
(INV-004). Pure domain: no framework, no DB, no providers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from buildingblocks.domain import AggregateRoot, AuditInfo, DomainError, new_id, utc_now

# Lifecycle (§6). MVP delivers immediately: Created -> Queued -> Delivered | Failed.
STATUS_TRANSITIONS = {
    "Created": {"Queued", "Canceled"},
    "Queued": {"Delivered", "Failed", "Expired"},
    "Delivered": set(),
    "Failed": {"Queued"},          # retry re-queues (same identity, INV-003/§6)
    "Expired": set(),
    "Canceled": set(),
}


@dataclass
class DeliveryAttempt:
    channel: str                    # "in_app" | "email" | ...
    status: str                     # "delivered" | "failed" | "skipped"
    at: datetime = field(default_factory=utc_now)
    detail: str | None = None


class Notification(AggregateRoot):
    def __init__(self, id, event_id, event_type, recipient_id, notif_type, title, body,
                 channels, status="Created", read=False, deliveries=None,
                 audit=None, version=0):
        super().__init__(id, version)
        self.event_id = event_id            # source business event (idempotency, INV-001/008)
        self.event_type = event_type
        self.recipient_id = recipient_id
        self.notif_type = notif_type        # NotificationType (§8)
        self.title = title
        self.body = body
        self.channels = channels            # requested delivery channels (§9)
        self.status = status
        self.read = read
        self.deliveries: list[DeliveryAttempt] = deliveries or []
        self.audit = audit or AuditInfo(created_by="system")

    @classmethod
    def create(cls, *, event_id, event_type, recipient_id, notif_type, title, body,
               channels) -> "Notification":
        if not recipient_id:
            raise DomainError("INVALID_RECIPIENT", "A notification needs a recipient", 422)  # INV-002
        if not channels:
            raise DomainError("INVALID_CHANNEL", "At least one delivery channel is required", 422)
        n = cls(id=new_id(), event_id=event_id, event_type=event_type,
                recipient_id=recipient_id, notif_type=notif_type, title=title, body=body,
                channels=channels, status="Created")
        n._raise("NotificationCreated",
                 {"notification_id": n.id, "recipient_id": recipient_id,
                  "notif_type": notif_type, "event_id": event_id})
        return n

    def _transition(self, target: str) -> None:
        if target not in STATUS_TRANSITIONS[self.status]:
            raise DomainError("INVALID_NOTIFICATION_STATE",
                              f"Cannot move notification from {self.status} to {target}", 409)
        self.status = target
        self.audit.updated_at = utc_now()

    def queue(self) -> None:
        self._transition("Queued")
        self._raise("NotificationQueued", {"notification_id": self.id})

    def record_delivery(self, channel: str, status: str, detail: str | None = None) -> None:
        self.deliveries.append(DeliveryAttempt(channel=channel, status=status, detail=detail))

    def mark_delivered(self) -> None:
        self._transition("Delivered")
        self._raise("NotificationDelivered", {"notification_id": self.id})

    def mark_failed(self, reason: str = "delivery_failed") -> None:
        self._transition("Failed")
        self._raise("NotificationFailed", {"notification_id": self.id, "reason": reason})

    def mark_read(self, user_id: str) -> bool:
        if user_id != self.recipient_id:
            raise DomainError("UNAUTHORIZED_ACCESS", "Not the notification recipient", 403)
        if self.read:
            return False                    # idempotent
        self.read = True
        self.audit.updated_at = utc_now()
        self._raise("NotificationRead", {"notification_id": self.id, "recipient_id": user_id})
        return True
