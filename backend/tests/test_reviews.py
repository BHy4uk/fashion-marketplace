"""Reviews (Phase 8, DOMAIN-008) — aggregate lifecycle, eligibility, duplicate
prevention, seller responses, moderation, and the ReviewPublished -> reputation
choreography with Identity. Requires SHIPPING_PROVIDER=sandbox, PAYMENT_PROVIDER=sandbox."""
from __future__ import annotations

import os
import time
import uuid

import pytest
import requests

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"

SELLER = {"email": "seller@archivemarket.co", "password": "Seller12345"}
ADMIN = {"email": os.environ.get("ADMIN_EMAIL", "admin@archivemarket.co"),
         "password": os.environ.get("ADMIN_PASSWORD", "Admin12345")}


# ---------- helpers ----------
def _register(prefix="rev"):
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
    return sess, r.json()["user"]


def _make_fresh_listing(seller_sess):
    payload = {
        "title": f"TEST_rev_{uuid.uuid4().hex[:6]}", "description": "test",
        "price_amount": 400000, "currency": "UAH", "brand": "Nike",
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


def _poll_order_status(sess, order_id, target, timeout=14.0):
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


def _completed_order(seller_sess, buyer_sess, amount=150000):
    """Drive a fresh order all the way to Completed and return the order dict."""
    lid = _make_fresh_listing(seller_sess)
    r = buyer_sess.post(f"{API}/offers", json={"listing_id": lid, "amount": amount})
    assert r.status_code == 200, r.text
    offer_id = r.json()["offer_id"]
    ra = seller_sess.post(f"{API}/offers/{offer_id}/accept")
    assert ra.status_code == 200, ra.text
    order = None
    end = time.time() + 8
    while time.time() < end and not order:
        for o in buyer_sess.get(f"{API}/orders", params={"box": "buyer"}).json()["items"]:
            if o.get("offer_id") == offer_id:
                order = o
                break
        if not order:
            time.sleep(0.4)
    assert order, "order not created"
    assert buyer_sess.post(f"{API}/payments/checkout", json={"order_id": order["id"]}).status_code == 200
    assert _poll_order_status(buyer_sess, order["id"], "PreparingShipment")
    shipment = _poll_shipment(seller_sess, order["id"])
    assert shipment
    assert seller_sess.post(f"{API}/shipments/{shipment['id']}/dispatch", json={}).status_code == 200
    assert _poll_order_status(seller_sess, order["id"], "Shipped")
    assert buyer_sess.post(f"{API}/shipments/{shipment['id']}/confirm-delivery").status_code == 200
    completed = _poll_order_status(buyer_sess, order["id"], "Completed")
    assert completed, "order did not reach Completed"
    return order


@pytest.fixture(scope="module")
def seller():
    return _login(SELLER)


@pytest.fixture(scope="module")
def admin_sess():
    return _login(ADMIN)[0]


@pytest.fixture
def buyer():
    return _register("rev")


# ---------- Domain unit tests ----------
class TestReviewDomain:
    def _make(self, rating=5, comment="great"):
        from modules.reviews.domain import Review
        return Review.create(order_id="o1", author_id="a", recipient_id="b",
                             rating=rating, comment=comment)

    def test_create_publishes_and_emits(self):
        r = self._make()
        assert r.status == "Published"
        evts = [e.event_type for e in r.pull_events()]
        assert evts == ["ReviewPublished"]

    def test_invalid_rating_rejected(self):
        from buildingblocks.domain import DomainError
        for bad in (0, 6, -1):
            with pytest.raises(DomainError) as e:
                self._make(rating=bad)
            assert e.value.code == "INVALID_RATING"

    def test_author_recipient_must_differ(self):
        from buildingblocks.domain import DomainError
        from modules.reviews.domain import Review
        with pytest.raises(DomainError) as e:
            Review.create(order_id="o", author_id="x", recipient_id="x", rating=5)
        assert e.value.code == "UNAUTHORIZED_REVIEWER"

    def test_response_once_only(self):
        from buildingblocks.domain import DomainError
        r = self._make()
        r.pull_events()
        r.add_response("b", "thanks!")
        assert r.response is not None
        with pytest.raises(DomainError) as e:
            r.add_response("b", "again")
        assert e.value.code == "RESPONSE_EXISTS"

    def test_moderation_transitions(self):
        from buildingblocks.domain import DomainError
        r = self._make()
        r.hide("mod")
        assert r.status == "Hidden"
        r.unhide("mod")
        assert r.status == "Published"
        r.remove("mod")
        assert r.status == "Removed"
        with pytest.raises(DomainError) as e:
            r.hide("mod")  # cannot transition from Removed
        assert e.value.code == "INVALID_REVIEW_STATE"

    def test_cannot_respond_to_removed(self):
        from buildingblocks.domain import DomainError
        r = self._make()
        r.remove("mod")
        with pytest.raises(DomainError) as e:
            r.add_response("b", "hi")
        assert e.value.code == "REVIEW_REMOVED"


# ---------- API + choreography ----------
class TestReviewsAPI:
    def test_cannot_review_incomplete_order(self, seller, buyer):
        seller_sess, _ = seller
        buyer_sess, _ = buyer
        # make an AwaitingPayment order (not completed)
        lid = _make_fresh_listing(seller_sess)
        r = buyer_sess.post(f"{API}/offers", json={"listing_id": lid, "amount": 120000})
        offer_id = r.json()["offer_id"]
        seller_sess.post(f"{API}/offers/{offer_id}/accept")
        order = None
        end = time.time() + 8
        while time.time() < end and not order:
            for o in buyer_sess.get(f"{API}/orders", params={"box": "buyer"}).json()["items"]:
                if o.get("offer_id") == offer_id:
                    order = o
            if not order:
                time.sleep(0.4)
        rr = buyer_sess.post(f"{API}/reviews", json={"order_id": order["id"], "rating": 5})
        assert rr.status_code == 409
        assert "ORDER_NOT_COMPLETED" in str(rr.json())

    def test_buyer_reviews_seller_and_reputation_updates(self, seller, buyer):
        seller_sess, seller_user = seller
        buyer_sess, _ = buyer
        order = _completed_order(seller_sess, buyer_sess)
        rr = buyer_sess.post(f"{API}/reviews",
                             json={"order_id": order["id"], "rating": 5, "comment": "Perfect!"})
        assert rr.status_code == 200, rr.text
        assert rr.json()["status"] == "Published"
        assert rr.json()["recipient_id"] == seller_user["id"]
        # reputation updates asynchronously via ReviewPublished -> Identity
        end = time.time() + 12
        found = False
        while time.time() < end:
            body = requests.get(f"{API}/reviews/user/{seller_user['id']}").json()
            item_present = any(i["order_id"] == order["id"] for i in body["items"])
            if item_present and body["completed_reviews"] >= 1 and body["average_rating"] >= 1:
                found = True
                break
            time.sleep(0.5)
        assert found, "review did not surface / reputation not updated"

    def test_reputation_deterministic_on_fresh_recipient(self, seller, buyer):
        # seller reviews the fresh buyer -> buyer starts at 0 reviews => deterministic
        seller_sess, _ = seller
        buyer_sess, buyer_user = buyer
        order = _completed_order(seller_sess, buyer_sess)
        rr = seller_sess.post(f"{API}/reviews",
                              json={"order_id": order["id"], "rating": 4, "comment": "Smooth buyer"})
        assert rr.status_code == 200, rr.text
        end = time.time() + 10
        ok = False
        while time.time() < end:
            body = requests.get(f"{API}/reviews/user/{buyer_user['id']}").json()
            if body["completed_reviews"] == 1:
                assert body["average_rating"] == 4.0
                ok = True
                break
            time.sleep(0.5)
        assert ok, "fresh recipient reputation not exactly 1 review @ 4.0"

    def test_both_directions_allowed(self, seller, buyer):
        seller_sess, _ = seller
        buyer_sess, _ = buyer
        order = _completed_order(seller_sess, buyer_sess)
        assert buyer_sess.post(f"{API}/reviews", json={"order_id": order["id"], "rating": 5}).status_code == 200
        assert seller_sess.post(f"{API}/reviews", json={"order_id": order["id"], "rating": 5}).status_code == 200
        items = seller_sess.get(f"{API}/reviews/order/{order['id']}").json()["items"]
        assert len(items) == 2

    def test_duplicate_review_prevented(self, seller, buyer):
        seller_sess, _ = seller
        buyer_sess, _ = buyer
        order = _completed_order(seller_sess, buyer_sess)
        assert buyer_sess.post(f"{API}/reviews", json={"order_id": order["id"], "rating": 5}).status_code == 200
        dup = buyer_sess.post(f"{API}/reviews", json={"order_id": order["id"], "rating": 3})
        assert dup.status_code == 409
        assert "DUPLICATE_REVIEW" in str(dup.json())

    def test_non_participant_cannot_review(self, seller, buyer):
        seller_sess, _ = seller
        buyer_sess, _ = buyer
        order = _completed_order(seller_sess, buyer_sess)
        third, _ = _register("third")
        rr = third.post(f"{API}/reviews", json={"order_id": order["id"], "rating": 5})
        assert rr.status_code == 403
        assert "UNAUTHORIZED_REVIEWER" in str(rr.json())

    def test_seller_response_once(self, seller, buyer):
        seller_sess, _ = seller
        buyer_sess, _ = buyer
        order = _completed_order(seller_sess, buyer_sess)
        rid = buyer_sess.post(f"{API}/reviews",
                              json={"order_id": order["id"], "rating": 5}).json()["review_id"]
        # recipient (seller) responds
        r1 = seller_sess.post(f"{API}/reviews/{rid}/response", json={"comment": "Thank you!"})
        assert r1.status_code == 200, r1.text
        assert r1.json()["has_response"] is True
        # second response rejected
        r2 = seller_sess.post(f"{API}/reviews/{rid}/response", json={"comment": "again"})
        assert r2.status_code == 409
        # non-recipient cannot respond
        r3 = buyer_sess.post(f"{API}/reviews/{rid}/response", json={"comment": "hi"})
        assert r3.status_code == 403

    def test_eligibility_endpoint(self, seller, buyer):
        seller_sess, _ = seller
        buyer_sess, _ = buyer
        order = _completed_order(seller_sess, buyer_sess)
        el = buyer_sess.get(f"{API}/reviews/eligibility/{order['id']}").json()
        assert el["can_review"] is True and el["already_reviewed"] is False
        buyer_sess.post(f"{API}/reviews", json={"order_id": order["id"], "rating": 5})
        el2 = buyer_sess.get(f"{API}/reviews/eligibility/{order['id']}").json()
        assert el2["already_reviewed"] is True and el2["can_review"] is False


# ---------- Moderation ----------
class TestModeration:
    def test_moderator_hide_removes_from_public_list(self, seller, buyer, admin_sess):
        seller_sess, seller_user = seller
        buyer_sess, _ = buyer
        order = _completed_order(seller_sess, buyer_sess)
        rid = buyer_sess.post(f"{API}/reviews",
                              json={"order_id": order["id"], "rating": 2,
                                    "comment": "spammy"}).json()["review_id"]
        # visible publicly first
        end = time.time() + 8
        while time.time() < end:
            pub = requests.get(f"{API}/reviews/user/{seller_user['id']}").json()["items"]
            if any(i["id"] == rid for i in pub):
                break
            time.sleep(0.4)
        # hide as admin
        h = admin_sess.post(f"{API}/reviews/{rid}/hide")
        assert h.status_code == 200 and h.json()["status"] == "Hidden"
        pub = requests.get(f"{API}/reviews/user/{seller_user['id']}").json()["items"]
        assert not any(i["id"] == rid for i in pub), "hidden review still public"

    def test_participant_cannot_moderate(self, seller, buyer):
        seller_sess, _ = seller
        buyer_sess, _ = buyer
        order = _completed_order(seller_sess, buyer_sess)
        rid = buyer_sess.post(f"{API}/reviews",
                              json={"order_id": order["id"], "rating": 1}).json()["review_id"]
        r = seller_sess.post(f"{API}/reviews/{rid}/hide")
        assert r.status_code == 403

    def test_admin_remove_review(self, seller, buyer, admin_sess):
        seller_sess, _ = seller
        buyer_sess, _ = buyer
        order = _completed_order(seller_sess, buyer_sess)
        rid = buyer_sess.post(f"{API}/reviews",
                              json={"order_id": order["id"], "rating": 3}).json()["review_id"]
        rm = admin_sess.post(f"{API}/reviews/{rid}/remove")
        assert rm.status_code == 200 and rm.json()["status"] == "Removed"
