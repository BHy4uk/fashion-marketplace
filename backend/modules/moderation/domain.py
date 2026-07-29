"""Moderation Domain — ModerationCase aggregate (DOMAIN-011).

Moderation is investigation-centric: every decision lives on a Case. A Case references
external marketplace entities but NEVER owns them (INV-007). Evidence is immutable
(INV-003); decisions are append-only (INV-004); closed cases are read-only (INV-005);
history is immutable (INV-008). Pure domain: no framework, no DB, no enforcement.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from buildingblocks.domain import AggregateRoot, AuditInfo, DomainError, new_id, utc_now

VALID_TARGETS = {"listing", "review", "message", "user"}

# Case lifecycle (§8). Open states may accept reports/evidence; DecisionMade -> Closed;
# Dismissed is an alternative terminal state. Terminal cases are read-only.
STATUS_TRANSITIONS = {
    "Created": {"UnderReview", "Investigation", "DecisionMade", "Dismissed"},
    "UnderReview": {"Investigation", "DecisionMade", "Dismissed"},
    "Investigation": {"DecisionMade", "Dismissed"},
    "DecisionMade": {"Closed", "Investigation"},   # further decisions may re-open investigation
    "Closed": set(),
    "Dismissed": set(),
}
OPEN_STATES = {"Created", "UnderReview", "Investigation", "DecisionMade"}

# Decision actions (§11). Enforcement is performed by the owning module (application layer).
DECISION_ACTIONS = {
    "NoAction", "Warning", "ListingHidden", "ListingRemoved", "MessageHidden",
    "ReviewHidden", "ReviewRemoved", "TemporarySuspension", "PermanentSuspension",
}


@dataclass(frozen=True)
class Report:
    reporter_id: str
    reason: str
    note: str | None = None
    report_id: str = field(default_factory=new_id)
    created_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True)
class Evidence:
    kind: str                       # listing|image|message|review|profile|audit|ai_signal
    ref: str
    note: str | None = None
    added_by: str | None = None
    evidence_id: str = field(default_factory=new_id)
    created_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True)
class ModerationDecision:
    action: str
    reason: str
    moderator_id: str
    policy_ref: str | None = None
    decision_id: str = field(default_factory=new_id)
    created_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True)
class CaseComment:
    author_id: str
    text: str
    comment_id: str = field(default_factory=new_id)
    created_at: datetime = field(default_factory=utc_now)


class ModerationCase(AggregateRoot):
    def __init__(self, id, target_type, target_id, target_context=None, status="Created",
                 priority="normal", assigned_to=None, reports=None, evidence=None,
                 decisions=None, comments=None, audit=None, version=0):
        super().__init__(id, version)
        self.target_type = target_type
        self.target_id = target_id
        self.target_context = target_context or {}
        self.status = status
        self.priority = priority
        self.assigned_to = assigned_to
        self.reports: list[Report] = reports or []
        self.evidence: list[Evidence] = evidence or []
        self.decisions: list[ModerationDecision] = decisions or []
        self.comments: list[CaseComment] = comments or []
        self.audit = audit or AuditInfo(created_by="system")

    @classmethod
    def open(cls, *, target_type, target_id, target_context, report: Report,
             priority="normal") -> "ModerationCase":
        if target_type not in VALID_TARGETS:
            raise DomainError("INVALID_TARGET", "Unsupported moderation target", 422)
        c = cls(id=new_id(), target_type=target_type, target_id=target_id,
                target_context=target_context, priority=priority,
                audit=AuditInfo(created_by=report.reporter_id))
        c.reports.append(report)
        c._raise("ModerationCaseCreated",
                 {"case_id": c.id, "target_type": target_type, "target_id": target_id})
        c._raise("ReportSubmitted",
                 {"case_id": c.id, "report_id": report.report_id,
                  "reporter_id": report.reporter_id})
        return c

    def _require_open(self) -> None:
        if self.status not in OPEN_STATES:
            raise DomainError("INVALID_CASE_STATE",
                              f"A {self.status} case can no longer be modified", 409)  # INV-005

    def _transition(self, target: str) -> None:
        if target not in STATUS_TRANSITIONS[self.status]:
            raise DomainError("INVALID_CASE_STATE",
                              f"Cannot move case from {self.status} to {target}", 409)  # INV-006
        self.status = target
        self.audit.updated_at = utc_now()

    def add_report(self, report: Report) -> None:
        self._require_open()
        self.reports.append(report)                 # merge (§9, §19)
        self._raise("ReportSubmitted",
                    {"case_id": self.id, "report_id": report.report_id,
                     "reporter_id": report.reporter_id})

    def assign(self, moderator_id: str) -> None:
        self._require_open()
        self.assigned_to = moderator_id
        if self.status == "Created":
            self._transition("UnderReview")

    def start_investigation(self, moderator_id: str) -> None:
        self._require_open()
        self.assigned_to = self.assigned_to or moderator_id
        if self.status in ("Created", "UnderReview"):
            self._transition("Investigation")
        self._raise("InvestigationStarted", {"case_id": self.id, "moderator_id": moderator_id})

    def add_evidence(self, evidence: Evidence) -> None:
        self._require_open()                         # INV-003: immutable once attached
        self.evidence.append(evidence)
        self._raise("EvidenceAdded", {"case_id": self.id, "evidence_id": evidence.evidence_id})

    def add_comment(self, comment: CaseComment) -> None:
        self._require_open()
        self.comments.append(comment)

    def record_decision(self, decision: ModerationDecision) -> None:
        self._require_open()
        if decision.action not in DECISION_ACTIONS:
            raise DomainError("INVALID_DECISION_ACTION", f"Unknown action {decision.action}", 422)
        self.decisions.append(decision)              # INV-004: append-only, never overwrite
        if self.status != "DecisionMade":
            self._transition("DecisionMade")
        self._raise("ModerationDecisionRecorded",
                    {"case_id": self.id, "decision_id": decision.decision_id,
                     "action": decision.action, "target_type": self.target_type,
                     "target_id": self.target_id})

    def close(self, moderator_id: str) -> None:
        if self.status != "DecisionMade":
            raise DomainError("INVALID_CASE_STATE",
                              "A case can only be closed after a decision is recorded", 409)
        self._transition("Closed")
        self._raise("CaseClosed", {"case_id": self.id, "moderator_id": moderator_id})

    def dismiss(self, moderator_id: str, reason: str = "no_violation") -> None:
        self._require_open()
        self._transition("Dismissed")
        self._raise("CaseDismissed",
                    {"case_id": self.id, "moderator_id": moderator_id, "reason": reason})
