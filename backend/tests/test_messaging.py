"""Messaging (Phase 9, DOMAIN-009) — conversation aggregate, REST endpoints,
authorization, dedup/reuse, read receipts, moderation, and REAL-TIME WebSocket
delivery. Requires PAYMENT_PROVIDER=sandbox / SHIPPING_PROVIDER=sandbox."""
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
ADMIN = {"email": os.environ.get("ADMIN_EMAIL", "admin@archivemarket.co"),
         "password": os.environ.get("ADMIN_PASSWORD", "Admin12345")}


def _register(prefix="msg"):
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
    payload = {
        "title": f"TEST_msg_{uuid.uuid4().hex[:6]}", "description": "test",
        "price_amount": 300000, "currency": "UAH", "brand": "Nike",
        "category": "footwear", "gender": "Men", "size": "42",
        "color": "White", "material": "Leather", "condition": "LIKE_NEW",
        "images": [{"url": "https://example.com/x.jpg"}], "allow_offers": True,
    }
    r = seller_sess.post(f"{API}/listings", json=payload)
    lid = r.json()["listing_id"]
    seller_sess.post(f"{API}/listings/{lid}/publish")
    return lid


@pytest.fixture(scope="module")
def seller():
    return _login(SELLER)


@pytest.fixture(scope="module")
def admin_sess():
    return _login(ADMIN)[0]


@pytest.fixture
def buyer():
    return _register("msg")


# ---------- Domain unit tests ----------
class TestConversationDomain:
    def _make(self):
        from modules.messaging.domain import Conversation
        return Conversation.start(context_type="listing", context_id="L1",
                                 participants=["a", "b"], created_by="a")

    def test_start_and_event(self):
        c = self._make()
        assert c.status == "Active" and c.participants == ["a", "b"]
        assert [e.event_type for e in c.pull_events()] == ["ConversationCreated"]

    def test_needs_two_participants(self):
        from buildingblocks.domain import DomainError
        from modules.messaging.domain import Conversation
        with pytest.raises(DomainError) as e:
            Conversation.start(context_type="listing", context_id="L1",
                               participants=["a", "a"], created_by="a")
        assert e.value.code == "INVALID_PARTICIPANTS"

    def test_only_participant_posts(self):
        from buildingblocks.domain import DomainError
        c = self._make(); c.pull_events()
        with pytest.raises(DomainError) as e:
            c.post_message("stranger", "hi")
        assert e.value.code == "PARTICIPANT_NOT_AUTHORIZED"

    def test_empty_message_rejected(self):
        from buildingblocks.domain import DomainError
        c = self._make()
        with pytest.raises(DomainError) as e:
            c.post_message("a", "   ")
        assert e.value.code == "EMPTY_MESSAGE"

    def test_read_receipt_idempotent_and_unread(self):
        c = self._make(); c.pull_events()
        c.post_message("a", "hello")   # from a
        assert c.unread_count("b") == 1
        assert c.unread_count("a") == 0     # author read own
        assert c.mark_read("b") is True
        assert c.unread_count("b") == 0
        assert c.mark_read("b") is False    # idempotent no-op

    def test_closed_is_readonly(self):
        from buildingblocks.domain import DomainError
        c = self._make(); c.pull_events()
        c.close("admin")
        with pytest.raises(DomainError) as e:
            c.post_message("a", "hi")
        assert e.value.code == "CONVERSATION_CLOSED"

    def test_hide_message_immutably(self):
        c = self._make(); c.pull_events()
        m = c.post_message("a", "secret"); c.pull_events()
        c.hide_message(m.message_id, "mod")
        assert c.messages[0].hidden is True
        assert c.messages[0].content == "secret"  # content preserved for audit


