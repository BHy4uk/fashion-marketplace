"""Identity Contracts — the ONLY sanctioned way for other modules to read Identity.

No other module may touch the identity_users collection directly (DOC-005 §24)."""
from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorDatabase


class IdentityContract:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def is_active(self, user_id: str) -> bool:
        u = await self.db.identity_users.find_one({"_id": user_id}, {"state": 1})
        return bool(u and u.get("state") == "Active")

    async def summary(self, user_id: str) -> dict | None:
        u = await self.db.identity_users.find_one(
            {"_id": user_id}, {"profile.display_name": 1, "reputation": 1, "state": 1})
        if not u:
            return None
        return {"id": u["_id"], "state": u.get("state"),
                "display_name": u.get("profile", {}).get("display_name"),
                "reputation": u.get("reputation")}

    async def contact(self, user_id: str) -> dict | None:
        """Email + display name for notification delivery (Notifications module)."""
        u = await self.db.identity_users.find_one(
            {"_id": user_id}, {"email": 1, "profile.display_name": 1})
        if not u:
            return None
        return {"id": u["_id"], "email": u.get("email"),
                "display_name": u.get("profile", {}).get("display_name")}
