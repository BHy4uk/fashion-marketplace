"""Backend API integration tests for ARCHIVE fashion marketplace.

Covers: health, identity (register/login/me/logout/refresh/brute force),
listings (search/filter/facets/sort/detail/create/publish/price/archive/ownership),
taxonomy.
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


# ---------- fixtures ----------
@pytest.fixture
def s():
    return requests.Session()


@pytest.fixture
def seller_session():
    sess = requests.Session()
    r = sess.post(f"{API}/auth/login", json=SELLER)
    assert r.status_code == 200, r.text
    return sess


def _new_user_payload():
    uid = uuid.uuid4().hex[:8]
    return {"email": f"TEST_{uid}@example.com", "password": "Password12345",
            "display_name": f"tester_{uid}"}


# ---------- Health ----------
def test_health(s):
    r = s.get(f"{API}/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ---------- Auth: register / duplicate / weak password ----------
def test_register_creates_user_and_cookies(s):
    payload = _new_user_payload()
    r = s.post(f"{API}/auth/register", json=payload)
    assert r.status_code in (200, 201), r.text
    data = r.json()
    assert "user" in data
    assert data["user"]["email"].lower() == payload["email"].lower()
    # httpOnly cookies
    ck = s.cookies.get_dict()
    assert "access_token" in ck, f"cookies={ck}"
    assert "refresh_token" in ck, f"cookies={ck}"

    # /me
    me = s.get(f"{API}/auth/me")
    assert me.status_code == 200
    assert me.json()["user"]["email"].lower() == payload["email"].lower()


def test_register_duplicate_email_409(s):
    payload = _new_user_payload()
    r1 = s.post(f"{API}/auth/register", json=payload)
    assert r1.status_code in (200, 201)
    s2 = requests.Session()
    r2 = s2.post(f"{API}/auth/register", json=payload)
    assert r2.status_code == 409, r2.text
    body = r2.json()
    # error_code should be EMAIL_EXISTS
    ec = body.get("error_code") or body.get("detail", {}).get("error_code") \
         or (body.get("detail") if isinstance(body.get("detail"), str) else None)
    assert "EMAIL_EXISTS" in str(body), f"expected EMAIL_EXISTS in {body}"


def test_register_weak_password_422(s):
    payload = _new_user_payload()
    payload["password"] = "short"
    r = s.post(f"{API}/auth/register", json=payload)
    assert r.status_code == 422, r.text


# ---------- Auth: login / bad creds ----------
def test_login_seed_seller(s):
    r = s.post(f"{API}/auth/login", json=SELLER)
    assert r.status_code == 200, r.text
    ck = s.cookies.get_dict()
    assert "access_token" in ck
    assert "refresh_token" in ck
    assert r.json()["user"]["email"] == SELLER["email"]


def test_login_wrong_password(s):
    r = s.post(f"{API}/auth/login",
               json={"email": SELLER["email"], "password": "wrongPassword123"})
    assert r.status_code == 401, r.text
    assert "INVALID_CREDENTIALS" in str(r.json())


def test_brute_force_lockout():
    # Use a dedicated user so we don't lock the seed seller.
    reg = requests.Session()
    payload = _new_user_payload()
    r = reg.post(f"{API}/auth/register", json=payload)
    assert r.status_code in (200, 201)
    email = payload["email"]
    saw_429 = False
    codes = []
    for _ in range(8):
        rr = requests.post(f"{API}/auth/login",
                           json={"email": email, "password": "BadPassword!!"})
        codes.append(rr.status_code)
        if rr.status_code == 429:
            saw_429 = True
            assert "ACCOUNT_LOCKED" in str(rr.json())
            break
    assert saw_429, f"expected 429 lockout, got {codes}"


def test_me_logout_refresh(seller_session):
    me = seller_session.get(f"{API}/auth/me")
    assert me.status_code == 200

    refresh = seller_session.post(f"{API}/auth/refresh")
    assert refresh.status_code == 200, refresh.text

    logout = seller_session.post(f"{API}/auth/logout")
    assert logout.status_code == 200

    # After logout /me should be 401
    after = seller_session.get(f"{API}/auth/me")
    assert after.status_code == 401


# ---------- Listings: search / filter / facet / sort ----------
def test_search_returns_six_published(s):
    r = s.get(f"{API}/listings")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 6, data
    assert "facets" in data
    for k in ("brand", "category", "condition", "size"):
        assert k in data["facets"]
    # No draft/sold/hidden state values in items
    for item in data["items"]:
        assert item["state"] in ("Published", "Reserved")


def test_search_filter_by_category_footwear(s):
    r = s.get(f"{API}/listings", params={"category": "footwear"})
    assert r.status_code == 200
    data = r.json()
    for it in data["items"]:
        assert it["attributes"]["category"] == "footwear"


def test_search_sort_price_asc_desc(s):
    asc = s.get(f"{API}/listings", params={"sort": "price_asc"}).json()["items"]
    desc = s.get(f"{API}/listings", params={"sort": "price_desc"}).json()["items"]
    if len(asc) >= 2:
        prices = [i["price"]["amount"] for i in asc]
        assert prices == sorted(prices)
    if len(desc) >= 2:
        prices = [i["price"]["amount"] for i in desc]
        assert prices == sorted(prices, reverse=True)


def test_search_min_max_price(s):
    r = s.get(f"{API}/listings", params={"min_price": 100000, "max_price": 500000})
    assert r.status_code == 200
    for it in r.json()["items"]:
        assert 100000 <= it["price"]["amount"] <= 500000


def test_search_pagination(s):
    r = s.get(f"{API}/listings", params={"page": 1, "page_size": 2})
    assert r.status_code == 200
    data = r.json()
    assert data["page"] == 1 and data["page_size"] == 2
    assert len(data["items"]) <= 2


# ---------- Listing detail ----------
def test_listing_detail_by_slug(s):
    items = s.get(f"{API}/listings").json()["items"]
    assert items
    slug = items[0]["slug"]
    r = s.get(f"{API}/listings/{slug}")
    assert r.status_code == 200
    lst = r.json()["listing"]
    assert lst["slug"] == slug
    assert "seller" in lst
    assert lst["seller"]["display_name"]


def test_listing_detail_unknown_404(s):
    r = s.get(f"{API}/listings/does-not-exist-xyz")
    assert r.status_code == 404
    assert "LISTING_NOT_FOUND" in str(r.json())


# ---------- Listing lifecycle: create -> publish incomplete -> complete -> price -> archive ----------
def test_incomplete_publish_returns_422(seller_session):
    # missing category, condition, images
    payload = {"title": "TEST_incomplete", "price_amount": 100000, "brand": "Nike"}
    r = seller_session.post(f"{API}/listings", json=payload)
    assert r.status_code in (200, 201), r.text
    lid = r.json()["listing_id"]
    r2 = seller_session.post(f"{API}/listings/{lid}/publish")
    assert r2.status_code == 422, r2.text
    assert "INCOMPLETE_LISTING" in str(r2.json())
    # cleanup
    seller_session.delete(f"{API}/listings/{lid}")


def test_full_listing_lifecycle_and_ownership(seller_session):
    payload = {
        "title": "TEST_full_listing",
        "description": "test item",
        "price_amount": 200000,
        "currency": "UAH",
        "brand": "Nike",
        "category": "footwear",
        "gender": "Men",
        "size": "42",
        "color": "White",
        "material": "Leather",
        "condition": "LIKE_NEW",
        "images": [{"url": "https://example.com/x.jpg"}],
    }
    r = seller_session.post(f"{API}/listings", json=payload)
    assert r.status_code in (200, 201), r.text
    lid = r.json()["listing_id"]

    # publish OK
    pub = seller_session.post(f"{API}/listings/{lid}/publish")
    assert pub.status_code == 200, pub.text
    assert pub.json()["state"] == "Published"

    # Detail visible
    d = requests.get(f"{API}/listings/{lid}")
    assert d.status_code == 200

    # Ownership: another user cannot re-price
    other = requests.Session()
    other.post(f"{API}/auth/register", json=_new_user_payload())
    r_forbid = other.patch(f"{API}/listings/{lid}/price", json={"amount": 999999})
    assert r_forbid.status_code == 403, r_forbid.text
    assert "FORBIDDEN" in str(r_forbid.json())

    # Owner can change price
    pr = seller_session.patch(f"{API}/listings/{lid}/price", json={"amount": 250000})
    assert pr.status_code == 200
    assert pr.json()["price"] == 250000

    # Archive (soft delete)
    ar = seller_session.delete(f"{API}/listings/{lid}")
    assert ar.status_code == 200

    # After archive - not in search
    listings = requests.get(f"{API}/listings", params={"page_size": 48}).json()["items"]
    ids = [i["id"] for i in listings]
    assert lid not in ids

    # Detail returns 404
    d2 = requests.get(f"{API}/listings/{lid}")
    assert d2.status_code == 404


# ---------- Taxonomy ----------
def test_taxonomy_categories(s):
    r = s.get(f"{API}/taxonomy/categories")
    assert r.status_code == 200
    body = r.json()
    cats = body if isinstance(body, list) else body.get("items") or body.get("categories") or []
    assert len(cats) == 12, f"expected 12 categories, got {len(cats)}: {body}"


def test_taxonomy_brands_meta(s):
    rb = s.get(f"{API}/taxonomy/brands")
    assert rb.status_code == 200
    rm = s.get(f"{API}/taxonomy/meta")
    assert rm.status_code == 200
    meta = rm.json()
    # expect conditions/genders/sizes/currencies keys somewhere
    keys = set(meta.keys()) if isinstance(meta, dict) else set()
    for k in ("conditions", "genders", "sizes", "currencies"):
        assert k in keys, f"missing {k} in meta {keys}"