# ---------- REST API + authorization ----------
class TestMessagingAPI:
    def test_start_from_listing_and_reuse(self, seller, buyer):
        seller_sess, _, _ = seller
        buyer_sess, _, _ = buyer
        lid = _fresh_listing(seller_sess)
        r1 = buyer_sess.post(f"{API}/conversations",
                             json={"context_type": "listing", "context_id": lid})
        assert r1.status_code == 200, r1.text
        cid = r1.json()["conversation_id"]
        # calling again reuses the same conversation (§9)
        r2 = buyer_sess.post(f"{API}/conversations",
                             json={"context_type": "listing", "context_id": lid})
        assert r2.json()["conversation_id"] == cid

    def test_seller_cannot_message_own_listing(self, seller):
        seller_sess, _, _ = seller
        lid = _fresh_listing(seller_sess)
        r = seller_sess.post(f"{API}/conversations",
                             json={"context_type": "listing", "context_id": lid})
        assert r.status_code == 422
        assert "INVALID_PARTICIPANTS" in str(r.json())

    def test_send_and_history_marks_read(self, seller, buyer):
        seller_sess, _, _ = seller
        buyer_sess, buyer_user, _ = buyer
        lid = _fresh_listing(seller_sess)
        cid = buyer_sess.post(f"{API}/conversations",
                              json={"context_type": "listing", "context_id": lid}).json()["conversation_id"]
        s = buyer_sess.post(f"{API}/conversations/{cid}/messages", json={"content": "Is this available?"})
        assert s.status_code == 200, s.text
        assert s.json()["content"] == "Is this available?"
        # seller sees 1 unread
        conv = next(c for c in seller_sess.get(f"{API}/conversations").json()["items"] if c["id"] == cid)
        assert conv["unread"] == 1
        # seller opens thread -> marked read
        h = seller_sess.get(f"{API}/conversations/{cid}/messages")
        assert h.status_code == 200 and len(h.json()["messages"]) == 1
        conv2 = next(c for c in seller_sess.get(f"{API}/conversations").json()["items"] if c["id"] == cid)
        assert conv2["unread"] == 0

    def test_non_participant_cannot_read_or_send(self, seller, buyer):
        seller_sess, _, _ = seller
        buyer_sess, _, _ = buyer
        lid = _fresh_listing(seller_sess)
        cid = buyer_sess.post(f"{API}/conversations",
                              json={"context_type": "listing", "context_id": lid}).json()["conversation_id"]
        third, _, _ = _register("third")
        assert third.get(f"{API}/conversations/{cid}/messages").status_code == 403
        assert third.post(f"{API}/conversations/{cid}/messages", json={"content": "hi"}).status_code == 403

    def test_start_from_order_requires_participant(self, seller, buyer):
        seller_sess, _, _ = seller
        buyer_sess, _, _ = buyer
        # build an order
        lid = _fresh_listing(seller_sess)
        offer_id = buyer_sess.post(f"{API}/offers", json={"listing_id": lid, "amount": 100000}).json()["offer_id"]
        seller_sess.post(f"{API}/offers/{offer_id}/accept")
        order = None
        end = time.time() + 8
        while time.time() < end and not order:
            for o in buyer_sess.get(f"{API}/orders", params={"box": "buyer"}).json()["items"]:
                if o.get("offer_id") == offer_id:
                    order = o
            if not order:
                time.sleep(0.4)
        assert order
        # both participants can open the order conversation (same one reused)
        c1 = buyer_sess.post(f"{API}/conversations", json={"context_type": "order", "context_id": order["id"]})
        c2 = seller_sess.post(f"{API}/conversations", json={"context_type": "order", "context_id": order["id"]})
        assert c1.status_code == 200 and c2.status_code == 200
        assert c1.json()["conversation_id"] == c2.json()["conversation_id"]
        # a stranger cannot
        third, _, _ = _register("third")
        assert third.post(f"{API}/conversations",
                          json={"context_type": "order", "context_id": order["id"]}).status_code == 403

    def test_archive(self, seller, buyer):
        seller_sess, _, _ = seller
        buyer_sess, _, _ = buyer
        lid = _fresh_listing(seller_sess)
        cid = buyer_sess.post(f"{API}/conversations",
                              json={"context_type": "listing", "context_id": lid}).json()["conversation_id"]
        r = buyer_sess.post(f"{API}/conversations/{cid}/archive")
        assert r.status_code == 200 and r.json()["status"] == "Archived"


