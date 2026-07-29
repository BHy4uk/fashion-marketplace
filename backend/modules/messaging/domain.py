"""Messaging Domain — Conversation aggregate (DOMAIN-009).

A Conversation is the communication context between >=2 participants, tied to exactly
one business object (Listing or Order for MVP; §4, §9). It owns messages, per-participant
read state, and archive/close lifecycle. Messages are IMMUTABLE and never deleted
(INV-004, INV-005) — moderation only hides. Pure domain: no framework, no DB, no sockets.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from buildingblocks.domain import AggregateRoot, AuditInfo, DomainError, new_id, utc_now

CONTENT_MAX = 4000
VALID_CONTEXTS = {"listing", "order"}

# Conversation lifecycle (§7). Created folds into Active on start; Closed is read-only.
STATUS_TRANSITIONS = {
    "Active": {"Archived", "Closed"},
    "Archived": {"Active", "Closed"},
    "Closed": set(),
}


@dataclass(frozen=True)
class Message:
    """One immutable communication event (INV-004, INV-007)."""
    author_id: str
    content: str
    message_id: str = field(default_factory=new_id)
    hidden: bool = False
    created_at: datetime = field(default_factory=utc_now)


@dataclass
class ReadReceipt:
    """Per-participant read state (§11). Never modifies message content."""
    user_id: str
    last_read_at: datetime
    last_read_message_id: str | None = None


def dedup_key_for(context_type: str, context_id: str, participants: list[str]) -> str:
    return f"{context_type}:{context_id}:{'|'.join(sorted(set(participants)))}"


class Conversation(AggregateRoot):
    def __init__(self, id, context_type, context_id, participants, dedup_key,
                 status="Active", messages=None, read_receipts=None,
                 last_message_at=None, audit=None, version=0):
        super().__init__(id, version)
        self.context_type = context_type
        self.context_id = context_id
        self.participants: list[str] = participants
        self.dedup_key = dedup_key
        self.status = status
        self.messages: list[Message] = messages or []
        self.read_receipts: dict[str, ReadReceipt] = read_receipts or {}
        self.last_message_at = last_message_at
        self.audit = audit or AuditInfo()

    @classmethod
    def start(cls, *, context_type, context_id, participants, created_by) -> "Conversation":
        if context_type not in VALID_CONTEXTS:
            raise DomainError("INVALID_CONTEXT", "Unsupported conversation context", 422)
        parts = sorted(set(participants))
        if len(parts) < 2:                       # INV-002, INV-008
            raise DomainError("INVALID_PARTICIPANTS",
                              "A conversation needs at least two distinct participants", 422)
        c = cls(id=new_id(), context_type=context_type, context_id=context_id,
                participants=parts, dedup_key=dedup_key_for(context_type, context_id, parts),
                status="Active", audit=AuditInfo(created_by=created_by))
        c._raise("ConversationCreated",
                 {"conversation_id": c.id, "context_type": context_type,
                  "context_id": context_id, "participants": parts})
        return c

    # ---- guards ----
    def _require_participant(self, user_id: str) -> None:
        if user_id not in self.participants:      # INV-003
            raise DomainError("PARTICIPANT_NOT_AUTHORIZED",
                              "Not a participant of this conversation", 403)

    # ---- messages ----
    def post_message(self, author_id: str, content: str) -> Message:
        self._require_participant(author_id)
        if self.status == "Closed":
            raise DomainError("CONVERSATION_CLOSED", "This conversation is closed", 409)
        content = (content or "").strip()
        if not content:
            raise DomainError("EMPTY_MESSAGE", "Message content is required", 422)
        if len(content) > CONTENT_MAX:
            raise DomainError("MESSAGE_TOO_LONG",
                              f"Message must be at most {CONTENT_MAX} characters", 422)
        if self.status == "Archived":
            self.status = "Active"               # a new message reactivates the thread
        msg = Message(author_id=author_id, content=content)
        self.messages.append(msg)
        self.last_message_at = msg.created_at
        self.read_receipts[author_id] = ReadReceipt(author_id, msg.created_at, msg.message_id)
        self._raise("MessageSent",
                    {"conversation_id": self.id, "message_id": msg.message_id,
                     "author_id": author_id, "participants": self.participants})
        return msg

    def mark_read(self, user_id: str) -> bool:
        """Idempotent (§19): re-reading the latest message is a no-op."""
        self._require_participant(user_id)
        if not self.messages:
            return False
        last = self.messages[-1]
        existing = self.read_receipts.get(user_id)
        if existing and existing.last_read_message_id == last.message_id:
            return False
        self.read_receipts[user_id] = ReadReceipt(user_id, utc_now(), last.message_id)
        self._raise("MessageRead",
                    {"conversation_id": self.id, "user_id": user_id,
                     "message_id": last.message_id})
        return True

    def unread_count(self, user_id: str) -> int:
        rr = self.read_receipts.get(user_id)
        last_read = rr.last_read_message_id if rr else None
        seen = last_read is None
        count = 0
        for m in self.messages:
            if not seen:
                if m.message_id == last_read:
                    seen = True
                continue
            if m.author_id != user_id and not m.hidden:
                count += 1
        return count

    # ---- lifecycle ----
    def _transition(self, target: str) -> None:
        if target not in STATUS_TRANSITIONS[self.status]:
            raise DomainError("INVALID_CONVERSATION_STATE",
                              f"Cannot move conversation from {self.status} to {target}", 409)
        self.status = target
        self.audit.updated_at = utc_now()

    def archive(self, user_id: str) -> None:
        self._require_participant(user_id)
        self._transition("Archived")
        self._raise("ConversationArchived", {"conversation_id": self.id, "user_id": user_id})

    def close(self, actor: str) -> None:
        self._transition("Closed")
        self._raise("ConversationClosed", {"conversation_id": self.id, "actor": actor})

    # ---- moderation (§12) ----
    def hide_message(self, message_id: str, actor: str) -> None:
        for i, m in enumerate(self.messages):
            if m.message_id == message_id:
                if m.hidden:
                    return
                self.messages[i] = Message(author_id=m.author_id, content=m.content,
                                           message_id=m.message_id, hidden=True,
                                           created_at=m.created_at)
                self.audit.updated_at = utc_now()
                self._raise("MessageHidden",
                            {"conversation_id": self.id, "message_id": message_id, "actor": actor})
                return
        raise DomainError("MESSAGE_NOT_FOUND", "Message not found", 404)
