"""Transactional Outbox + in-process event bus (STD-001 §7, §15).

Events raised by an aggregate are persisted to the `outbox` collection in the same
save operation, then a background relay dispatches them to registered handlers.
Handlers must be idempotent (STD-001 §11); dispatch is at-least-once.
"""
from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from dataclasses import asdict
from typing import Awaitable, Callable

from motor.motor_asyncio import AsyncIOMotorDatabase

from .domain import DomainEvent, utc_now

log = logging.getLogger("outbox")

Handler = Callable[[dict], Awaitable[None]]
_handlers: dict[str, list[Handler]] = defaultdict(list)


def subscribe(event_type: str, handler: Handler) -> None:
    _handlers[event_type].append(handler)


async def persist_events(db: AsyncIOMotorDatabase, events: list[DomainEvent]) -> None:
    if not events:
        return
    docs = []
    for e in events:
        d = asdict(e)
        d["_id"] = e.event_id
        d["processed"] = False
        d["created_at"] = e.occurred_at
        docs.append(d)
    await db.outbox.insert_many(docs)


async def _dispatch_once(db: AsyncIOMotorDatabase) -> int:
    cursor = db.outbox.find({"processed": False}).sort("created_at", 1).limit(50)
    count = 0
    async for doc in cursor:
        for handler in _handlers.get(doc["event_type"], []):
            try:
                await handler(doc)
            except Exception:  # noqa: BLE001 - handler failures must not stop the relay
                log.exception("handler failed for %s", doc["event_type"])
        await db.outbox.update_one(
            {"_id": doc["_id"]}, {"$set": {"processed": True, "processed_at": utc_now()}}
        )
        count += 1
    return count


async def run_relay(db: AsyncIOMotorDatabase, interval: float = 2.0) -> None:
    log.info("outbox relay started")
    while True:
        try:
            await _dispatch_once(db)
        except Exception:  # noqa: BLE001
            log.exception("relay loop error")
        await asyncio.sleep(interval)
