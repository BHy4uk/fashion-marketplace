"""Shared-kernel value object: Money (integer minor units, no floats)."""
from __future__ import annotations

from dataclasses import dataclass

from .domain import DomainError


@dataclass(frozen=True)
class Money:
    amount: int          # minor units (kopiykas/cents)
    currency: str = "UAH"

    def __post_init__(self):
        if self.amount <= 0:
            raise DomainError("INVALID_AMOUNT", "Amount must be greater than zero", 422)

    def same_currency(self, other: "Money") -> bool:
        return self.currency == other.currency

    def as_dict(self) -> dict:
        return {"amount": self.amount, "currency": self.currency}
