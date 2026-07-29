"""AI Domain — AIJob aggregate (DOMAIN-013).

AI augments business domains; it NEVER owns entities or makes business decisions
(INV-003/005, §14). Analyses are immutable (§5); confidence scores immutable once
published (INV-008); recommendations are ADVISORY (INV-004); every execution records
model/provider/prompt/timestamp/result (INV-007). Pure domain: no framework, no provider.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from buildingblocks.domain import AggregateRoot, AuditInfo, DomainError, new_id, utc_now

# AI Job lifecycle (§8). Retries create NEW executions (never overwrite, §21).
STATUS_TRANSITIONS = {
    "Created": {"Queued", "Canceled"},
    "Queued": {"Running", "Canceled"},
    "Running": {"Completed", "Failed"},
    "Completed": set(),
    "Failed": {"Queued"},
    "Canceled": set(),
}


@dataclass(frozen=True)
class AIAnalysis:
    kind: str                       # detected_brand | category_suggestion | quality_score | attribute | fraud_score
    value: str
    confidence: float               # 0..1, immutable once published (INV-008)
    analysis_id: str = field(default_factory=new_id)
    created_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True)
class AIRecommendation:
    kind: str                       # improve_title | improve_description | adjust_price | add_photos | suggest_category
    message: str
    confidence: float
    rec_id: str = field(default_factory=new_id)
    created_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True)
class AIExecution:
    provider: str
    model: str
    prompt_version: str
    status: str                     # completed | failed
    error: str | None = None
    execution_id: str = field(default_factory=new_id)
    created_at: datetime = field(default_factory=utc_now)


class AIJob(AggregateRoot):
    def __init__(self, id, objective, subject_type, subject_id, status="Created",
                 executions=None, analyses=None, recommendations=None,
                 audit=None, version=0):
        super().__init__(id, version)
        self.objective = objective          # exactly one objective (INV-001)
        self.subject_type = subject_type
        self.subject_id = subject_id
        self.status = status
        self.executions: list[AIExecution] = executions or []
        self.analyses: list[AIAnalysis] = analyses or []
        self.recommendations: list[AIRecommendation] = recommendations or []
        self.audit = audit or AuditInfo(created_by="system")

    @classmethod
    def create(cls, *, objective, subject_type, subject_id) -> "AIJob":
        if not objective:
            raise DomainError("INVALID_OBJECTIVE", "An AI job requires one objective", 422)
        j = cls(id=new_id(), objective=objective, subject_type=subject_type, subject_id=subject_id)
        j._raise("AIJobCreated",
                 {"job_id": j.id, "objective": objective, "subject_type": subject_type,
                  "subject_id": subject_id})
        return j

    def _transition(self, target: str) -> None:
        if target not in STATUS_TRANSITIONS[self.status]:
            raise DomainError("INVALID_AI_JOB_STATE",
                              f"Cannot move AI job from {self.status} to {target}", 409)
        self.status = target
        self.audit.updated_at = utc_now()

    def queue(self) -> None:
        self._transition("Queued")
        self._raise("AIJobQueued", {"job_id": self.id})

    def start(self) -> None:
        self._transition("Running")
        self._raise("AIExecutionStarted", {"job_id": self.id})

    def complete(self, *, provider, model, prompt_version, analyses, recommendations) -> None:
        self.executions.append(AIExecution(provider=provider, model=model,
                                           prompt_version=prompt_version, status="completed"))
        self.analyses.extend(analyses)               # analyses are append/immutable (§5, INV-009)
        self.recommendations.extend(recommendations)
        self._transition("Completed")
        self._raise("AIExecutionCompleted", {"job_id": self.id})
        if analyses:
            self._raise("AIAnalysisPublished",
                        {"job_id": self.id, "count": len(analyses)})
        if recommendations:
            self._raise("RecommendationGenerated",
                        {"job_id": self.id, "count": len(recommendations)})

    def fail(self, *, provider, model, prompt_version, error) -> None:
        self.executions.append(AIExecution(provider=provider, model=model,
                                           prompt_version=prompt_version, status="failed",
                                           error=str(error)[:500]))
        self._transition("Failed")
        self._raise("AIExecutionFailed", {"job_id": self.id, "error": str(error)[:200]})
