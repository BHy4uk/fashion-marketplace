"""Notifications (Phase 10, DOMAIN-010) — aggregate lifecycle, email provider
abstraction, templates, event-sourced creation, idempotency, preferences, read
status, and real-time in-app (WebSocket) delivery.
Requires EMAIL_PROVIDER=sandbox / PAYMENT_PROVIDER=sandbox / SHIPPING_PROVIDER=sandbox."""
from __future__ import annotations

import asyncio
import json
import os
import time
import uuid

import pytest
import requests

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"
WS_URL = BASE_URL.replace("http", "ws", 1) + "/api/ws/messages"

SELLER = {"email": "seller@archivemarket.co", "password": "Seller12345"}


def _register(prefix="ntf"):
    sess = requests.Session()
    uid = uuid.uuid4().hex[:8]
    r = sess.post(f"{API}/auth/register", json={
        "email": f"TEST_{prefix}_{uid}@example.com",
        "password": "Password12345", "display_name": f"{prefix}_{uid}"})
    assert r.status_code in (200, 201), r.text
    return sess, r.json()["user"], r.json().get("access_token")


def _login(creds):
    sess = requests.Session()
    r = sess.post(f"{API}/auth/login", json=creds)
    assert r.status_code == 200, r.text
    return sess, r.json()["user"], r.json().get("access_token")


def _fresh_listing(seller_sess):
    payload = {"title": f"TEST_ntf_{uuid.uuid4().hex[:6]}", "description": "test",
               "price_amount": 300000, "currency": "UAH", "brand": "Nike",
               "category": "footwear", "gender": "Men", "size": "42", "color": "White",
               "material": "Leather", "condition": "LIKE_NEW",
               "images": [{"url": "https://example.com/x.jpg"}], "allow_offers": True}
    lid = seller_sess.post(f"{API}/listings", json=payload).json()["listing_id"]
    seller_sess.post(f"{API}/listings/{lid}/publish")
    return lid


def _poll_notifications(sess, predicate, timeout=12.0):
    end = time.time() + timeout
    while time.time() < end:
        items = sess.get(f"{API}/notifications").json()["items"]
        match = [n for n in items if predicate(n)]
        if match:
            return match
        time.sleep(0.5)
    return []


@pytest.fixture(scope="module")
def seller():
    return _login(SELLER)


@pytest.fixture
def buyer():
    return _register("ntf")


# ---------- Domain ----------
class TestNotificationDomain:
    def _make(self):
        from modules.notifications.domain import Notification
        return Notification.create(event_id="e1", event_type="MessageSent",
                                   recipient_id="u1", notif_type="NewMessage",
                                   title="t", body="b", channels=["in_app", "email"])

    def test_lifecycle(self):
        n = self._make()
        assert n.status == "Created"
        assert [e.event_type for e in n.pull_events()] == ["NotificationCreated"]
        n.queue(); assert n.status == "Queued"
        n.record_delivery("in_app", "delivered")
        n.mark_delivered(); assert n.status == "Delivered"

    def test_requires_recipient_and_channel(self):
        from buildingblocks.domain import DomainError
        from modules.notifications.domain import Notification
        with pytest.raises(DomainError):
            Notification.create(event_id="e", event_type="x", recipient_id="",
                                notif_type="t", title="a", body="b", channels=["in_app"])
        with pytest.raises(DomainError):
            Notification.create(event_id="e", event_type="x", recipient_id="u",
                                notif_type="t", title="a", body="b", channels=[])

    def test_mark_read_authz_and_idempotent(self):
        from buildingblocks.domain import DomainError
        n = self._make(); n.pull_events()
        with pytest.raises(DomainError) as e:
            n.mark_read("other")
        assert e.value.code == "UNAUTHORIZED_ACCESS"
        assert n.mark_read("u1") is True
        assert n.mark_read("u1") is False


# ---------- Provider + templates ----------
class TestProviderAndTemplates:
    def test_sandbox_send(self):
        from modules.notifications.provider import SandboxEmailProvider
        out = asyncio.get_event_loop().run_until_complete(
            SandboxEmailProvider().send(to="a@b.com", subject="s", html="<p>h</p>"))
        assert out["status"] == "delivered"

    def test_build_default_and_resend_requires_key(self, monkeypatch):
        from modules.notifications.provider import build_email_provider, SandboxEmailProvider
        monkeypatch.delenv("EMAIL_PROVIDER", raising=False)
        assert isinstance(build_email_provider(), SandboxEmailProvider)
        monkeypatch.setenv("EMAIL_PROVIDER", "resend")
        monkeypatch.delenv("RESEND_API_KEY", raising=False)
        with pytest.raises(RuntimeError):
            build_email_provider()

    def test_templates_cover_events(self):
        from modules.notifications.templates import specs_for
        assert specs_for("PaymentCaptured", {"seller_id": "s", "order_id": "o",
                                             "amount": 10000, "currency": "UAH"})[0]["recipient_id"] == "s"
        oc = specs_for("OrderCompleted", {"seller_id": "s", "buyer_id": "b", "order_id": "o"})
        assert {x["recipient_id"] for x in oc} == {"s", "b"}
        ms = specs_for("MessageSent", {"author_id": "a", "participants": ["a", "b"]})
        assert len(ms) == 1 and ms[0]["recipient_id"] == "b"
        rv = specs_for("ReviewPublished", {"recipient_id": "r", "rating": 5})
        assert rv[0]["recipient_id"] == "r"
        assert specs_for("UnknownEvent", {}) == []


