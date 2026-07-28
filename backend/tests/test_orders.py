"""Orders domain (Phase 5, DOMAIN-005) API + integration tests.

Covers §7 event-driven creation, §9 listing reservation, §12 cancel-releases,
§21 one-order-per-listing/idempotency, §22 authorization/privacy, INV-005/006
immutability & state machine (domain unit tests), and atomic outbox behavior.
"""
from __future__ import annotations

import os
import time
import uuid

import pytest
import requests

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"

SELLER = {"email": "seller@archivemarket.co", "password": "Seller12345"}
ADMIN = {"email": "admin@archivemarket.co", "password": "Admin12345"}
FEE_PCT = int(os.environ.get("PLATFORM_FEE_PERCENT", "10"))


# ---------- helpers ----------
def _new_user_payload():
    uid = uuid.uuid4().hex[:8]
    return {"email": f"TEST_ord_{uid}@example.com", "password": "Password12345",
            "display_name": f"buyer_{uid}"}


def _register():
    sess = requests.Session()
    payload = _new_user_payload()
    r = sess.post(f"{API}/auth/register", json=payload)
    assert r.status_code in (200, 201), r.text
    return sess, r.json()["user"]


def _login(creds):
    sess = requests.Session()
    r = sess.post(f"{API}/auth/login", json=creds)
    assert r.status_code == 200, r.text
    return sess


def _make_fresh_listing(seller_sess, price_amount=400000):
    payload = {
        "title": f"TEST_ord_{uuid.uuid4().hex[:6]}", "description": "test",
        "price_amount": price_amount, "currency": "UAH", "brand": "Nike",
        "category": "footwear", "gender": "Men", "size": "42",
        "color": "White", "material": "Leather", "condition": "LIKE_NEW",
        "images": [{"url": "https://example.com/x.jpg"}], "allow_offers": True,
    }
    r = seller_sess.post(f"{API}/listings", json=payload)
    assert r.status_code in (200, 201), r.text
    lid = r.json()["listing_id"]
    p = seller_sess.post(f"{API}/listings/{lid}/publish")
    assert p.status_code == 200, p.text
    return lid, price_amount


def _accepted_offer_flow(buyer_sess, seller_sess, listing_id, offer_amount=150000):
    r = buyer_sess.post(f"{API}/offers",
                        json={"listing_id": listing_id, "amount": offer_amount})
    assert r.status_code == 200, r.text
    offer_id = r.json()["offer_id"]
    ra = seller_sess.post(f"{API}/offers/{offer_id}/accept")
    assert ra.status_code == 200, ra.text
    return offer_id


def _poll_order_for_buyer(buyer_sess, offer_id, timeout=8.0):
    """Poll GET /api/orders?box=buyer until an order matching offer_id appears."""
    end = time.time() + timeout
    while time.time() < end:
        r = buyer_sess.get(f"{API}/orders", params={"box": "buyer"})
        assert r.status_code == 200, r.text
        for o in r.json()["items"]:
            if o.get("offer_id") == offer_id:
                return o
        time.sleep(0.5)
    return None


# ---------- Fixtures ----------
@pytest.fixture(scope="module")
def seller_sess():
    return _login(SELLER)


@pytest.fixture
def buyer_sess():
    sess, _ = _register()
    return sess


# ---------- Domain unit tests (INV-005/006, state machine) ----------
class TestOrderDomain:
    def test_state_machine_transitions_and_immutability(self):
        from modules.orders.domain import Order
        from buildingblocks.domain import DomainError

        o = Order.create_from_offer(
            buyer_id="b", seller_id="s", listing_id="l", offer_id="of",
            title="t", amount=100000, currency="UAH", fee_percent=10)
        assert o.status == "AwaitingPayment"
        assert o.total == 100000 and o.platform_fee == 10000 and o.subtotal == 100000
        assert o.order_number.startswith("ARC-")
        # status history contains Created and AwaitingPayment
        to_states = [h.to_status for h in o.status_history]
        assert "Created" in to_states and "AwaitingPayment" in to_states

        # Invalid transition: AwaitingPayment -> Shipped
        with pytest.raises(DomainError) as e:
            o._transition("Shipped")
        assert e.value.code == "INVALID_ORDER_STATE"

        # Valid: mark_paid -> Paid; cannot go backwards
        o.mark_paid("p1")
        assert o.status == "Paid"
        with pytest.raises(DomainError):
            o.cancel(actor="b")  # cancel only allowed from AwaitingPayment

    def test_cancel_only_from_awaiting_payment(self):
        from modules.orders.domain import Order
        from buildingblocks.domain import DomainError

        o = Order.create_from_offer(
            buyer_id="b", seller_id="s", listing_id="l", offer_id="of",
            title="t", amount=1000, currency="UAH", fee_percent=10)
        o.cancel(actor="b")
        assert o.status == "Canceled"
        # already canceled -> cannot cancel again
        with pytest.raises(DomainError) as e:
            o.cancel(actor="b")
        assert e.value.code == "CANCELLATION_NOT_ALLOWED"


