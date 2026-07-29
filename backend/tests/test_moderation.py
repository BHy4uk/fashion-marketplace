"""Moderation (Phase 11, DOMAIN-011) — case aggregate lifecycle, report intake with
merging + dedup, evidence immutability, append-only decisions, permissions, and
decision ENFORCEMENT into owning modules (Reviews/Listings/Identity).
Requires PAYMENT_PROVIDER=sandbox / SHIPPING_PROVIDER=sandbox."""
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


def _register(prefix="mod"):
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


def _fresh_listing(seller_sess):
    payload = {"title": f"TEST_mod_{uuid.uuid4().hex[:6]}", "description": "test",
               "price_amount": 250000, "currency": "UAH", "brand": "Nike",
               "category": "footwear", "gender": "Men", "size": "42", "color": "White",
               "material": "Leather", "condition": "LIKE_NEW",
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


@pytest.fixture
def reporter():
    return _register("mod")


# ---------- Domain ----------
class TestModerationDomain:
    def _case(self):
        from modules.moderation.domain import ModerationCase, Report
        return ModerationCase.open(target_type="listing", target_id="L1", target_context={},
                                   report=Report(reporter_id="r1", reason="counterfeit"))

    def test_open_emits_events(self):
        c = self._case()
        assert c.status == "Created" and len(c.reports) == 1
        assert [e.event_type for e in c.pull_events()] == ["ModerationCaseCreated", "ReportSubmitted"]

    def test_lifecycle_and_decision_append_only(self):
        from modules.moderation.domain import ModerationDecision
        c = self._case(); c.pull_events()
        c.start_investigation("mod1"); assert c.status == "Investigation"
        c.record_decision(ModerationDecision(action="Warning", reason="first offense", moderator_id="mod1"))
        assert c.status == "DecisionMade" and len(c.decisions) == 1
        c.record_decision(ModerationDecision(action="ListingRemoved", reason="repeat", moderator_id="mod1"))
        assert len(c.decisions) == 2      # append-only, never overwrite (INV-004)
        c.close("mod1"); assert c.status == "Closed"

    def test_closed_case_readonly(self):
        from buildingblocks.domain import DomainError
        from modules.moderation.domain import Evidence, ModerationDecision
        c = self._case(); c.pull_events()
        c.record_decision(ModerationDecision(action="NoAction", reason="ok", moderator_id="m"))
        c.close("m")
        with pytest.raises(DomainError) as e:
            c.add_evidence(Evidence(kind="listing", ref="L1"))
        assert e.value.code == "INVALID_CASE_STATE"

    def test_invalid_action_rejected(self):
        from buildingblocks.domain import DomainError
        from modules.moderation.domain import ModerationDecision
        c = self._case(); c.pull_events()
        with pytest.raises(DomainError) as e:
            c.record_decision(ModerationDecision(action="Nuke", reason="x", moderator_id="m"))
        assert e.value.code == "INVALID_DECISION_ACTION"

    def test_close_requires_decision(self):
        from buildingblocks.domain import DomainError
        c = self._case(); c.pull_events()
        with pytest.raises(DomainError):
            c.close("m")


# ---------- Report intake ----------
class TestReportIntake:
    def test_report_creates_case(self, seller, reporter):
        seller_sess, _ = seller
        rep_sess, _ = reporter
        lid = _fresh_listing(seller_sess)
        r = rep_sess.post(f"{API}/moderation/reports",
                          json={"target_type": "listing", "target_id": lid, "reason": "counterfeit"})
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "Created"

    def test_reports_merge_into_one_case(self, seller, reporter):
        seller_sess, _ = seller
        rep1, _ = reporter
        rep2, _ = _register("mod2")
        lid = _fresh_listing(seller_sess)
        c1 = rep1.post(f"{API}/moderation/reports",
                       json={"target_type": "listing", "target_id": lid, "reason": "fake"}).json()["case_id"]
        c2 = rep2.post(f"{API}/moderation/reports",
                       json={"target_type": "listing", "target_id": lid, "reason": "fake too"}).json()["case_id"]
        assert c1 == c2, "second report should merge into the same open case (§9)"

    def test_duplicate_report_rejected(self, seller, reporter):
        seller_sess, _ = seller
        rep_sess, _ = reporter
        lid = _fresh_listing(seller_sess)
        rep_sess.post(f"{API}/moderation/reports",
                      json={"target_type": "listing", "target_id": lid, "reason": "a"})
        dup = rep_sess.post(f"{API}/moderation/reports",
                            json={"target_type": "listing", "target_id": lid, "reason": "b"})
        assert dup.status_code == 409 and "DUPLICATE_REPORT" in str(dup.json())


# ---------- Permissions ----------
class TestPermissions:
    def test_non_staff_cannot_access_cases(self, seller, reporter):
        seller_sess, _ = seller
        rep_sess, _ = reporter
        lid = _fresh_listing(seller_sess)
        cid = rep_sess.post(f"{API}/moderation/reports",
                            json={"target_type": "listing", "target_id": lid, "reason": "x"}).json()["case_id"]
        assert rep_sess.get(f"{API}/moderation/cases").status_code == 403
        assert rep_sess.get(f"{API}/moderation/cases/{cid}").status_code == 403
        assert rep_sess.post(f"{API}/moderation/cases/{cid}/decision",
                             json={"action": "NoAction", "reason": "x"}).status_code == 403

    def test_staff_can_list_and_view(self, seller, reporter, admin_sess):
        seller_sess, _ = seller
        rep_sess, _ = reporter
        lid = _fresh_listing(seller_sess)
        cid = rep_sess.post(f"{API}/moderation/reports",
                            json={"target_type": "listing", "target_id": lid, "reason": "y"}).json()["case_id"]
        lst = admin_sess.get(f"{API}/moderation/cases", params={"status": "Created"})
        assert lst.status_code == 200 and any(c["id"] == cid for c in lst.json()["items"])
        detail = admin_sess.get(f"{API}/moderation/cases/{cid}")
        assert detail.status_code == 200 and detail.json()["target_id"] == lid


# ---------- Enforcement ----------
class TestEnforcement:
    def test_listing_removed_takes_down_listing(self, seller, reporter, admin_sess):
        seller_sess, _ = seller
        rep_sess, _ = reporter
        lid = _fresh_listing(seller_sess)
        assert requests.get(f"{API}/listings/{lid}").status_code == 200
        cid = rep_sess.post(f"{API}/moderation/reports",
                            json={"target_type": "listing", "target_id": lid, "reason": "counterfeit"}).json()["case_id"]
        admin_sess.post(f"{API}/moderation/cases/{cid}/investigate")
        d = admin_sess.post(f"{API}/moderation/cases/{cid}/decision",
                            json={"action": "ListingRemoved", "reason": "confirmed counterfeit"})
        assert d.status_code == 200, d.text
        # listing is now taken down (no longer publicly retrievable as active)
        end = time.time() + 6
        gone = False
        while time.time() < end:
            resp = requests.get(f"{API}/listings/{lid}")
            if resp.status_code == 404 or (resp.status_code == 200 and resp.json().get("listing", {}).get("state") in ("Deleted", "Archived")):
                gone = True
                break
            time.sleep(0.4)
        assert gone, "listing was not taken down by the moderation decision"
        admin_sess.post(f"{API}/moderation/cases/{cid}/close")

    def test_suspension_blocks_login(self, admin_sess):
        # register a throwaway offender, then permanently suspend via a user-target case
        offender = requests.Session()
        uid = uuid.uuid4().hex[:8]
        email = f"TEST_offender_{uid}@example.com"
        offender.post(f"{API}/auth/register",
                      json={"email": email, "password": "Password12345", "display_name": f"off_{uid}"})
        me = offender.get(f"{API}/auth/me").json()["user"]
        reporter = _register("rep")[0]
        cid = reporter.post(f"{API}/moderation/reports",
                            json={"target_type": "user", "target_id": me["id"], "reason": "scam"}).json()["case_id"]
        admin_sess.post(f"{API}/moderation/cases/{cid}/decision",
                        json={"action": "PermanentSuspension", "reason": "fraud"})
        # suspended user can no longer log in
        blocked = requests.post(f"{API}/auth/login", json={"email": email, "password": "Password12345"})
        assert blocked.status_code in (401, 403), f"suspended user could still log in: {blocked.status_code}"

    def test_dismiss_case(self, seller, reporter, admin_sess):
        seller_sess, _ = seller
        rep_sess, _ = reporter
        lid = _fresh_listing(seller_sess)
        cid = rep_sess.post(f"{API}/moderation/reports",
                            json={"target_type": "listing", "target_id": lid, "reason": "spam"}).json()["case_id"]
        r = admin_sess.post(f"{API}/moderation/cases/{cid}/dismiss", json={"reason": "no violation"})
        assert r.status_code == 200 and r.json()["status"] == "Dismissed"
        # closed/dismissed cases are read-only
        r2 = admin_sess.post(f"{API}/moderation/cases/{cid}/decision",
                             json={"action": "Warning", "reason": "late"})
        assert r2.status_code == 409

    def test_stats_endpoint(self, admin_sess):
        s = admin_sess.get(f"{API}/moderation/stats")
        assert s.status_code == 200 and "open" in s.json()