# ---------- Idempotency (INV-008) ----------
class TestIdempotency:
    def test_duplicate_event_recipient_blocked(self):
        import motor.motor_asyncio as m
        from modules.notifications.domain import Notification
        from modules.notifications.repository import NotificationRepository
        from buildingblocks.domain import DomainError

        async def run():
            db = m.AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
            repo = NotificationRepository(db)
            eid = "evt_" + uuid.uuid4().hex
            n1 = Notification.create(event_id=eid, event_type="MessageSent", recipient_id="uX",
                                     notif_type="NewMessage", title="t", body="b", channels=["in_app"])
            await repo.add(n1)
            n2 = Notification.create(event_id=eid, event_type="MessageSent", recipient_id="uX",
                                     notif_type="NewMessage", title="t", body="b", channels=["in_app"])
            dup = False
            try:
                await repo.add(n2)
            except DomainError as e:
                dup = (e.code == "DUPLICATE_NOTIFICATION")
            await db.notifications.delete_many({"event_id": eid})
            return dup
        assert asyncio.get_event_loop().run_until_complete(run()) is True


# ---------- Event-sourced creation + API ----------
class TestNotificationsAPI:
    def test_new_message_notification(self, seller, buyer):
        seller_sess, _, _ = seller
        buyer_sess, _, _ = buyer
        lid = _fresh_listing(seller_sess)
        cid = buyer_sess.post(f"{API}/conversations",
                              json={"context_type": "listing", "context_id": lid}).json()["conversation_id"]
        buyer_sess.post(f"{API}/conversations/{cid}/messages", json={"content": "hello there"})
        # seller should receive a NewMessage notification
        got = _poll_notifications(seller_sess, lambda n: n["notif_type"] == "NewMessage")
        assert got, "seller did not receive a NewMessage notification"

    def test_offer_accepted_notification(self, seller, buyer):
        seller_sess, _, _ = seller
        buyer_sess, _, _ = buyer
        lid = _fresh_listing(seller_sess)
        offer_id = buyer_sess.post(f"{API}/offers", json={"listing_id": lid, "amount": 90000}).json()["offer_id"]
        seller_sess.post(f"{API}/offers/{offer_id}/accept")
        got = _poll_notifications(buyer_sess, lambda n: n["notif_type"] == "OfferAccepted")
        assert got, "buyer did not receive an OfferAccepted notification"

    def test_unread_count_and_mark_read(self, seller, buyer):
        # Use the FRESH buyer as the notification recipient so no other tests' events
        # pollute the unread count (the shared seller account accumulates notifications).
        seller_sess, _, _ = seller
        buyer_sess, _, _ = buyer
        lid = _fresh_listing(seller_sess)
        cid = buyer_sess.post(f"{API}/conversations",
                              json={"context_type": "listing", "context_id": lid}).json()["conversation_id"]
        # seller replies -> the buyer receives a NewMessage notification
        buyer_sess.post(f"{API}/conversations/{cid}/messages", json={"content": "hi"})
        seller_sess.post(f"{API}/conversations/{cid}/messages", json={"content": "reply from seller"})
        got = _poll_notifications(buyer_sess, lambda n: n["notif_type"] == "NewMessage")
        assert got
        before = buyer_sess.get(f"{API}/notifications/unread-count").json()["count"]
        assert before >= 1
        buyer_sess.post(f"{API}/notifications/{got[0]['id']}/read")
        one = next(n for n in buyer_sess.get(f"{API}/notifications").json()["items"] if n["id"] == got[0]["id"])
        assert one["read"] is True
        buyer_sess.post(f"{API}/notifications/read-all")
        assert buyer_sess.get(f"{API}/notifications/unread-count").json()["count"] == 0

    def test_preferences_roundtrip(self, buyer):
        buyer_sess, _, _ = buyer
        d = buyer_sess.get(f"{API}/notifications/preferences").json()
        assert d["email_enabled"] is True
        upd = buyer_sess.put(f"{API}/notifications/preferences",
                             json={"email_enabled": False, "in_app_enabled": True,
                                   "muted_types": ["NewMessage"]}).json()
        assert upd["email_enabled"] is False and "NewMessage" in upd["muted_types"]
        again = buyer_sess.get(f"{API}/notifications/preferences").json()
        assert again["email_enabled"] is False


# ---------- Real-time in-app delivery over WebSocket ----------
class TestRealtimeNotification:
    def test_notification_pushed_live(self, seller, buyer):
        try:
            import websockets  # noqa: F401
        except ImportError:
            pytest.skip("websockets not installed")
        seller_sess, _, _ = seller
        buyer_sess, _, buyer_token = buyer
        lid = _fresh_listing(seller_sess)
        cid = buyer_sess.post(f"{API}/conversations",
                              json={"context_type": "listing", "context_id": lid}).json()["conversation_id"]

        async def scenario():
            import websockets
            async with websockets.connect(f"{WS_URL}?token={buyer_token}") as ws:
                await asyncio.sleep(0.4)
                # seller replies -> buyer should get a live "notification" frame
                seller_sess.post(f"{API}/conversations/{cid}/messages", json={"content": "reply"})
                for _ in range(30):
                    data = json.loads(await asyncio.wait_for(ws.recv(), timeout=6))
                    if data.get("type") == "notification":
                        return data
                return None
        got = asyncio.get_event_loop().run_until_complete(scenario())
        assert got is not None, "no real-time notification frame received"
        assert got["notif_type"] == "NewMessage"
