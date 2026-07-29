"""Identity API — thin controllers under /api/auth and /api/users. No business logic."""
from __future__ import annotations

import os

from fastapi import APIRouter, Depends, Request, Response
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, EmailStr, Field

from buildingblocks.deps import get_current_user, get_db
from buildingblocks.security import ACCESS_TTL, REFRESH_TTL

from .domain import User
from .service import IdentityService

auth_router = APIRouter(prefix="/api/auth", tags=["auth"])
users_router = APIRouter(prefix="/api/users", tags=["users"])


class RegisterReq(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: str = Field(min_length=1, max_length=60)


class LoginReq(BaseModel):
    email: EmailStr
    password: str


class ForgotReq(BaseModel):
    email: EmailStr


class ResetReq(BaseModel):
    token: str
    password: str = Field(min_length=8)


def _public(user: User | dict) -> dict:
    if isinstance(user, dict):
        return {"id": user["_id"], "email": user["email"], "role": user.get("role", "user"),
                "state": user.get("state"), "email_verified": user.get("email_verified"),
                "profile": user.get("profile"), "reputation": user.get("reputation")}
    return {"id": user.id, "email": user.email, "role": user.role, "state": user.state,
            "email_verified": user.email_verified,
            "profile": {"display_name": user.profile.display_name, "bio": user.profile.bio,
                        "avatar_file_id": user.profile.avatar_file_id,
                        "location": user.profile.location},
            "reputation": {"average_rating": user.reputation.average_rating,
                           "completed_reviews": user.reputation.completed_reviews}}


def _cookie_options() -> dict:
    frontend_url = (os.environ.get("FRONTEND_URL") or "").strip().lower()
    local_hosts = ("http://localhost", "http://127.0.0.1")
    if frontend_url.startswith(local_hosts):
        return {"secure": False, "samesite": "lax"}
    return {"secure": True, "samesite": "none"}


def _set_cookies(resp: Response, access: str, refresh: str) -> None:
    options = _cookie_options()
    resp.set_cookie("access_token", access, httponly=True,
                    max_age=int(ACCESS_TTL.total_seconds()), path="/", **options)
    resp.set_cookie("refresh_token", refresh, httponly=True,
                    max_age=int(REFRESH_TTL.total_seconds()), path="/", **options)


@auth_router.post("/register")
async def register(req: RegisterReq, response: Response, db: AsyncIOMotorDatabase = Depends(get_db)):
    svc = IdentityService(db)
    user = await svc.register(req.email, req.password, req.display_name)
    access, refresh = svc.tokens(user)
    _set_cookies(response, access, refresh)
    return {"user": _public(user), "access_token": access}


@auth_router.post("/login")
async def login(req: LoginReq, request: Request, response: Response,
                db: AsyncIOMotorDatabase = Depends(get_db)):
    svc = IdentityService(db)
    ip = request.client.host if request.client else "unknown"
    user = await svc.login(req.email, req.password, ip)
    access, refresh = svc.tokens(user)
    _set_cookies(response, access, refresh)
    return {"user": _public(user), "access_token": access}


@auth_router.post("/logout")
async def logout(response: Response, user: dict = Depends(get_current_user)):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return {"ok": True}


@auth_router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return {"user": _public(user)}


@auth_router.post("/refresh")
async def refresh(request: Request, response: Response, db: AsyncIOMotorDatabase = Depends(get_db)):
    from fastapi import HTTPException
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token")
    access = await IdentityService(db).refresh(token)
    response.set_cookie("access_token", access, httponly=True,
                        max_age=int(ACCESS_TTL.total_seconds()), path="/", **_cookie_options())
    return {"access_token": access}


@auth_router.post("/forgot-password")
async def forgot(req: ForgotReq, db: AsyncIOMotorDatabase = Depends(get_db)):
    await IdentityService(db).request_password_reset(req.email)
    return {"ok": True}


@auth_router.post("/reset-password")
async def reset(req: ResetReq, db: AsyncIOMotorDatabase = Depends(get_db)):
    await IdentityService(db).reset_password(req.token, req.password)
    return {"ok": True}


@users_router.get("/{user_id}")
async def public_profile(user_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    user = await IdentityService(db).get(user_id)
    pub = _public(user)
    pub.pop("email", None)  # public profile hides sensitive info (DOMAIN-001 §15)
    return {"user": pub}
