"""Identity Infrastructure — UserRepository (Mongo). Persists the User aggregate
as a single document with optimistic concurrency (STD-003 §9)."""
from __future__ import annotations

from dataclasses import asdict

from motor.motor_asyncio import AsyncIOMotorDatabase

from buildingblocks.domain import DomainError
from buildingblocks.outbox import persist_events

from .domain import Profile, Reputation, User

COLLECTION = "identity_users"


def _to_doc(user: User) -> dict:
    return {
        "_id": user.id,
        "email": user.email,
        "password_hash": user.password_hash,
        "profile": asdict(user.profile),
        "role": user.role,
        "state": user.state,
        "email_verified": user.email_verified,
        "reputation": asdict(user.reputation),
        "audit": {
            "created_at": user.audit.created_at,
            "created_by": user.audit.created_by,
            "updated_at": user.audit.updated_at,
            "updated_by": user.audit.updated_by,
        },
        "version": user.version,
    }


def _from_doc(doc: dict) -> User:
    from buildingblocks.domain import AuditInfo
    a = doc.get("audit", {})
    user = User(
        id=doc["_id"], email=doc["email"], password_hash=doc["password_hash"],
        profile=Profile(**doc["profile"]), role=doc.get("role", "user"),
        state=doc.get("state", "Active"), email_verified=doc.get("email_verified", False),
        reputation=Reputation(**doc.get("reputation", {})),
        audit=AuditInfo(**a) if a else AuditInfo(), version=doc.get("version", 0),
    )
    return user


class UserRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.col = db[COLLECTION]

    async def by_id(self, user_id: str) -> User | None:
        doc = await self.col.find_one({"_id": user_id})
        return _from_doc(doc) if doc else None

    async def by_email(self, email: str) -> User | None:
        doc = await self.col.find_one({"email": email.strip().lower()})
        return _from_doc(doc) if doc else None

    async def add(self, user: User) -> None:
        doc = _to_doc(user)
        try:
            await self.col.insert_one(doc)
        except Exception as e:  # duplicate email
            if "duplicate" in str(e).lower() or "E11000" in str(e):
                raise DomainError("EMAIL_EXISTS", "Email already registered", 409)
            raise
        await persist_events(self.db, user.pull_events())

    async def save(self, user: User) -> None:
        expected = user.version
        user.version += 1
        result = await self.col.replace_one(
            {"_id": user.id, "version": expected}, _to_doc(user))
        if result.matched_count == 0:
            raise DomainError("CONCURRENCY_CONFLICT", "Stale update detected", 409)
        await persist_events(self.db, user.pull_events())
