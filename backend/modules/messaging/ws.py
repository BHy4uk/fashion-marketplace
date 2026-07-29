"""Messaging real-time transport — in-process WebSocket connection manager.

Maps user_id -> open sockets and pushes JSON frames to connected participants for
low-latency delivery. Persistence + history remain in Mongo; this layer is only the
live fan-out. NOTE (MVP): single-pod in-memory registry. Horizontal scaling needs a
Redis pub/sub (or similar) broadcast bus — tracked as technical debt.
"""
from __future__ import annotations

from collections import defaultdict


class ConnectionManager:
    def __init__(self) -> None:
        self.active: dict[str, set] = defaultdict(set)

    async def connect(self, user_id: str, websocket) -> None:
        await websocket.accept()
        self.active[user_id].add(websocket)

    def disconnect(self, user_id: str, websocket) -> None:
        self.active[user_id].discard(websocket)
        if not self.active[user_id]:
            self.active.pop(user_id, None)

    async def broadcast(self, user_ids, payload: dict) -> None:
        for uid in set(user_ids):
            for ws in list(self.active.get(uid, ())):
                try:
                    await ws.send_json(payload)
                except Exception:  # noqa: BLE001 - drop dead sockets, never stall a send
                    self.disconnect(uid, ws)


manager = ConnectionManager()
