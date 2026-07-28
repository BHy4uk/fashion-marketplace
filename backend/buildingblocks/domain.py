"""Shared kernel: base building blocks for DDD aggregates.

No framework or infrastructure references live here (Clean Architecture: the
domain core is the most stable, dependency-free layer).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> datetime:
    """All timestamps are UTC (STD-003 §6)."""
    return datetime.now(timezone.utc)


def new_id() -> str:
    """Opaque, immutable, non-sequential business identifier (STD-003 §4)."""
    return uuid.uuid4().hex


@dataclass
class DomainEvent:
    """A completed business fact (STD-001). Immutable, past-tense named."""

    aggregate_id: str
    event_type: str
    payload: dict[str, Any]
    occurred_at: datetime = field(default_factory=utc_now)
    event_id: str = field(default_factory=new_id)


@dataclass
class AuditInfo:
    """Mandatory audit fields on every entity (BR-123, STD-003 §6)."""

    created_at: datetime = field(default_factory=utc_now)
    created_by: str | None = None
    updated_at: datetime = field(default_factory=utc_now)
    updated_by: str | None = None


class DomainError(Exception):
    """Deterministic business error carrying a stable code (STD-002 §14)."""

    def __init__(self, code: str, message: str, http_status: int = 400):
        self.code = code
        self.message = message
        self.http_status = http_status
        super().__init__(message)


class AggregateRoot:
    """Base aggregate root: identity, optimistic-concurrency version, and a
    collected list of domain events published only after a successful commit."""

    def __init__(self, id: str, version: int = 0):
        self.id = id
        self.version = version
        self._events: list[DomainEvent] = []

    def _raise(self, event_type: str, payload: dict[str, Any]) -> None:
        self._events.append(
            DomainEvent(aggregate_id=self.id, event_type=event_type, payload=payload)
        )

    def pull_events(self) -> list[DomainEvent]:
        events = self._events
        self._events = []
        return events
