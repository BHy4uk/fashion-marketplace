"""Payments (Phase 6, DOMAIN-006) — escrow lifecycle, provider abstraction,
choreography with Orders, and API tests. Requires PAYMENT_PROVIDER=sandbox."""
from __future__ import annotations

import asyncio
import base64
import json
import os
import time
import uuid
from datetime import timedelta

import pytest
import requests

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"

SELLER = {"email": "seller@archivemarket.co", "password": "Seller12345"}


# ---------- helpers ----------
def _register(prefix="pay"):
    sess = requests.Session()
    uid = uuid.uuid4().hex[:8]
    r = sess.post(f"{API}/auth/register", json={
        "email": f"TEST_{prefix}_{uid}@example.com",
        "password": "Password12345",
        "display_name": f"{prefix}_{uid}"})
    assert r.status_code in (200, 201), r.text
    return sess, r.json()["user"]


def _login(creds):
    sess = requests.Session()
    r = sess.post(f"{API}/auth/login", json=creds)
    assert r.status_code == 200, r.text
    return sess


def _make_fresh_listing(seller_sess, price_amount=400000):
    payload = {
        "title": f"TEST_pay_{uuid.uuid4().hex[:6]}", "description": "test",
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
    return lid


def _create_awaiting_order(seller_sess, buyer_sess, amount=150000):
    lid = _make_fresh_listing(seller_sess)
    r = buyer_sess.post(f"{API}/offers", json={"listing_id": lid, "amount": amount})
    assert r.status_code == 200, r.text
    offer_id = r.json()["offer_id"]
    ra = seller_sess.post(f"{API}/offers/{offer_id}/accept")
    assert ra.status_code == 200, ra.text
    # poll for order
    end = time.time() + 8
    while time.time() < end:
        r = buyer_sess.get(f"{API}/orders", params={"box": "buyer"})
        for o in r.json()["items"]:
            if o.get("offer_id") == offer_id:
                return o, lid
        time.sleep(0.4)
    raise AssertionError("order not created")


def _poll_order_status(sess, order_id, target, timeout=8.0):
    end = time.time() + timeout
    while time.time() < end:
        r = sess.get(f"{API}/orders/{order_id}")
        if r.status_code == 200 and r.json()["order"]["status"] == target:
            return r.json()["order"]
        time.sleep(0.4)
    return None


@pytest.fixture(scope="module")
def seller_sess():
    return _login(SELLER)


@pytest.fixture
def buyer_sess():
    sess, _ = _register("pay")
    return sess


# ---------- Domain unit tests (Payment aggregate + provider adapters) ----------
class TestPaymentDomain:
    def _make(self):
        from modules.payments.domain import Payment
        return Payment.create(order_id="o1", buyer_id="b", seller_id="s",
                              amount=100000, currency="UAH", provider="sandbox")

    def test_valid_state_machine(self):
        p = self._make()
        p.initiate(); assert p.status == "PendingAuthorization"
        p.authorize("ref"); assert p.status == "Authorized"
        p.capture("ref"); assert p.status == "Captured" and p.held is True
        # schedule + release
        p.schedule_release(timedelta(hours=72))
        assert p.release_at is not None
        p.release("rel"); assert p.status == "Settled" and p.held is False
        kinds = [t.kind for t in p.transactions]
        assert "authorize" in kinds and "capture" in kinds and "settle" in kinds

    def test_invalid_transitions_raise(self):
        from buildingblocks.domain import DomainError
        p = self._make()
        # cannot capture from Created
        with pytest.raises(DomainError) as e:
            p.capture()
        assert e.value.code == "INVALID_PAYMENT_STATE"

    def test_refund_only_from_auth_or_captured(self):
        from buildingblocks.domain import DomainError
        p = self._make()
        with pytest.raises(DomainError) as e:
            p.refund()
        assert e.value.code == "REFUND_NOT_ALLOWED"
        p.initiate(); p.authorize(); p.capture()
        p.refund("ref")
        assert p.status == "Refunded" and p.held is False

    def test_schedule_release_noop_when_not_captured(self):
        p = self._make()
        p.initiate(); p.authorize()
        p.schedule_release(timedelta(hours=72))
        assert p.release_at is None  # noop

    def test_is_release_due(self):
        from buildingblocks.domain import utc_now
        p = self._make()
        p.initiate(); p.authorize(); p.capture()
        # not due when release_at unset
        assert not p.is_release_due()
        p.schedule_release(timedelta(hours=-1))  # already passed
        assert p.is_release_due(now=utc_now())


class TestProvider:
    def test_liqpay_sign_and_verify_callback_roundtrip(self):
        from modules.payments.provider import LiqPayProvider
        prov = LiqPayProvider("pub", "priv", "https://x/callback", sandbox=True)
        payload = {"order_id": "o1", "status": "success", "amount": "10.00"}
        data = prov._encode(payload)
        sig = prov._sign(data)
        # correct sig -> parses back
        result = asyncio.get_event_loop().run_until_complete(prov.verify_callback(data, sig))
        assert result["order_id"] == "o1"
        # tampered sig raises
        with pytest.raises(ValueError):
            asyncio.get_event_loop().run_until_complete(prov.verify_callback(data, "bad"))

    def test_liqpay_create_checkout_shape(self):
        from modules.payments.provider import LiqPayProvider
        prov = LiqPayProvider("pub", "priv", "https://x/cb", sandbox=True)
        out = asyncio.get_event_loop().run_until_complete(
            prov.create_checkout(order_id="o1", amount="10.00", currency="UAH",
                                 description="d", hold=True))
        assert out["provider"] == "liqpay"
        assert out["auto_settle"] is False
        assert out["checkout_url"] and out["data"] and out["signature"]
        # verify sig on returned data
        result = asyncio.get_event_loop().run_until_complete(
            prov.verify_callback(out["data"], out["signature"]))
        assert result["action"] == "hold"
        assert result["order_id"] == "o1"

    def test_sandbox_provider_auto_settle(self):
        from modules.payments.provider import SandboxProvider
        prov = SandboxProvider()
        out = asyncio.get_event_loop().run_until_complete(
            prov.create_checkout(order_id="o1", amount="10.00", currency="UAH",
                                 description="d", hold=True))
        assert out["auto_settle"] is True and out["provider"] == "sandbox"

    def test_build_provider_selects_sandbox_by_default(self, monkeypatch):
        from modules.payments.provider import build_provider, SandboxProvider
        monkeypatch.delenv("PAYMENT_PROVIDER", raising=False)
        assert isinstance(build_provider(), SandboxProvider)
        monkeypatch.setenv("PAYMENT_PROVIDER", "sandbox")
        assert isinstance(build_provider(), SandboxProvider)

    def test_build_provider_liqpay_requires_keys(self, monkeypatch):
        from modules.payments.provider import build_provider
        monkeypatch.setenv("PAYMENT_PROVIDER", "liqpay")
        monkeypatch.delenv("LIQPAY_PUBLIC_KEY", raising=False)
        monkeypatch.delenv("LIQPAY_PRIVATE_KEY", raising=False)
        with pytest.raises(RuntimeError):
            build_provider()


# ---------- API tests: sandbox checkout & escrow choreography ----------
class TestCheckoutAPI:
    def test_checkout_captures_and_holds_escrow(self, seller_sess, buyer_sess):
        order, _ = _create_awaiting_order(seller_sess, buyer_sess, 150000)
        r = buyer_sess.post(f"{API}/payments/checkout", json={"order_id": order["id"]})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["status"] == "Captured"
        # GET /api/payments/order/{id}
        g = buyer_sess.get(f"{API}/payments/order/{order['id']}")
        assert g.status_code == 200
        p = g.json()["payment"]
        assert p is not None
        assert p["status"] == "Captured"
        assert p["held"] is True
        assert p["provider"] == "sandbox"
        kinds = [t["kind"] for t in p["transactions"]]
        assert "authorize" in kinds and "capture" in kinds

    def test_order_becomes_paid_via_event(self, seller_sess, buyer_sess):
        order, _ = _create_awaiting_order(seller_sess, buyer_sess, 200000)
        r = buyer_sess.post(f"{API}/payments/checkout", json={"order_id": order["id"]})
        assert r.status_code == 200
        # poll for order Paid (async choreography via outbox)
        paid = _poll_order_status(buyer_sess, order["id"], "Paid", timeout=8)
        assert paid is not None, "order did not transition to Paid via PaymentCaptured event"
        assert len(paid["payment_ids"]) == 1
        states = [h["to_status"] for h in paid["status_history"]]
        assert states == ["Created", "AwaitingPayment", "Paid"]

    def test_only_buyer_can_pay(self, seller_sess, buyer_sess):
        order, _ = _create_awaiting_order(seller_sess, buyer_sess, 150000)
        # seller
        r = seller_sess.post(f"{API}/payments/checkout", json={"order_id": order["id"]})
        assert r.status_code == 403
        assert "UNAUTHORIZED_ACCESS" in str(r.json())
        # third party
        third, _ = _register("third")
        r = third.post(f"{API}/payments/checkout", json={"order_id": order["id"]})
        assert r.status_code == 403

    def test_order_not_found(self, buyer_sess):
        r = buyer_sess.post(f"{API}/payments/checkout",
                            json={"order_id": "nonexistent-id"})
        assert r.status_code == 404
        assert "ORDER_NOT_FOUND" in str(r.json())

    def test_idempotent_double_checkout(self, seller_sess, buyer_sess):
        order, _ = _create_awaiting_order(seller_sess, buyer_sess, 150000)
        r1 = buyer_sess.post(f"{API}/payments/checkout", json={"order_id": order["id"]})
        assert r1.status_code == 200
        pid1 = r1.json()["payment_id"]
        # second call must be idempotent
        r2 = buyer_sess.post(f"{API}/payments/checkout", json={"order_id": order["id"]})
        assert r2.status_code == 200, r2.text
        assert r2.json()["payment_id"] == pid1
        assert r2.json()["status"] == "Captured"
        # exactly one payment doc
        g = buyer_sess.get(f"{API}/payments/order/{order['id']}")
        p = g.json()["payment"]
        # only one capture transaction
        caps = [t for t in p["transactions"] if t["kind"] == "capture"]
        assert len(caps) == 1

    def test_pay_after_paid_returns_existing(self, seller_sess, buyer_sess):
        order, _ = _create_awaiting_order(seller_sess, buyer_sess, 150000)
        buyer_sess.post(f"{API}/payments/checkout", json={"order_id": order["id"]})
        # wait until Order is Paid
        assert _poll_order_status(buyer_sess, order["id"], "Paid") is not None
        # attempt again -> the checkout should short-circuit idempotently since
        # payment.status is Captured/Settled
        r = buyer_sess.post(f"{API}/payments/checkout", json={"order_id": order["id"]})
        assert r.status_code == 200, r.text
        assert r.json()["status"] in ("Captured", "Settled")


# ---------- Service-level escrow release + refund ----------
class TestEscrowService:
    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def _db(self):
        from motor.motor_asyncio import AsyncIOMotorClient
        mongo_url = os.environ["MONGO_URL"].strip().strip('"').strip("'")
        db_name = os.environ["DB_NAME"].strip().strip('"').strip("'")
        return AsyncIOMotorClient(mongo_url)[db_name]

    def test_schedule_release_and_release_due(self, seller_sess, buyer_sess):
        from modules.payments.service import PaymentService
        from buildingblocks.domain import utc_now

        order, _ = _create_awaiting_order(seller_sess, buyer_sess, 150000)
        r = buyer_sess.post(f"{API}/payments/checkout", json={"order_id": order["id"]})
        assert r.status_code == 200

        db = self._db()
        svc = PaymentService(db)

        # schedule release (would normally be triggered by OrderCompleted)
        self._run(svc.schedule_release_for_order(order["id"]))
        payment = self._run(svc.repo.by_order(order["id"]))
        assert payment.status == "Captured" and payment.held is True
        assert payment.release_at is not None

        # sweeper: release_at is 72h in future -> should NOT release
        released = self._run(svc.release_due())
        assert released == 0
        payment = self._run(svc.repo.by_order(order["id"]))
        assert payment.status == "Captured"

        # Force release_at to past and re-sweep
        self._run(db.payments.update_one(
            {"order_id": order["id"]},
            {"$set": {"release_at": utc_now() - timedelta(seconds=1)}}))
        released = self._run(svc.release_due())
        assert released == 1
        payment = self._run(svc.repo.by_order(order["id"]))
        assert payment.status == "Settled" and payment.held is False

    def test_sweeper_ignores_payments_without_release_at(self, seller_sess, buyer_sess):
        from modules.payments.service import PaymentService
        order, _ = _create_awaiting_order(seller_sess, buyer_sess, 150000)
        buyer_sess.post(f"{API}/payments/checkout", json={"order_id": order["id"]})
        db = self._db()
        svc = PaymentService(db)
        # Do NOT call schedule_release; release_at should be None
        payment = self._run(svc.repo.by_order(order["id"]))
        assert payment.release_at is None
        released = self._run(svc.release_due())
        # nothing to release for THIS payment (may release others in DB, but this stays Captured)
        payment = self._run(svc.repo.by_order(order["id"]))
        assert payment.status == "Captured" and payment.held is True

    def test_refund_for_order_noop_without_captured_payment(self, seller_sess, buyer_sess):
        from modules.payments.service import PaymentService
        order, _ = _create_awaiting_order(seller_sess, buyer_sess, 150000)
        # no checkout -> no payment
        db = self._db()
        svc = PaymentService(db)
        # should be a no-op, no error
        self._run(svc.refund_for_order(order["id"]))
        assert self._run(svc.repo.by_order(order["id"])) is None

    def test_refund_captured_payment(self, seller_sess, buyer_sess):
        from modules.payments.service import PaymentService
        order, _ = _create_awaiting_order(seller_sess, buyer_sess, 150000)
        buyer_sess.post(f"{API}/payments/checkout", json={"order_id": order["id"]})
        db = self._db()
        svc = PaymentService(db)
        self._run(svc.refund_for_order(order["id"], reason="dispute"))
        p = self._run(svc.repo.by_order(order["id"]))
        assert p.status == "Refunded" and p.held is False


# ---------- Cancel + refund choreography ----------
class TestCancelChoreography:
    def test_cancel_awaiting_payment_no_refund_needed(self, seller_sess, buyer_sess):
        order, _ = _create_awaiting_order(seller_sess, buyer_sess, 150000)
        # cancel without paying
        r = buyer_sess.post(f"{API}/orders/{order['id']}/cancel")
        assert r.status_code == 200
        assert r.json()["status"] == "Canceled"
        # no payment exists
        g = buyer_sess.get(f"{API}/payments/order/{order['id']}")
        assert g.status_code == 200
        assert g.json()["payment"] is None
