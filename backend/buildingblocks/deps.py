"""API-layer dependencies: current user extraction + RBAC (BR-110..113, STD-005 §5)."""
from __future__ import annotations

from fastapi import Depends, HTTPException, Request
from motor.motor_asyncio import AsyncIOMotorDatabase

from .mongo import get_db as _get_db
from .security import decode_token


def get_db() -> AsyncIOMotorDatabase:
    return _get_db()


def _extract_token(request: Request) -> str | None:
    token = request.cookies.get("access_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    return token


async def get_current_user(request: Request, db: AsyncIOMotorDatabase = Depends(get_db)) -> dict:
    token = _extract_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_token(token)
    except Exception:  # noqa: BLE001
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")
    user = await db.identity_users.find_one({"_id": payload["sub"]})
    if not user or user.get("state") == "Deleted":
        raise HTTPException(status_code=401, detail="User not found")
    if user.get("state") == "Suspended":
        raise HTTPException(status_code=403, detail="Account suspended")
    user.pop("password_hash", None)
    return user


def require_roles(*roles: str):
    async def _guard(user: dict = Depends(get_current_user)) -> dict:
        if user.get("role") not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return _guard
