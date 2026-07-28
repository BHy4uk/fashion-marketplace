"""Payment provider abstraction + adapters (DOC-000 §13, DOMAIN-006).

IPaymentProvider is the port; adapters are swappable via PAYMENT_PROVIDER config
without touching the Payments domain/application. Ships with:
  - SandboxProvider: deterministic, no external calls (default; enables full local
    testing of the escrow lifecycle without credentials).
  - LiqPayProvider: real PrivatBank/LiqPay integration (needs public/private keys).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from abc import ABC, abstractmethod
from typing import Any

import httpx


class IPaymentProvider(ABC):
    name: str

    @abstractmethod
    async def create_checkout(self, *, order_id: str, amount: str, currency: str,
                              description: str, hold: bool = True) -> dict[str, Any]: ...

    @abstractmethod
    async def verify_callback(self, data: str, signature: str) -> dict[str, Any]: ...

    @abstractmethod
    async def capture_hold(self, order_id: str, amount: str | None = None) -> dict[str, Any]: ...

    @abstractmethod
    async def void_hold(self, order_id: str) -> dict[str, Any]: ...

    @abstractmethod
    async def refund(self, order_id: str, amount: str | None = None) -> dict[str, Any]: ...


class SandboxProvider(IPaymentProvider):
    """No-network provider. Authorization + capture succeed deterministically so the
    escrow state machine and cross-domain choreography can be validated end-to-end."""
    name = "sandbox"

    async def create_checkout(self, *, order_id, amount, currency, description, hold=True):
        return {"provider": "sandbox", "auto_settle": True, "order_id": order_id,
                "checkout_url": None, "status": "hold_placed" if hold else "success"}

    async def verify_callback(self, data, signature):
        return json.loads(base64.b64decode(data).decode("utf-8"))

    async def capture_hold(self, order_id, amount=None):
        return {"provider": "sandbox", "status": "success", "order_id": order_id}

    async def void_hold(self, order_id):
        return {"provider": "sandbox", "status": "reversed", "order_id": order_id}

    async def refund(self, order_id, amount=None):
        return {"provider": "sandbox", "status": "reversed", "order_id": order_id}


class LiqPayProvider(IPaymentProvider):
    """LiqPay adapter (playbook-compliant): base64(JSON) data + sha3-256 signature."""
    name = "liqpay"
    API_URL = "https://www.liqpay.ua/api/request"
    CHECKOUT_URL = "https://www.liqpay.ua/api/3/checkout"

    def __init__(self, public_key: str, private_key: str, server_url: str, sandbox: bool = True):
        self.public_key = public_key
        self.private_key = private_key
        self.server_url = server_url
        self.sandbox = sandbox

    def _encode(self, payload: dict) -> str:
        raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode()
        return base64.b64encode(raw).decode("ascii")

    def _sign(self, data: str) -> str:
        msg = f"{self.private_key}{data}{self.private_key}".encode()
        return base64.b64encode(hashlib.sha3_256(msg).digest()).decode("ascii")

    async def create_checkout(self, *, order_id, amount, currency, description, hold=True):
        payload = {"public_key": self.public_key, "version": 3,
                   "action": "hold" if hold else "pay", "amount": amount,
                   "currency": currency, "description": description, "order_id": order_id,
                   "server_url": self.server_url, "sandbox": 1 if self.sandbox else 0}
        data = self._encode(payload)
        return {"provider": "liqpay", "auto_settle": False,
                "checkout_url": self.CHECKOUT_URL, "data": data, "signature": self._sign(data)}

    async def verify_callback(self, data, signature):
        if not hmac.compare_digest(self._sign(data), signature):
            raise ValueError("Invalid LiqPay signature")
        return json.loads(base64.b64decode(data).decode("utf-8"))

    async def _request(self, payload: dict) -> dict:
        data = self._encode({**payload, "public_key": self.public_key, "version": 3,
                             "sandbox": 1 if self.sandbox else 0})
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.post(self.API_URL, data={"data": data, "signature": self._sign(data)})
            r.raise_for_status()
            return r.json()

    async def capture_hold(self, order_id, amount=None):
        p = {"action": "hold_completion", "order_id": order_id}
        if amount:
            p["amount"] = amount
        return await self._request(p)

    async def void_hold(self, order_id):
        return await self._request({"action": "refund", "order_id": order_id})

    async def refund(self, order_id, amount=None):
        p = {"action": "refund", "order_id": order_id}
        if amount:
            p["amount"] = amount
        return await self._request(p)


def build_provider() -> IPaymentProvider:
    choice = os.environ.get("PAYMENT_PROVIDER", "sandbox").lower()
    if choice == "liqpay":
        pub, priv = os.environ.get("LIQPAY_PUBLIC_KEY"), os.environ.get("LIQPAY_PRIVATE_KEY")
        if not pub or not priv:
            raise RuntimeError("PAYMENT_PROVIDER=liqpay but LIQPAY keys are not configured")
        server_url = f"{os.environ.get('BACKEND_PUBLIC_URL', '')}/api/payments/webhook/liqpay"
        sandbox = os.environ.get("LIQPAY_SANDBOX", "true").lower() == "true"
        return LiqPayProvider(pub, priv, server_url, sandbox)
    return SandboxProvider()
