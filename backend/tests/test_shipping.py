"""Shipping (Phase 7, DOMAIN-007) — fulfilment state machine, carrier provider
abstraction, and the choreography that closes the escrow loop end-to-end.
Requires SHIPPING_PROVIDER=sandbox and PAYMENT_PROVIDER=sandbox."""
from __future__ import annotations

import asyncio
import os
import time
import uuid

import pytest
import requests

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"

SELLER = {"email": "seller@archivemarket.co", "password": "Seller12345"}


# ---------- helpers ----------
def _register(prefix="ship"):
    sess = requests.Session()
    uid = uuid.uuid4().hex[:8]
    r = sess.post(f"{API}/auth/register", json={
        "email": f"TEST_{prefix}_{uid}@example.com",
        "password": "Password12345", "display_name": f"{prefix}_{uid}"})
    assert r.status_code in (200, 201), r.text
    return sess, r.json()["user"]


def _login(creds):
    sess = requests.Session()
    r = sess.post(f"{API}/auth/login", json=creds)
    assert r.status_code == 200, r.text
    return sess


def _make_fresh_listing(seller_sess, price_amount=400000):
    payload = {
        "title": f"TEST_ship_{uuid.uuid4().hex[:6]}", "description": "test",
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


def _create_paid_order(seller_sess, buyer_sess, amount=150000):
    """Create an order and pay it (sandbox capture). Returns the order dict once Paid."""
    lid = _make_fresh_listing(seller_sess)
    r = buyer_sess.post(f"{API}/offers", json={"listing_id": lid, "amount": amount})
    assert r.status_code == 200, r.text
    offer_id = r.json()["offer_id"]
    ra = seller_sess.post(f"{API}/offers/{offer_id}/accept")
    assert ra.status_code == 200, ra.text
    # poll for order
    order = None
    end = time.time() + 8
    while time.time() < end and not order:
        r = buyer_sess.get(f"{API}/orders", params={"box": "buyer"})
        for o in r.json()["items"]:
            if o.get("offer_id") == offer_id:
                order = o
                break
        if not order:
            time.sleep(0.4)
    assert order, "order not created"
    pr = buyer_sess.post(f"{API}/payments/checkout", json={"order_id": order["id"]})
    assert pr.status_code == 200, pr.text
    return order


def _poll_order_status(sess, order_id, target, timeout=12.0):
    end = time.time() + timeout
    while time.time() < end:
        r = sess.get(f"{API}/orders/{order_id}")
        if r.status_code == 200 and r.json()["order"]["status"] == target:
            return r.json()["order"]
        time.sleep(0.4)
    return None


def _poll_shipment(sess, order_id, timeout=12.0):
    end = time.time() + timeout
    while time.time() < end:
        r = sess.get(f"{API}/shipments/order/{order_id}")
        if r.status_code == 200 and r.json().get("shipment"):
            return r.json()["shipment"]
        time.sleep(0.4)
    return None


@pytest.fixture(scope="module")
def seller_sess():
    return _login(SELLER)


@pytest.fixture
def buyer_sess():
    sess, _ = _register("ship")
    return sess


# ---------- Domain unit tests (Shipment aggregate) ----------
class TestShipmentDomain:
    def _make(self):
        from modules.shipping.domain import Shipment
        return Shipment.create(order_id="o1", buyer_id="b", seller_id="s",
                               listing_id="l1", carrier="sandbox")

    def test_valid_lifecycle(self):
        s = self._make()
        assert s.status == "Pending"
        s.assign_label(tracking_number="TRK1", carrier_ref="ref1")
        assert s.status == "LabelCreated" and s.tracking_number == "TRK1"
        s.dispatch()
        assert s.status == "Dispatched"
        assert s.mark_in_transit("moving") is True
        assert s.status == "InTransit"
        s.mark_delivered("delivered")
        assert s.status == "Delivered"
        statuses = [e.status for e in s.tracking_events]
        assert statuses == ["LabelCreated", "Dispatched", "InTransit", "Delivered"]

    def test_delivered_directly_from_dispatched(self):
        s = self._make()
        s.assign_label(tracking_number="TRK2")
        s.dispatch()
        s.mark_delivered()
        assert s.status == "Delivered"

    def test_invalid_transitions_raise(self):
        from buildingblocks.domain import DomainError
        s = self._make()
        with pytest.raises(DomainError) as e:
            s.dispatch()  # cannot dispatch from Pending (needs label)
        assert e.value.code == "INVALID_SHIPMENT_STATE"

    def test_mark_in_transit_is_idempotent_noop(self):
        s = self._make()
        s.assign_label(tracking_number="T")
        s.dispatch()
        assert s.mark_in_transit() is True
        assert s.mark_in_transit() is False  # already InTransit

    def test_cancel_from_pending(self):
        s = self._make()
        s.cancel("no stock")
        assert s.status == "Canceled"

    def test_events_emitted(self):
        s = self._make()
        evts = [e.event_type for e in s.pull_events()]
        assert evts == ["ShipmentCreated"]
        s.assign_label(tracking_number="T")
        s.dispatch()
        evts = [e.event_type for e in s.pull_events()]
        assert evts == ["ShipmentLabelCreated", "ShipmentDispatched"]


# ---------- Provider abstraction ----------
class TestShippingProvider:
    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def test_sandbox_create_and_track(self):
        from modules.shipping.provider import SandboxShippingProvider
        prov = SandboxShippingProvider()
        out = self._run(prov.create_shipment(order_id="o1", to_address={}, from_address={},
                                             parcel={}, description="d"))
        assert out["tracking_number"].startswith("SBX")
        assert out["carrier_ref"]
        t = self._run(prov.get_tracking(tracking_number=out["tracking_number"]))
        assert t["status"] == "in_transit"

    def test_novaposhta_status_mapping(self):
        from modules.shipping.provider import _NP_STATUS
        assert _NP_STATUS["9"] == "delivered"
        assert _NP_STATUS["4"] == "in_transit"
        assert _NP_STATUS["2"] == "canceled"
        assert _NP_STATUS["102"] == "returned"

    def test_build_provider_sandbox_by_default(self, monkeypatch):
        from modules.shipping.provider import build_provider, SandboxShippingProvider
        monkeypatch.delenv("SHIPPING_PROVIDER", raising=False)
        assert isinstance(build_provider(), SandboxShippingProvider)

    def test_build_provider_novaposhta_requires_key(self, monkeypatch):
        from modules.shipping.provider import build_provider
        monkeypatch.setenv("SHIPPING_PROVIDER", "novaposhta")
        monkeypatch.delenv("NOVAPOSHTA_API_KEY", raising=False)
        with pytest.raises(RuntimeError):
            build_provider()


# ---------- API + choreography (the escrow loop) ----------
class TestShippingChoreography:
    def test_shipment_created_on_order_paid(self, seller_sess, buyer_sess):
        order = _create_paid_order(seller_sess, buyer_sess)
        shipment = _poll_shipment(buyer_sess, order["id"])
        assert shipment is not None, "shipment not created from OrderPaid event"
        assert shipment["carrier"] == "sandbox"
        assert shipment["status"] == "Pending"
        # order auto-advances Paid -> PreparingShipment via ShipmentCreated
        prep = _poll_order_status(buyer_sess, order["id"], "PreparingShipment")
        assert prep is not None, "order did not reach PreparingShipment"

    def test_seller_dispatch_marks_order_shipped(self, seller_sess, buyer_sess):
        order = _create_paid_order(seller_sess, buyer_sess)
        shipment = _poll_shipment(seller_sess, order["id"])
        assert shipment
        _poll_order_status(seller_sess, order["id"], "PreparingShipment")
        r = seller_sess.post(f"{API}/shipments/{shipment['id']}/dispatch", json={})
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "Dispatched"
        assert r.json()["tracking_number"]
        shipped = _poll_order_status(seller_sess, order["id"], "Shipped")
        assert shipped is not None, "order did not reach Shipped after dispatch"

    def test_only_seller_can_dispatch(self, seller_sess, buyer_sess):
        order = _create_paid_order(seller_sess, buyer_sess)
        shipment = _poll_shipment(buyer_sess, order["id"])
        assert shipment
        _poll_order_status(buyer_sess, order["id"], "PreparingShipment")
        r = buyer_sess.post(f"{API}/shipments/{shipment['id']}/dispatch", json={})
        assert r.status_code == 403
        assert "UNAUTHORIZED_ACCESS" in str(r.json())

    def test_full_loop_delivery_completes_order_and_schedules_escrow(self, seller_sess, buyer_sess):
        order = _create_paid_order(seller_sess, buyer_sess)
        shipment = _poll_shipment(seller_sess, order["id"])
        assert shipment
        _poll_order_status(seller_sess, order["id"], "PreparingShipment")
        # seller dispatches
        seller_sess.post(f"{API}/shipments/{shipment['id']}/dispatch", json={})
        assert _poll_order_status(seller_sess, order["id"], "Shipped") is not None
        # buyer confirms delivery
        r = buyer_sess.post(f"{API}/shipments/{shipment['id']}/confirm-delivery")
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "Delivered"
        # order auto-completes via ShipmentDelivered event
        completed = _poll_order_status(buyer_sess, order["id"], "Completed")
        assert completed is not None, "order did not auto-complete on delivery"
        states = [h["to_status"] for h in completed["status_history"]]
        assert states == ["Created", "AwaitingPayment", "Paid", "PreparingShipment",
                          "Shipped", "Delivered", "Completed"]
        # escrow payout was scheduled (release_at set on the captured payment)
        end = time.time() + 8
        release_at = None
        while time.time() < end:
            g = buyer_sess.get(f"{API}/payments/order/{order['id']}")
            p = g.json()["payment"]
            if p and p.get("release_at"):
                release_at = p["release_at"]
                break
            time.sleep(0.4)
        assert release_at is not None, "escrow payout release_at was not scheduled on completion"

    def test_only_buyer_can_confirm_delivery(self, seller_sess, buyer_sess):
        order = _create_paid_order(seller_sess, buyer_sess)
        shipment = _poll_shipment(seller_sess, order["id"])
        assert shipment
        _poll_order_status(seller_sess, order["id"], "PreparingShipment")
        seller_sess.post(f"{API}/shipments/{shipment['id']}/dispatch", json={})
        r = seller_sess.post(f"{API}/shipments/{shipment['id']}/confirm-delivery")
        assert r.status_code == 403
        assert "UNAUTHORIZED_ACCESS" in str(r.json())

    def test_track_advances_to_in_transit(self, seller_sess, buyer_sess):
        order = _create_paid_order(seller_sess, buyer_sess)
        shipment = _poll_shipment(seller_sess, order["id"])
        assert shipment
        _poll_order_status(seller_sess, order["id"], "PreparingShipment")
        seller_sess.post(f"{API}/shipments/{shipment['id']}/dispatch", json={})
        r = seller_sess.post(f"{API}/shipments/{shipment['id']}/track")
        assert r.status_code == 200, r.text
        assert r.json()["shipment"]["status"] == "InTransit"

    def test_non_participant_cannot_read_shipment(self, seller_sess, buyer_sess):
        order = _create_paid_order(seller_sess, buyer_sess)
        _poll_shipment(buyer_sess, order["id"])
        third, _ = _register("third")
        r = third.get(f"{API}/shipments/order/{order['id']}")
        assert r.status_code == 403
