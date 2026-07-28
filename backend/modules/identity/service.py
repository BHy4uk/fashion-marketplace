"""Identity Application — use cases (register, login, refresh, verify, reputation).
Coordinates domain + infrastructure; enforces application-level rules like
brute-force lockout (DOMAIN-001 §11, §16)."""
from __future__ import annotations

import os
import secrets
from datetime import timedelta

from motor.motor_asyncio import AsyncIOMotorDatabase

from buildingblocks.domain import DomainError, utc_now
from buildingblocks.security import (create_access_token, create_refresh_token,
                                     decode_token, hash_password, verify_password)

from .domain import User
from .repository import UserRepository

MAX_FAILED = 5
LOCKOUT = timedelta(minutes=15)


class IdentityService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.repo = UserRepository(db)

    async def register(self, email: str, password: str, display_name: str) -> User:
        if len(password) < 8:
            raise DomainError("WEAK_PASSWORD", "Password must be at least 8 characters", 422)
        if await self.repo.by_email(email):
            raise DomainError("EMAIL_EXISTS", "Email already registered", 409)
        user = User.register(email, hash_password(password), display_name)
        # MVP: auto-activate (email verification flow is wired but not enforced).
        user.activate_directly()
        await self.repo.add(user)
        return user

    async def _check_lockout(self, identifier: str) -> None:
        rec = await self.db.identity_login_attempts.find_one({"_id": identifier})
        if rec and rec.get("count", 0) >= MAX_FAILED:
            if utc_now() - rec["last"] < LOCKOUT:
                raise DomainError("ACCOUNT_LOCKED",
                                  "Too many failed attempts. Try again later.", 429)

    async def _record_failure(self, identifier: str) -> None:
        await self.db.identity_login_attempts.update_one(
            {"_id": identifier},
            {"$inc": {"count": 1}, "$set": {"last": utc_now()}}, upsert=True)

    async def login(self, email: str, password: str, ip: str) -> User:
        identifier = f"{ip}:{email.strip().lower()}"
        await self._check_lockout(identifier)
        user = await self.repo.by_email(email)
        if not user or not verify_password(password, user.password_hash):
            await self._record_failure(identifier)
            raise DomainError("INVALID_CREDENTIALS", "Invalid email or password", 401)
        if user.state == "Suspended":
            raise DomainError("ACCOUNT_SUSPENDED", "Account suspended", 403)
        await self.db.identity_login_attempts.delete_one({"_id": identifier})
        return user

    async def get(self, user_id: str) -> User:
        user = await self.repo.by_id(user_id)
        if not user:
            raise DomainError("USER_NOT_FOUND", "User not found", 404)
        return user

    def tokens(self, user: User) -> tuple[str, str]:
        return (create_access_token(user.id, user.email, user.role),
                create_refresh_token(user.id))

    async def refresh(self, refresh_token: str) -> str:
        try:
            payload = decode_token(refresh_token)
        except Exception:
            raise DomainError("INVALID_TOKEN", "Invalid refresh token", 401)
        if payload.get("type") != "refresh":
            raise DomainError("INVALID_TOKEN", "Invalid token type", 401)
        user = await self.get(payload["sub"])
        return create_access_token(user.id, user.email, user.role)

    async def request_password_reset(self, email: str) -> None:
        user = await self.repo.by_email(email)
        if not user:
            return  # do not leak existence
        token = secrets.token_urlsafe(32)
        await self.db.identity_password_resets.insert_one({
            "_id": token, "user_id": user.id,
            "expires_at": utc_now() + timedelta(hours=1), "used": False})
        print(f"[password-reset] {email}: {os.environ.get('FRONTEND_URL','')}/reset?token={token}")

    async def reset_password(self, token: str, new_password: str) -> None:
        if len(new_password) < 8:
            raise DomainError("WEAK_PASSWORD", "Password must be at least 8 characters", 422)
        rec = await self.db.identity_password_resets.find_one({"_id": token})
        if not rec or rec["used"] or rec["expires_at"] < utc_now():
            raise DomainError("INVALID_RESET_TOKEN", "Invalid or expired token", 400)
        user = await self.get(rec["user_id"])
        user.password_hash = hash_password(new_password)
        await self.repo.save(user)
        await self.db.identity_password_resets.update_one(
            {"_id": token}, {"$set": {"used": True}})
