"""Offers domain (Phase 4, DOMAIN-004) API tests.

Covers creation rules (§8), turn model (§7/§9/§10/§11), acceptance atomicity
(INV-005), rejection/cancellation, authz/privacy (§22), and offer list views.
"""
from __future__ import annotations

import os
import uuid

import pytest
import requests

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"

SELLER = {"email": "seller@archivemarket.co", "password": "Seller12345"}


# ---------- helpers / fixtures ----------
def _new_user_payload():
    uid = uuid.uuid4().hex[:8]
    return {"email": f"TEST_off_{uid}@example.com", "password": "Password12345",
            "display_name": f"buyer_{uid}"}


def _register(sess=None):
    sess = sess or requests.Session()
    payload = _new_user_payload()
    r = sess.post(f"{API}/auth/register", json=payload)
    assert r.status_code in (200, 201), r.text
    return sess, r.json()["user"], payload


def _seller_session():
    sess = requests.Session()
    r = sess.post(f"{API}/auth/login", json=SELLER)
    assert r.status_code == 200, r.text
    return sess


def _first_listing_id():
    r = requests.get(f"{API}/listings")
    assert r.status_code == 200
    items = r.json()["items"]
    assert items, "expected at least one seeded listing"
    return items[0]["id"], items[0]["price"]["amount"]


@pytest.fixture
def seller():
    return _seller_session()


@pytest.fixture
def buyer():
    sess, user, _ = _register()
    return sess, user


@pytest.fixture
def listing():
    return _first_listing_id()


def _make_fresh_listing(seller_sess, allow_offers=True, price_amount=400000):
    payload = {
        "title": f"TEST_off_{uuid.uuid4().hex[:6]}", "description": "test",
        "price_amount": price_amount, "currency": "UAH", "brand": "Nike",
        "category": "footwear", "gender": "Men", "size": "42",
        "color": "White", "material": "Leather", "condition": "LIKE_NEW",
        "images": [{"url": "https://example.com/x.jpg"}],
        "allow_offers": allow_offers,
    }
    r = seller_sess.post(f"{API}/listings", json=payload)
    lid = r.json()["listing_id"]
    seller_sess.post(f"{API}/listings/{lid}/publish")
    return lid, price_amount