# ---------- Auto-creation, reservation, idempotency ----------
class TestOrderAutoCreation:
    def test_order_auto_created_after_accept(self, seller_sess, buyer_sess):
        lid, _ = _make_fresh_listing(seller_sess)
        amount = 150000
        offer_id = _accepted_offer_flow(buyer_sess, seller_sess, lid, amount)

        order = _poll_order_for_buyer(buyer_sess, offer_id)
        assert order is not None, "Order was not auto-created within timeout"
        assert order["status"] == "AwaitingPayment"
        assert order["order_number"].startswith("ARC-")
        assert order["total"] == amount
        assert order["platform_fee"] == round(amount * FEE_PCT / 100)
        assert order["currency"] == "UAH"

        to_states = [h["to_status"] for h in order["status_history"]]
        assert "Created" in to_states and "AwaitingPayment" in to_states

        # Seller box also lists it
        sr = seller_sess.get(f"{API}/orders", params={"box": "seller"})
        assert sr.status_code == 200
        assert any(o["offer_id"] == offer_id for o in sr.json()["items"])

    def test_listing_becomes_reserved_new_offer_409(self, seller_sess, buyer_sess):
        lid, _ = _make_fresh_listing(seller_sess)
        offer_id = _accepted_offer_flow(buyer_sess, seller_sess, lid, 150000)
        assert _poll_order_for_buyer(buyer_sess, offer_id) is not None

        # Poll until listing reservation propagates (OrderCreated -> reserve)
        b2, _ = _register()
        last = None
        for _ in range(15):
            last = b2.post(f"{API}/offers",
                           json={"listing_id": lid, "amount": 100000})
            if last.status_code == 409:
                break
            time.sleep(0.5)
        assert last.status_code == 409, last.text
        body_s = str(last.json())
        assert ("LISTING_NOT_AVAILABLE" in body_s
                or "LISTING_SOLD" in body_s
                or "LISTING_RESERVED" in body_s), body_s

    def test_one_order_per_offer_idempotent(self, seller_sess, buyer_sess):
        lid, _ = _make_fresh_listing(seller_sess)
        offer_id = _accepted_offer_flow(buyer_sess, seller_sess, lid, 150000)
        assert _poll_order_for_buyer(buyer_sess, offer_id) is not None

        # After some settling time, only ONE order should exist for this offer_id
        time.sleep(2.0)
        r = buyer_sess.get(f"{API}/orders", params={"box": "buyer"})
        matches = [o for o in r.json()["items"] if o["offer_id"] == offer_id]
        assert len(matches) == 1, f"expected exactly 1 order per offer, got {len(matches)}"


# ---------- Cancellation flow (§12) ----------
class TestOrderCancel:
    def test_buyer_can_cancel_awaiting_payment(self, seller_sess, buyer_sess):
        lid, _ = _make_fresh_listing(seller_sess)
        offer_id = _accepted_offer_flow(buyer_sess, seller_sess, lid, 150000)
        order = _poll_order_for_buyer(buyer_sess, offer_id)
        assert order is not None

        rc = buyer_sess.post(f"{API}/orders/{order['id']}/cancel")
        assert rc.status_code == 200, rc.text
        assert rc.json()["status"] == "Canceled"

        # Listing should be released (Published) within a few seconds -> new offer works
        b2, _ = _register()
        ok = False
        for _ in range(10):
            r = b2.post(f"{API}/offers", json={"listing_id": lid, "amount": 100000})
            if r.status_code == 200:
                ok = True
                break
            time.sleep(0.5)
        assert ok, f"listing was not released after order cancel; last resp: {r.text}"

    def test_seller_cannot_cancel_order(self, seller_sess, buyer_sess):
        lid, _ = _make_fresh_listing(seller_sess)
        offer_id = _accepted_offer_flow(buyer_sess, seller_sess, lid, 150000)
        order = _poll_order_for_buyer(buyer_sess, offer_id)
        assert order is not None
        rc = seller_sess.post(f"{API}/orders/{order['id']}/cancel")
        assert rc.status_code == 403, rc.text
        assert "UNAUTHORIZED_ACCESS" in str(rc.json())

    def test_cannot_cancel_twice(self, seller_sess, buyer_sess):
        lid, _ = _make_fresh_listing(seller_sess)
        offer_id = _accepted_offer_flow(buyer_sess, seller_sess, lid, 150000)
        order = _poll_order_for_buyer(buyer_sess, offer_id)
        assert order is not None

        r1 = buyer_sess.post(f"{API}/orders/{order['id']}/cancel")
        assert r1.status_code == 200
        r2 = buyer_sess.post(f"{API}/orders/{order['id']}/cancel")
        assert r2.status_code == 409, r2.text
        assert "CANCELLATION_NOT_ALLOWED" in str(r2.json())