# ---------- Moderation ----------
class TestMessagingModeration:
    def test_admin_hide_message(self, seller, buyer, admin_sess):
        seller_sess, _, _ = seller
        buyer_sess, _, _ = buyer
        lid = _fresh_listing(seller_sess)
        cid = buyer_sess.post(f"{API}/conversations",
                              json={"context_type": "listing", "context_id": lid}).json()["conversation_id"]
        mid = buyer_sess.post(f"{API}/conversations/{cid}/messages",
                              json={"content": "spam link"}).json()["message_id"]
        h = admin_sess.post(f"{API}/conversations/{cid}/messages/{mid}/hide")
        assert h.status_code == 200
        # participant no longer sees content
        msgs = buyer_sess.get(f"{API}/conversations/{cid}/messages").json()["messages"]
        assert all(m["message_id"] != mid for m in msgs), "hidden message still visible to participant"

    def test_participant_cannot_hide(self, seller, buyer):
        seller_sess, _, _ = seller
        buyer_sess, _, _ = buyer
        lid = _fresh_listing(seller_sess)
        cid = buyer_sess.post(f"{API}/conversations",
                              json={"context_type": "listing", "context_id": lid}).json()["conversation_id"]
        mid = buyer_sess.post(f"{API}/conversations/{cid}/messages",
                              json={"content": "hi"}).json()["message_id"]
        assert buyer_sess.post(f"{API}/conversations/{cid}/messages/{mid}/hide").status_code == 403

    def test_admin_close_makes_readonly(self, seller, buyer, admin_sess):
        seller_sess, _, _ = seller
        buyer_sess, _, _ = buyer
        lid = _fresh_listing(seller_sess)
        cid = buyer_sess.post(f"{API}/conversations",
                              json={"context_type": "listing", "context_id": lid}).json()["conversation_id"]
        assert admin_sess.post(f"{API}/conversations/{cid}/close").json()["status"] == "Closed"
        r = buyer_sess.post(f"{API}/conversations/{cid}/messages", json={"content": "hi"})
        assert r.status_code == 409 and "CONVERSATION_CLOSED" in str(r.json())


# ---------- Real-time WebSocket delivery ----------
class TestWebSocketDelivery:
    def test_message_delivered_live_to_other_participant(self, seller, buyer):
        try:
            import websockets  # noqa: F401
        except ImportError:
            pytest.skip("websockets package not installed")

        seller_sess, _, seller_token = seller
        buyer_sess, _, buyer_token = buyer
        assert seller_token and buyer_token, "access_token must be returned by auth"
        lid = _fresh_listing(seller_sess)
        cid = buyer_sess.post(f"{API}/conversations",
                              json={"context_type": "listing", "context_id": lid}).json()["conversation_id"]

        async def scenario():
            import websockets
            # seller connects and waits for a live message
            async with websockets.connect(f"{WS_URL}?token={seller_token}") as ws:
                await asyncio.sleep(0.4)  # let the connection register
                # buyer sends via REST -> server should broadcast to seller's socket
                buyer_sess.post(f"{API}/conversations/{cid}/messages",
                                json={"content": "Real-time hello"})
                received = None
                for _ in range(20):
                    frame = await asyncio.wait_for(ws.recv(), timeout=5)
                    data = json.loads(frame)
                    if data.get("type") == "message":
                        received = data
                        break
                return received

        received = asyncio.get_event_loop().run_until_complete(scenario())
        assert received is not None, "message was not delivered over the WebSocket"
        assert received["content"] == "Real-time hello"
        assert received["conversation_id"] == cid

    def test_ws_send_frame_persists_and_delivers(self, seller, buyer):
        try:
            import websockets  # noqa: F401
        except ImportError:
            pytest.skip("websockets package not installed")

        seller_sess, _, seller_token = seller
        buyer_sess, _, buyer_token = buyer
        lid = _fresh_listing(seller_sess)
        cid = buyer_sess.post(f"{API}/conversations",
                              json={"context_type": "listing", "context_id": lid}).json()["conversation_id"]

        async def scenario():
            import websockets
            async with websockets.connect(f"{WS_URL}?token={buyer_token}") as ws:
                await asyncio.sleep(0.4)
                await ws.send(json.dumps({"type": "send", "conversation_id": cid,
                                          "content": "Sent over the socket"}))
                for _ in range(20):
                    data = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
                    if data.get("type") == "message":
                        return data
                return None

        received = asyncio.get_event_loop().run_until_complete(scenario())
        assert received and received["content"] == "Sent over the socket"
        # and it persisted to history
        msgs = buyer_sess.get(f"{API}/conversations/{cid}/messages").json()["messages"]
        assert any(m["content"] == "Sent over the socket" for m in msgs)
