"""Notifications Application — turn business events into notifications, evaluate
preferences, and deliver across channels (In-App via WebSocket + Email via provider).

Reads recipient contact ONLY via IdentityContract. In-app real-time delivery reuses
the shared WebSocket connection registry. Delivery failures NEVER propagate to the
originating business workflow (INV-005). Idempotent per (event_id, recipient) (INV-008)."""
from __future__ import annotations

import logging

from motor.motor_asyncio import AsyncIOMotorDatabase

from buildingblocks.domain import DomainError
from modules.identity.contracts import IdentityContract
from modules.messaging.ws import manager

from .domain import Notification
from .provider import build_email_provider
from .repository import COLLECTION, NotificationRepository
from .templates import specs_for

log = logging.getLogger("notifications")


class NotificationService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.repo = NotificationRepository(db)
        self.identity = IdentityContract(db)
        self.email = build_email_provider()

    # ---- event ingestion (idempotent) ----
    async def handle_event(self, event: dict) -> None:
        event_id = event.get("event_id")
        event_type = event.get("event_type")
        specs = specs_for(event_type, event.get("payload", {}))
        for spec in specs:
            await self._create_and_deliver(event_id, event_type, spec)

    async def _create_and_deliver(self, event_id, event_type, spec) -> None:
        prefs = await self.repo.get_prefs(spec["recipient_id"])
        muted = spec["notif_type"] in prefs.get("muted_types", [])
        channels = ["in_app"]
        if prefs.get("email_enabled", True) and not muted:
            channels.append("email")
        try:
            notif = Notification.create(
                event_id=event_id, event_type=event_type, recipient_id=spec["recipient_id"],
                notif_type=spec["notif_type"], title=spec["title"], body=spec["body"],
                channels=channels)
            await self.repo.add(notif)
        except DomainError as e:
            if e.code == "DUPLICATE_NOTIFICATION":
                return  # idempotent: event already produced this recipient's notification
            raise
        await self._deliver(notif)

    async def _deliver(self, notif: Notification) -> None:
        notif.queue()
        # In-App: persistent record already saved; push live if the recipient is connected.
        try:
            await manager.broadcast([notif.recipient_id], {
                "type": "notification", "id": notif.id, "notif_type": notif.notif_type,
                "title": notif.title, "body": notif.body,
                "created_at": notif.audit.created_at.isoformat()})
            notif.record_delivery("in_app", "delivered")
        except Exception as exc:  # noqa: BLE001 - never let delivery affect business flow (INV-005)
            notif.record_delivery("in_app", "failed", str(exc))
        # Email: only if requested (preferences already evaluated).
        if "email" in notif.channels:
            contact = await self.identity.contact(notif.recipient_id)
            if contact and contact.get("email"):
                res = await self.email.send(
                    to=contact["email"], subject=notif.title,
                    html=f"<p>{notif.body}</p>")
                notif.record_delivery("email", res.get("status", "failed"), res.get("detail"))
            else:
                notif.record_delivery("email", "skipped", "no recipient email")
        # A notification counts as delivered if at least the in-app record reached the user.
        if any(d.channel == "in_app" and d.status == "delivered" for d in notif.deliveries):
            notif.mark_delivered()
        else:
            notif.mark_failed("all channels failed")
        await self.repo.save(notif)

    # ---- queries ----
    async def list_for_user(self, user_id: str, limit: int = 50) -> list[dict]:
        cur = self.db[COLLECTION].find({"recipient_id": user_id}) \
            .sort("audit.created_at", -1).limit(limit)
        return [self._view(d) async for d in cur]

    async def unread_count(self, user_id: str) -> int:
        return await self.db[COLLECTION].count_documents({"recipient_id": user_id, "read": False})

    async def mark_read(self, notification_id: str, user: dict) -> None:
        notif = await self.repo.by_id(notification_id)
        if not notif:
            raise DomainError("NOTIFICATION_NOT_FOUND", "Notification not found", 404)
        if notif.mark_read(user["_id"]):
            await self.repo.save(notif)

    async def mark_all_read(self, user_id: str) -> int:
        res = await self.db[COLLECTION].update_many(
            {"recipient_id": user_id, "read": False}, {"$set": {"read": True}})
        return res.modified_count

    # ---- preferences ----
    async def get_prefs(self, user_id: str) -> dict:
        return await self.repo.get_prefs(user_id)

    async def set_prefs(self, user_id: str, prefs: dict) -> dict:
        return await self.repo.set_prefs(user_id, prefs)

    def _view(self, d: dict) -> dict:
        return {"id": d["_id"], "notif_type": d["notif_type"], "title": d["title"],
                "body": d["body"], "read": d.get("read", False),
                "status": d.get("status"),
                "created_at": d.get("audit", {}).get("created_at")}