# ---------- Authz/privacy (§22) ----------
class TestOrderAuthz:
    def test_third_party_cannot_view_order(self, seller_sess, buyer_sess):
        lid, _ = _make_fresh_listing(seller_sess)
        offer_id = _accepted_offer_flow(buyer_sess, seller_sess, lid, 150000)
        order = _poll_order_for_buyer(buyer_sess, offer_id)
        assert order is not None

        third, _ = _register()
        r = third.get(f"{API}/orders/{order['id']}")
        assert r.status_code == 403, r.text
        assert "UNAUTHORIZED_ACCESS" in str(r.json())

    def test_admin_can_view_order(self, seller_sess, buyer_sess):
        lid, _ = _make_fresh_listing(seller_sess)
        offer_id = _accepted_offer_flow(buyer_sess, seller_sess, lid, 150000)
        order = _poll_order_for_buyer(buyer_sess, offer_id)
        assert order is not None
        admin = _login(ADMIN)
        r = admin.get(f"{API}/orders/{order['id']}")
        assert r.status_code == 200, r.text
        assert r.json()["order"]["id"] == order["id"]

    def test_order_endpoints_require_auth(self):
        r1 = requests.get(f"{API}/orders")
        assert r1.status_code == 401
        r2 = requests.get(f"{API}/orders/some-id")
        assert r2.status_code == 401
        r3 = requests.post(f"{API}/orders/some-id/cancel")
        assert r3.status_code == 401

    def test_no_public_post_to_create_order(self, buyer_sess):
        # There is intentionally no POST /api/orders — should be 404 or 405
        r = buyer_sess.post(f"{API}/orders", json={"listing_id": "x"})
        assert r.status_code in (404, 405), r.text


# ---------- Atomic outbox behavior ----------
class TestAtomicOutbox:
    def test_outbox_receives_events_and_pending_cleared(self, seller_sess, buyer_sess):
        """After an accepted offer -> order flow, outbox collection should have
        OfferAccepted (and OrderCreated) copies and aggregate pending_events cleared."""
        import asyncio

        from motor.motor_asyncio import AsyncIOMotorClient

        lid, _ = _make_fresh_listing(seller_sess)
        offer_id = _accepted_offer_flow(buyer_sess, seller_sess, lid, 150000)
        order = _poll_order_for_buyer(buyer_sess, offer_id)
        assert order is not None
        # Give relay a moment
        time.sleep(2.0)

        mongo_url = os.environ["MONGO_URL"].strip().strip('"').strip("'")
        db_name = os.environ["DB_NAME"].strip().strip('"').strip("'")

        async def _check():
            client = AsyncIOMotorClient(mongo_url)
            db = client[db_name]
            # Outbox has an OfferAccepted event for this offer
            oa = await db.outbox.find_one(
                {"event_type": "OfferAccepted", "payload.offer_id": offer_id})
            oc = await db.outbox.find_one(
                {"event_type": "OrderCreated", "payload.offer_id": offer_id})
            # Aggregate pending_events cleared by relay
            offer_doc = await db.offers.find_one({"_id": offer_id})
            order_doc = await db.orders.find_one({"_id": order["id"]})
            client.close()
            return oa, oc, offer_doc, order_doc

        oa, oc, offer_doc, order_doc = asyncio.get_event_loop().run_until_complete(_check())
        assert oa is not None, "OfferAccepted not found in outbox"
        assert oc is not None, "OrderCreated not found in outbox"
        assert offer_doc is not None
        assert not offer_doc.get("pending_events"), (
            f"offer pending_events not cleared: {offer_doc.get('pending_events')}")
        assert order_doc is not None
        assert not order_doc.get("pending_events"), (
            f"order pending_events not cleared: {order_doc.get('pending_events')}")


# ---------- Listings->Contracts refactor sanity ----------
class TestListingContractRefactor:
    def test_seed_listing_detail_has_embedded_seller(self):
        r = requests.get(f"{API}/listings")
        assert r.status_code == 200
        items = r.json()["items"]
        assert items, "no seeded listings"
        # find a seeded one (not TEST_ prefixed)
        seed = next((x for x in items if not x.get("title", "").startswith("TEST_")), items[0])
        d = requests.get(f"{API}/listings/{seed['id']}")
        assert d.status_code == 200, d.text
        listing = d.json()["listing"]
        assert "seller" in listing
        assert "display_name" in listing["seller"]
        assert "reputation" in listing["seller"]
