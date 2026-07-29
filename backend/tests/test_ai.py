"""AI Enrichment + Analytics (Phase 12, DOMAIN-012/013) — AIJob aggregate lifecycle,
deterministic sandbox provider, fraud flags, advisory enrichment/fraud APIs (owner +
staff authz), auto-enrichment + fraud->moderation choreography on publish, and the
seller + marketplace analytics read models. Requires AI_PROVIDER=sandbox."""
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
ADMIN = {"email": os.environ.get("ADMIN_EMAIL", "admin@archivemarket.co"),
         "password": os.environ.get("ADMIN_PASSWORD", "Admin12345")}


def _login(creds):
    sess = requests.Session()
    r = sess.post(f"{API}/auth/login", json=creds)
    assert r.status_code == 200, r.text
    return sess, r.json()["user"]


def _register(prefix="ai"):
    sess = requests.Session()
    uid = uuid.uuid4().hex[:8]
    r = sess.post(f"{API}/auth/register", json={
        "email": f"TEST_{prefix}_{uid}@example.com",
        "password": "Password12345", "display_name": f"{prefix}_{uid}"})
    assert r.status_code in (200, 201), r.text
    return sess, r.json()["user"]


def _listing(seller_sess, *, title=None, description="A clean pair, worn twice.", price=250000):
    payload = {"title": title or f"TEST_ai_{uuid.uuid4().hex[:6]} sneakers",
               "description": description, "price_amount": price, "currency": "UAH",
               "brand": "Nike", "category": "footwear", "gender": "Men", "size": "42",
               "color": "White", "material": "Leather", "condition": "LIKE_NEW",
               "images": [{"url": "https://example.com/x.jpg"}], "allow_offers": True}
    lid = seller_sess.post(f"{API}/listings", json=payload).json()["listing_id"]
    seller_sess.post(f"{API}/listings/{lid}/publish")
    return lid


@pytest.fixture(scope="module")
def seller():
    return _login(SELLER)


@pytest.fixture(scope="module")
def admin_sess():
    return _login(ADMIN)[0]


# ---------- Domain ----------
class TestAIDomain:
    def _job(self):
        from modules.ai.domain import AIJob
        return AIJob.create(objective="listing_enrichment", subject_type="listing", subject_id="L1")

    def test_create_requires_objective(self):
        from buildingblocks.domain import DomainError
        from modules.ai.domain import AIJob
        with pytest.raises(DomainError):
            AIJob.create(objective="", subject_type="listing", subject_id="L1")

    def test_lifecycle_and_immutability(self):
        from modules.ai.domain import AIAnalysis, AIRecommendation
        j = self._job()
        assert [e.event_type for e in j.pull_events()] == ["AIJobCreated"]
        j.queue(); j.start()
        j.complete(provider="sandbox", model="sandbox-v1", prompt_version="v1",
                   analyses=[AIAnalysis(kind="quality_score", value="70", confidence=0.7)],
                   recommendations=[AIRecommendation(kind="improve_title", message="x", confidence=0.9)])
        assert j.status == "Completed" and len(j.analyses) == 1 and len(j.recommendations) == 1
        types = [e.event_type for e in j.pull_events()]
        assert "AIExecutionCompleted" in types and "AIAnalysisPublished" in types

    def test_invalid_transition(self):
        from buildingblocks.domain import DomainError
        j = self._job()
        with pytest.raises(DomainError):
            j.start()  # cannot go Created -> Running directly

    def test_failure_records_execution(self):
        j = self._job(); j.queue(); j.start()
        j.fail(provider="sandbox", model="sandbox-v1", prompt_version="v1", error="boom")
        assert j.status == "Failed" and j.executions[-1].status == "failed"


# ---------- Sandbox provider ----------
class TestSandboxProvider:
    def test_deterministic(self):
        from modules.ai.provider import SandboxAIProvider
        p = SandboxAIProvider()
        a = asyncio.get_event_loop().run_until_complete(
            p.analyze_listing(title="Nike Air Max", description="great condition sneakers"))
        b = asyncio.get_event_loop().run_until_complete(
            p.analyze_listing(title="Nike Air Max", description="great condition sneakers"))
        assert a == b
        assert 0 <= a["quality_score"]["value"] <= 100

    def test_fraud_flags(self):
        from modules.ai.provider import SandboxAIProvider
        p = SandboxAIProvider()
        out = asyncio.get_event_loop().run_until_complete(
            p.score_fraud(title="replica mirror", description="wire transfer telegram", price=100))
        assert out["risk_score"] >= 0.75
        assert "replica" in out["flags"] and "price_too_low" in out["flags"]


