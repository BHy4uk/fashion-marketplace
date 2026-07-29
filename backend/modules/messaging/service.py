"""Messaging Application — start/reuse conversations, send messages (with live
WebSocket fan-out), read receipts, archive, and moderation.

Reads business context ONLY via Listing/Order contracts and user info via Identity
contract (no cross-module DB). Message send both PERSISTS (history/audit) and BROADCASTS
(real-time) to connected participants."""
from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorDatabase

from buildingblocks.domain import DomainError
from modules.identity.contracts import IdentityContract
from modules.listings.contracts import ListingContract
from modules.orders.contracts import OrderContract

from .domain import Conversation, Message, dedup_key_for
from .repository import ConversationRepository
from .ws import manager

COLLECTION = "conversations"


class MessagingService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.repo = ConversationRepository(db)
        self.listings = ListingContract(db)
        self.orders = OrderContract(db)
        self.identity = IdentityContract(db)

    # ---- start / reuse (§9) ----
    async def start(self, user: dict, context_type: str, context_id: str) -> Conversation:
        participants = await self._resolve_participants(user, context_type, context_id)
        key = dedup_key_for(context_type, context_id, participants)
        existing = await self.repo.by_dedup_key(key)
        if existing:
            return existing
        conv = Conversation.start(context_type=context_type, context_id=context_id,
                                  participants=participants, created_by=user["_id"])
        try:
            await self.repo.add(conv)
        except DomainError as e:
            if e.code == "DUPLICATE_CONVERSATION":
                return await self.repo.by_dedup_key(key)
            raise
        return conv

    async def _resolve_participants(self, user: dict, context_type: str, context_id: str) -> list[str]:
        uid = user["_id"]
        if context_type == "listing":
            snap = await self.listings.snapshot(context_id)
            if not snap:
                raise DomainError("LISTING_NOT_FOUND", "Listing not found", 404)
            if uid == snap.seller_id:
                raise DomainError("INVALID_PARTICIPANTS",
                                  "You cannot start a conversation about your own listing", 422)
            return [uid, snap.seller_id]
        if context_type == "order":
            snap = await self.orders.snapshot(context_id)
            if not snap:
                raise DomainError("ORDER_NOT_FOUND", "Order not found", 404)
            if uid not in (snap.buyer_id, snap.seller_id):
                raise DomainError("PARTICIPANT_NOT_AUTHORIZED", "Not a participant of this order", 403)
            return [snap.buyer_id, snap.seller_id]
        raise DomainError("INVALID_CONTEXT", "Unsupported conversation context", 422)

    # ---- messaging ----
    async def send_message(self, conversation_id: str, user: dict, content: str) -> dict:
        conv = await self._load_participant(conversation_id, user)
        msg = conv.post_message(user["_id"], content)
        await self.repo.save(conv)
        view = self._message_view(conv.id, msg)
        await manager.broadcast(conv.participants, {"type": "message", **view})
        return view

    async def mark_read(self, conversation_id: str, user: dict) -> None:
        conv = await self._load_participant(conversation_id, user)
        if conv.mark_read(user["_id"]):
            await self.repo.save(conv)
            await manager.broadcast(
                conv.participants,
                {"type": "read", "conversation_id": conv.id, "user_id": user["_id"]})

    async def archive(self, conversation_id: str, user: dict) -> Conversation:
        conv = await self._load_participant(conversation_id, user)
        conv.archive(user["_id"])
        await self.repo.save(conv)
        return conv

    # ---- moderation (moderator/admin) ----
    async def close(self, conversation_id: str, user: dict) -> Conversation:
        conv = await self.repo.by_id(conversation_id)
        if not conv:
            raise DomainError("CONVERSATION_NOT_FOUND", "Conversation not found", 404)
        conv.close(actor=user["_id"])
        await self.repo.save(conv)
        await manager.broadcast(conv.participants,
                                {"type": "closed", "conversation_id": conv.id})
        return conv

    async def hide_message(self, conversation_id: str, message_id: str, user: dict) -> Conversation:
        conv = await self.repo.by_id(conversation_id)
        if not conv:
            raise DomainError("CONVERSATION_NOT_FOUND", "Conversation not found", 404)
        conv.hide_message(message_id, actor=user["_id"])
        await self.repo.save(conv)
        return conv

    # ---- queries ----
    async def list_for_user(self, user: dict) -> list[dict]:
        uid = user["_id"]
        cur = self.db[COLLECTION].find({"participants": uid}).sort("last_message_at", -1)
        out = []
        async for d in cur:
            conv = self._doc_to_conv(d)
            other_ids = [p for p in conv.participants if p != uid]
            other = await self.identity.summary(other_ids[0]) if other_ids else None
            last = conv.messages[-1] if conv.messages else None
            out.append({
                "id": conv.id, "context_type": conv.context_type,
                "context_id": conv.context_id, "status": conv.status,
                "counterparty_id": other_ids[0] if other_ids else None,
                "counterparty_name": (other or {}).get("display_name"),
                "last_message": (None if not last or last.hidden else last.content),
                "last_message_at": conv.last_message_at,
                "unread": conv.unread_count(uid),
            })
        return out

    async def messages(self, conversation_id: str, user: dict) -> dict:
        conv = await self._load_participant(conversation_id, user)
        is_staff = user.get("role") in ("admin", "moderator")
        # reading marks the thread read for this participant
        if conv.mark_read(user["_id"]):
            await self.repo.save(conv)
            await manager.broadcast(
                conv.participants,
                {"type": "read", "conversation_id": conv.id, "user_id": user["_id"]})
        msgs = [self._message_view(conv.id, m) for m in conv.messages
                if is_staff or not m.hidden]
        others = [p for p in conv.participants if p != user["_id"]]
        other = await self.identity.summary(others[0]) if others else None
        return {"id": conv.id, "context_type": conv.context_type,
                "context_id": conv.context_id, "status": conv.status,
                "participants": conv.participants,
                "counterparty_name": (other or {}).get("display_name"),
                "messages": msgs}

    # ---- helpers ----
    async def _load_participant(self, conversation_id: str, user: dict) -> Conversation:
        conv = await self.repo.by_id(conversation_id)
        if not conv:
            raise DomainError("CONVERSATION_NOT_FOUND", "Conversation not found", 404)
        if user.get("role") not in ("admin", "moderator") and user["_id"] not in conv.participants:
            raise DomainError("PARTICIPANT_NOT_AUTHORIZED", "Not a participant of this conversation", 403)
        return conv

    def _doc_to_conv(self, d: dict) -> Conversation:
        from .repository import _from_doc
        return _from_doc(d)

    def _message_view(self, conversation_id: str, m: Message) -> dict:
        return {"conversation_id": conversation_id, "message_id": m.message_id,
                "author_id": m.author_id,
                "content": ("[hidden by moderator]" if m.hidden else m.content),
                "hidden": m.hidden,
                "created_at": m.created_at.isoformat() if m.created_at else None}
