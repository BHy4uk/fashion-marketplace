"""Email delivery abstraction + adapters (DOMAIN-010 §2/§9/§23).

The Notifications DOMAIN does not own email delivery — this infrastructure layer does.
EmailProvider is the ONLY email abstraction the application depends on; adding a
provider (SendGrid / AWS SES / Mailgun) = one new adapter, no domain change. The
active provider is chosen by EMAIL_PROVIDER config (no code change to switch).

Ships with:
  - SandboxEmailProvider: default, no network, logs the email (full local/CI testing
    of the notification + preference + delivery flow without any credentials).
  - ResendEmailProvider: production Resend API (sync SDK run off the event loop).
"""
from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod

log = logging.getLogger("notifications.email")


class EmailProvider(ABC):
    name: str

    @abstractmethod
    async def send(self, *, to: str, subject: str, html: str) -> dict:
        """Return {status: 'delivered'|'failed', id?, detail?}."""
        ...


class SandboxEmailProvider(EmailProvider):
    name = "sandbox"

    async def send(self, *, to, subject, html):
        log.info("[email:sandbox] to=%s subject=%r", to, subject)
        return {"status": "delivered", "id": "sandbox", "detail": "logged (sandbox)"}


class ResendEmailProvider(EmailProvider):
    name = "resend"

    def __init__(self, *, api_key: str, sender: str):
        self.api_key = api_key
        self.sender = sender

    async def send(self, *, to, subject, html):
        import asyncio
        import resend
        resend.api_key = self.api_key
        params = {"from": self.sender, "to": [to], "subject": subject, "html": html}
        try:
            result = await asyncio.to_thread(resend.Emails.send, params)
            return {"status": "delivered", "id": (result or {}).get("id"), "detail": "resend"}
        except Exception as exc:  # noqa: BLE001 - delivery failure must never bubble to business flow
            log.warning("[email:resend] send failed to=%s err=%s", to, exc)
            return {"status": "failed", "detail": str(exc)}


def build_email_provider() -> EmailProvider:
    choice = os.environ.get("EMAIL_PROVIDER", "sandbox").lower()
    if choice == "resend":
        key = os.environ.get("RESEND_API_KEY")
        if not key:
            raise RuntimeError("EMAIL_PROVIDER=resend but RESEND_API_KEY is not configured")
        return ResendEmailProvider(
            api_key=key, sender=os.environ.get("SENDER_EMAIL", "onboarding@resend.dev"))
    return SandboxEmailProvider()
