"""Messaging API — /api/conversations (REST) + /api/ws/messages (WebSocket).

REST covers start/list/history/send/read/archive and moderator hide/close.
The WebSocket delivers messages and read receipts in real time; it authenticates via
the httpOnly access_token cookie (or ?token= fallback) and also accepts client-sent
send/read/ping frames."""
from __future__ import annotations

from fastapi import (APIRouter, Depends, WebSocket, WebSocketDisconnect)
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

from buildingblocks.deps import get_current_user, get_db, require_roles
from buildingblocks.domain import DomainError
from buildingblocks.mongo import get_db as _get_db
from buildingblocks.security import decode_token

from .service import MessagingService
from .ws import manager

router = APIRouter(prefix="/api/conversations", tags=["messaging"])
ws_router = APIRouter(tags=["messaging"])


class StartReq(BaseModel):
    context_type: str = Field(pattern="^(listing|order)$")
    context_id: str


class SendReq(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


@router.post("")
async def start(req: StartReq, user: dict = Depends(get_current_user),
                db: AsyncIOMotorDatabase = Depends(get_db)):
    c = await MessagingService(db).start(user, req.context_type, req.context_id)
    return {"conversation_id": c.id, "status": c.status}


@router.get("")
async def my_conversations(user: dict = Depends(get_current_user),
                           db: AsyncIOMotorDatabase = Depends(get_db)):
    return {"items": await MessagingService(db).list_for_user(user)}


@router.get("/{conversation_id}/messages")
async def history(conversation_id: str, user: dict = Depends(get_current_user),
                  db: AsyncIOMotorDatabase = Depends(get_db)):
    return await MessagingService(db).messages(conversation_id, user)


@router.post("/{conversation_id}/messages")
async def send(conversation_id: str, req: SendReq,
               user: dict = Depends(get_current_user),
               db: AsyncIOMotorDatabase = Depends(get_db)):
    return await MessagingService(db).send_message(conversation_id, user, req.content)


@router.post("/{conversation_id}/read")
async def read(conversation_id: str, user: dict = Depends(get_current_user),
               db: AsyncIOMotorDatabase = Depends(get_db)):
    await MessagingService(db).mark_read(conversation_id, user)
    return {"ok": True}


@router.post("/{conversation_id}/archive")
async def archive(conversation_id: str, user: dict = Depends(get_current_user),
                  db: AsyncIOMotorDatabase = Depends(get_db)):
    c = await MessagingService(db).archive(conversation_id, user)
    return {"conversation_id": c.id, "status": c.status}


@router.post("/{conversation_id}/close")
async def close(conversation_id: str, user: dict = Depends(require_roles("moderator", "admin")),
                db: AsyncIOMotorDatabase = Depends(get_db)):
    c = await MessagingService(db).close(conversation_id, user)
    return {"conversation_id": c.id, "status": c.status}


@router.post("/{conversation_id}/messages/{message_id}/hide")
async def hide(conversation_id: str, message_id: str,
               user: dict = Depends(require_roles("moderator", "admin")),
               db: AsyncIOMotorDatabase = Depends(get_db)):
    await MessagingService(db).hide_message(conversation_id, message_id, user)
    return {"ok": True}


@ws_router.websocket("/api/ws/messages")
async def ws_messages(websocket: WebSocket):
    token = websocket.cookies.get("access_token") or websocket.query_params.get("token")
    user_id = None
    if token:
        try:
            payload = decode_token(token)
            if payload.get("type") == "access":
                user_id = payload["sub"]
        except Exception:  # noqa: BLE001
            user_id = None
    if not user_id:
        await websocket.close(code=1008)
        return
    await manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            kind = data.get("type")
            if kind == "ping":
                await websocket.send_json({"type": "pong"})
                continue
            cid = data.get("conversation_id")
            if not cid:
                continue
            svc = MessagingService(_get_db())
            actor = {"_id": user_id, "role": "user"}
            try:
                if kind == "send":
                    await svc.send_message(cid, actor, data.get("content", ""))
                elif kind == "read":
                    await svc.mark_read(cid, actor)
            except DomainError as e:
                await websocket.send_json({"type": "error", "code": e.code, "detail": e.message})
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
    except Exception:  # noqa: BLE001
        manager.disconnect(user_id, websocket)