# ---------- Creation rules (§8) ----------
def test_create_offer_success(buyer, listing):
    sess, _ = buyer
    lid, price = listing
    amount = max(1, price // 2)
    r = sess.post(f"{API}/offers", json={"listing_id": lid, "amount": amount})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "Active"
    assert body["awaiting"] == "seller"
    assert body["current_amount"] == amount
    assert body["listing_id"] == lid


def test_create_offer_own_listing_422(seller, listing):
    lid, _ = listing
    r = seller.post(f"{API}/offers", json={"listing_id": lid, "amount": 10000})
    assert r.status_code == 422, r.text
    assert "CANNOT_OFFER_OWN_LISTING" in str(r.json())


def test_create_offer_amount_must_be_positive(buyer, listing):
    sess, _ = buyer
    lid, _ = listing
    r = sess.post(f"{API}/offers", json={"listing_id": lid, "amount": 0})
    assert r.status_code == 422, r.text


def test_offers_disabled_returns_409(seller):
    """Create a Published listing with allow_offers=False then have a fresh buyer try."""
    payload = {
        "title": "TEST_no_offers", "description": "no offers",
        "price_amount": 300000, "currency": "UAH", "brand": "Nike",
        "category": "footwear", "gender": "Men", "size": "42",
        "color": "White", "material": "Leather", "condition": "LIKE_NEW",
        "images": [{"url": "https://example.com/x.jpg"}],
        "allow_offers": False,
    }
    r = seller.post(f"{API}/listings", json=payload)
    assert r.status_code in (200, 201), r.text
    lid = r.json()["listing_id"]
    pub = seller.post(f"{API}/listings/{lid}/publish")
    assert pub.status_code == 200, pub.text

    buyer_sess, _, _ = _register()
    r2 = buyer_sess.post(f"{API}/offers", json={"listing_id": lid, "amount": 100000})
    assert r2.status_code == 409, r2.text
    assert "OFFERS_DISABLED" in str(r2.json())

    seller.delete(f"{API}/listings/{lid}")


def test_create_offer_unauthenticated_401(listing):
    lid, _ = listing
    r = requests.post(f"{API}/offers", json={"listing_id": lid, "amount": 10000})
    assert r.status_code == 401, r.text


# ---------- Turn model & negotiation ----------
def test_turn_model_counter_and_accept(buyer, seller):
    buyer_sess, buyer_user = buyer
    lid, price = _make_fresh_listing(seller)
    r = buyer_sess.post(f"{API}/offers", json={"listing_id": lid, "amount": max(1, price // 3)})
    assert r.status_code == 200, r.text
    offer_id = r.json()["offer_id"]

    # Buyer tries to accept while awaiting seller -> NOT_YOUR_TURN
    r_bad = buyer_sess.post(f"{API}/offers/{offer_id}/accept")
    assert r_bad.status_code == 409, r_bad.text
    assert "NOT_YOUR_TURN" in str(r_bad.json())

    # Seller counters
    counter_amt = max(2, price // 2)
    rc = seller.post(f"{API}/offers/{offer_id}/counter", json={"amount": counter_amt})
    assert rc.status_code == 200, rc.text
    body = rc.json()
    assert body["awaiting"] == "buyer"
    assert body["current_amount"] == counter_amt
    assert body["status"] == "Active"

    # Seller trying to accept while awaiting buyer -> NOT_YOUR_TURN
    r_s_accept = seller.post(f"{API}/offers/{offer_id}/accept")
    assert r_s_accept.status_code == 409, r_s_accept.text
    assert "NOT_YOUR_TURN" in str(r_s_accept.json())

    # Buyer accepts
    ra = buyer_sess.post(f"{API}/offers/{offer_id}/accept")
    assert ra.status_code == 200, ra.text
    assert ra.json()["status"] == "Accepted"

    # Detail shows history revisions >= 2
    d = buyer_sess.get(f"{API}/offers/{offer_id}")
    assert d.status_code == 200
    assert len(d.json()["offer"]["revisions"]) >= 2


# ---------- Acceptance atomicity (INV-005) ----------
def test_acceptance_atomicity_blocks_other_offers(seller):
    """After one offer is Accepted on a listing, a different buyer's offer on the
    same listing cannot be accepted -> OFFER_ALREADY_ACCEPTED."""
    # Fresh listing to isolate state
    payload = {
        "title": "TEST_atomic", "description": "atomic test",
        "price_amount": 400000, "currency": "UAH", "brand": "Nike",
        "category": "footwear", "gender": "Men", "size": "42",
        "color": "Black", "material": "Leather", "condition": "LIKE_NEW",
        "images": [{"url": "https://example.com/x.jpg"}],
    }
    r = seller.post(f"{API}/listings", json=payload)
    lid = r.json()["listing_id"]
    seller.post(f"{API}/listings/{lid}/publish")

    b1, _, _ = _register()
    b2, _, _ = _register()
    o1 = b1.post(f"{API}/offers", json={"listing_id": lid, "amount": 100000}).json()["offer_id"]
    o2 = b2.post(f"{API}/offers", json={"listing_id": lid, "amount": 120000}).json()["offer_id"]

    # Seller accepts offer 1
    ra = seller.post(f"{API}/offers/{o1}/accept")
    assert ra.status_code == 200, ra.text
    assert ra.json()["status"] == "Accepted"

    # Accepting o1 again -> INVALID_OFFER_STATE
    ra2 = seller.post(f"{API}/offers/{o1}/accept")
    assert ra2.status_code == 409, ra2.text
    assert "INVALID_OFFER_STATE" in str(ra2.json())

    # Accepting o2 should now fail atomically
    rb = seller.post(f"{API}/offers/{o2}/accept")
    assert rb.status_code == 409, rb.text
    assert "OFFER_ALREADY_ACCEPTED" in str(rb.json()), rb.text

    # cleanup: try to archive listing (may fail if Reserved/Sold; ignore)
    seller.delete(f"{API}/listings/{lid}")


# ---------- Rejection & cancellation ----------
def test_reject_then_cannot_accept(buyer, seller, listing):
    buyer_sess, _ = buyer
    lid, price = listing
    r = buyer_sess.post(f"{API}/offers", json={"listing_id": lid, "amount": max(1, price // 4)})
    offer_id = r.json()["offer_id"]

    rj = seller.post(f"{API}/offers/{offer_id}/reject")
    assert rj.status_code == 200, rj.text
    assert rj.json()["status"] == "Rejected"

    # Cannot accept a rejected offer (also NOT_YOUR_TURN would happen; but state check first)
    ra = buyer_sess.post(f"{API}/offers/{offer_id}/accept")
    assert ra.status_code == 409, ra.text
    assert "INVALID_OFFER_STATE" in str(ra.json())


def test_cancel_only_by_buyer(buyer, seller, listing):
    buyer_sess, _ = buyer
    lid, price = listing
    r = buyer_sess.post(f"{API}/offers", json={"listing_id": lid, "amount": max(1, price // 5)})
    offer_id = r.json()["offer_id"]

    # Seller cancel -> 403 FORBIDDEN
    r_sc = seller.post(f"{API}/offers/{offer_id}/cancel")
    assert r_sc.status_code == 403, r_sc.text
    assert "FORBIDDEN" in str(r_sc.json())

    # Buyer cancels
    r_bc = buyer_sess.post(f"{API}/offers/{offer_id}/cancel")
    assert r_bc.status_code == 200, r_bc.text
    assert r_bc.json()["status"] == "Canceled"


# ---------- Authorization & privacy (§22) ----------
def test_third_party_cannot_view_offer(buyer, listing):
    buyer_sess, _ = buyer
    lid, price = listing
    r = buyer_sess.post(f"{API}/offers", json={"listing_id": lid, "amount": max(1, price // 6)})
    offer_id = r.json()["offer_id"]

    third, _, _ = _register()
    d = third.get(f"{API}/offers/{offer_id}")
    assert d.status_code == 403, d.text
    assert "FORBIDDEN" in str(d.json())


def test_offer_endpoints_require_auth(listing):
    lid, _ = listing
    # unauthenticated
    for path in [
        ("POST", f"{API}/offers"),
        ("GET", f"{API}/offers"),
        ("GET", f"{API}/offers/some-id"),
        ("POST", f"{API}/offers/some-id/accept"),
        ("POST", f"{API}/offers/some-id/reject"),
        ("POST", f"{API}/offers/some-id/cancel"),
        ("POST", f"{API}/offers/some-id/counter"),
    ]:
        method, url = path
        body = {"listing_id": lid, "amount": 100} if url.endswith("/offers") and method == "POST" else {"amount": 100}
        r = requests.request(method, url, json=body if method == "POST" else None)
        assert r.status_code == 401, f"{method} {url} -> {r.status_code}: {r.text}"


# ---------- Offer listing views ----------
def test_list_offers_by_box(buyer, seller, listing):
    buyer_sess, _ = buyer
    lid, price = listing
    r = buyer_sess.post(f"{API}/offers", json={"listing_id": lid, "amount": max(1, price // 7)})
    assert r.status_code == 200
    offer_id = r.json()["offer_id"]

    r_buyer = buyer_sess.get(f"{API}/offers", params={"box": "buyer"})
    assert r_buyer.status_code == 200
    ids = [o["id"] for o in r_buyer.json()["items"]]
    assert offer_id in ids

    r_seller = seller.get(f"{API}/offers", params={"box": "seller"})
    assert r_seller.status_code == 200
    ids_s = [o["id"] for o in r_seller.json()["items"]]
    assert offer_id in ids_s


def test_list_offers_for_listing_owner_only(buyer, seller, listing):
    buyer_sess, _ = buyer
    lid, price = listing
    buyer_sess.post(f"{API}/offers", json={"listing_id": lid, "amount": max(1, price // 8)})

    # Seller (owner) can list
    r_ok = seller.get(f"{API}/offers/listing/{lid}")
    assert r_ok.status_code == 200
    assert isinstance(r_ok.json()["items"], list)

    # Third party cannot
    third, _, _ = _register()
    r_bad = third.get(f"{API}/offers/listing/{lid}")
    assert r_bad.status_code == 403, r_bad.text