# ---------- Enrichment API ----------
class TestEnrichmentAPI:
    def test_owner_can_run_and_read_enrichment(self, seller):
        sess, _ = seller
        lid = _listing(sess)
        r = sess.post(f"{API}/ai/listings/{lid}/enrich")
        assert r.status_code == 200, r.text
        e = r.json()["enrichment"]
        assert e["status"] == "Completed" and len(e["analyses"]) >= 1
        g = sess.get(f"{API}/ai/listings/{lid}")
        assert g.status_code == 200 and g.json()["enrichment"] is not None

    def test_non_owner_forbidden(self, seller):
        sess, _ = seller
        lid = _listing(sess)
        other, _ = _register()
        r = other.get(f"{API}/ai/listings/{lid}")
        assert r.status_code == 403

    def test_staff_can_view_any(self, seller, admin_sess):
        sess, _ = seller
        lid = _listing(sess)
        sess.post(f"{API}/ai/listings/{lid}/enrich")
        r = admin_sess.get(f"{API}/ai/listings/{lid}")
        assert r.status_code == 200

    def test_fraud_view_staff_only(self, seller, admin_sess):
        sess, _ = seller
        lid = _listing(sess)
        assert sess.get(f"{API}/ai/listings/{lid}/fraud").status_code == 403
        assert admin_sess.get(f"{API}/ai/listings/{lid}/fraud").status_code == 200


# ---------- Choreography: publish -> auto enrich + fraud -> moderation ----------
class TestPublishChoreography:
    def test_suspicious_listing_creates_moderation_signal(self, seller, admin_sess):
        sess, _ = seller
        lid = _listing(sess, title="Nike replica AAA mirror sneakers",
                       description="cheap fake, pay via wire transfer on telegram whatsapp",
                       price=300)
        deadline = time.time() + 20
        fraud = None
        while time.time() < deadline:
            fraud = admin_sess.get(f"{API}/ai/listings/{lid}/fraud").json()["fraud"]
            if fraud:
                break
            time.sleep(2)
        assert fraud is not None and fraud["status"] == "Completed"
        cases = admin_sess.get(f"{API}/moderation/cases").json()
        items = cases if isinstance(cases, list) else cases.get("items", [])
        assert any(c["target_id"] == lid for c in items), "AI fraud signal should open a moderation case"


# ---------- Analytics ----------
class TestAnalytics:
    def test_seller_analytics_shape(self, seller):
        sess, _ = seller
        r = sess.get(f"{API}/analytics/seller")
        assert r.status_code == 200, r.text
        d = r.json()
        for k in ("listings", "sales", "escrow", "offers", "reputation"):
            assert k in d

    def test_marketplace_staff_only(self, seller, admin_sess):
        sess, _ = seller
        assert sess.get(f"{API}/analytics/marketplace").status_code == 403
        r = admin_sess.get(f"{API}/analytics/marketplace")
        assert r.status_code == 200
        d = r.json()
        for k in ("gmv", "orders", "users", "listings", "trust_safety"):
            assert k in d


# ---------- Hardening ----------
class TestHardening:
    def test_security_headers_present(self):
        r = requests.get(f"{API}/health")
        assert r.headers.get("X-Content-Type-Options") == "nosniff"
        assert r.headers.get("X-Frame-Options") == "DENY"

    def test_login_rate_limited(self):
        # forgot-password is the isolated brute-force-sensitive endpoint (limit 5/300s).
        email = f"nobody_{uuid.uuid4().hex}@example.com"
        codes = [requests.post(f"{API}/auth/forgot-password", json={"email": email}).status_code
                 for _ in range(7)]
        assert 429 in codes, f"expected a 429 after the forgot-password limit, got {codes}"
