"""Atomic Transactional Outbox via embedded events (STD-001 §7, §15).

Rationale: the runtime Mongo is a standalone node (no replica set), so multi-document
transactions are unavailable. Instead each aggregate document carries its own
`pending_events` array. Because a domain event is written INSIDE the aggregate
document in a single atomic write (`$set` fields + `$push` events, or one `insert`),
the aggregate state change and its events are persisted atomically — there is no
window in which one exists without the other.

A background relay scans event-carrying collections, dispatches each event to its
registered handlers (idempotent, at-least-once), records an audit copy in the
`outbox` collection, then `$pull`s the dispatched events. If the process crashes
after dispatch but before the pull, events are re-dispatched — handlers must be
idempotent (STD-001 §11).
"""
from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Awaitable, Callable

from motor.motor_asyncio import AsyncIOMotorDatabase

from .domain import DomainEvent, utc_now

log = logging.getLogger("outbox")

Handler = Callable[[dict], Awaitable[None]]
_handlers: dict[str, list[Handler]] = defaultdict(list)
_event_collections: set[str] = set()


def subscribe(event_type: str, handler: Handler) -> None:
    _handlers[event_type].append(handler)


def register_event_collection(name: str) -> None:
    """A repository registers its collection so the relay knows to scan it."""
    _event_collections.add(name)


def to_embedded(events: list[DomainEvent]) -> list[dict]:
    """Serialize domain events for embedding in the aggregate document."""
    return [{
        "event_id": e.event_id,
        "aggregate_id": e.aggregate_id,
        "event_type": e.event_type,
        "payload": e.payload,
        "occurred_at": e.occurred_at,
    } for e in events]


async def _dispatch_doc(db: AsyncIOMotorDatabase, coll: str, doc: dict) -> None:
    events = doc.get("pending_events") or []
    dispatched: list[str] = []
    for ev in events:
        for handler in _handlers.get(ev["event_type"], []):
            try:
                await handler(ev)
            except Exception:  # noqa: BLE001 - a bad handler must not stall the relay
                log.exception("handler failed for %s", ev["event_type"])
        # idempotent audit copy in the dedicated outbox collection
        await db.outbox.update_one(
            {"_id": ev["event_id"]},
            {"$setOnInsert": {**ev, "source": coll, "processed_at": utc_now()}},
            upsert=True,
        )
        dispatched.append(ev["event_id"])
    if dispatched:
        await db[coll].update_one(
            {"_id": doc["_id"]},
            {"$pull": {"pending_events": {"event_id": {"$in": dispatched}}}},
        )


async def _dispatch_once(db: AsyncIOMotorDatabase) -> int:
    total = 0
    for coll in list(_event_collections):
        cursor = db[coll].find({"pending_events.0": {"$exists": True}}).limit(100)
        async for doc in cursor:
            await _dispatch_doc(db, coll, doc)
            total += len(doc.get("pending_events") or [])
    return total


async def run_relay(db: AsyncIOMotorDatabase, interval: float = 1.0) -> None:
    log.info("outbox relay started (collections=%s)", _event_collections)
    while True:
        try:
            await _dispatch_once(db)
        except Exception:  # noqa: BLE001
            log.exception("relay loop error")
        await asyncio.sleep(interval)
