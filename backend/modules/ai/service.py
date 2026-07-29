"""AI Application — orchestrates advisory enrichment + fraud scoring behind AIProvider.

AI augments other domains; it NEVER owns entities or makes binding decisions
(INV-003/005, §14). Enrichment produces immutable analyses + advisory recommendations.
Fraud scoring produces a risk signal; when it crosses the configured threshold it opens
(or merges into) a Moderation case for HUMAN review — it never takes an entity down.

Reads listing content ONLY via ListingContract (no cross-module DB access, §22)."""
from __future__ import annotations

import logging
import os

from motor.motor_asyncio import AsyncIOMotorDatabase

from buildingblocks.domain import DomainError
from modules.listings.contracts import ListingContract

from .domain import AIAnalysis, AIJob, AIRecommendation
from .prompts import active_version
from .provider import build_ai_provider
from .repository import AIJobRepository

log = logging.getLogger("ai")

_SYSTEM_REPORTER = {"_id": "system-ai"}


class AIService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.repo = AIJobRepository(db)
        self.listings = ListingContract(db)
        self.provider = build_ai_provider()
        self.fraud_threshold = float(os.environ.get("AI_FRAUD_THRESHOLD", "0.75"))

    @property
    def _model(self) -> str:
        return getattr(self.provider, "model", self.provider.name)

    # ---- enrichment (advisory attributes + recommendations) ----
    async def enrich_listing(self, listing_id: str) -> AIJob:
        detail = await self.listings.detail(listing_id)
        if not detail:
            raise DomainError("LISTING_NOT_FOUND", "Listing not found", 404)
        job = AIJob.create(objective="listing_enrichment", subject_type="listing",
                           subject_id=listing_id)
        await self.repo.add(job)
        job.queue()
        job.start()
        pv = active_version("listing_enrichment")
        try:
            out = await self.provider.analyze_listing(
                title=detail.get("title", ""), description=detail.get("description", ""))
            analyses, recs = self._map_enrichment(out)
            job.complete(provider=self.provider.name, model=self._model,
                         prompt_version=pv, analyses=analyses, recommendations=recs)
        except Exception as exc:  # noqa: BLE001 - AI is advisory, never breaks the flow
            log.exception("listing enrichment failed for %s", listing_id)
            job.fail(provider=self.provider.name, model=self._model,
                     prompt_version=pv, error=exc)
        await self.repo.save(job)
        return job

    # ---- fraud scoring (advisory signal -> Moderation) ----
    async def score_listing_fraud(self, listing_id: str) -> AIJob:
        detail = await self.listings.detail(listing_id)
        if not detail:
            raise DomainError("LISTING_NOT_FOUND", "Listing not found", 404)
        job = AIJob.create(objective="fraud_analysis", subject_type="listing",
                           subject_id=listing_id)
        await self.repo.add(job)
        job.queue()
        job.start()
        pv = active_version("fraud_analysis")
        risk, flags = 0.0, []
        try:
            out = await self.provider.score_fraud(
                title=detail.get("title", ""), description=detail.get("description", ""),
                price=detail.get("price_amount"))
            risk = float(out.get("risk_score", 0) or 0)
            flags = [str(f) for f in out.get("flags", [])]
            analyses = [AIAnalysis(kind="fraud_score", value=str(risk), confidence=risk)]
            analyses += [AIAnalysis(kind="fraud_flag", value=f, confidence=risk) for f in flags]
            job.complete(provider=self.provider.name, model=self._model,
                         prompt_version=pv, analyses=analyses, recommendations=[])
        except Exception as exc:  # noqa: BLE001
            log.exception("fraud scoring failed for %s", listing_id)
            job.fail(provider=self.provider.name, model=self._model,
                     prompt_version=pv, error=exc)
        await self.repo.save(job)
        if risk >= self.fraud_threshold:
            await self._raise_moderation_signal(listing_id, risk, flags)
        return job

    async def _raise_moderation_signal(self, listing_id: str, risk: float, flags: list) -> None:
        """Advisory only: open/merge a Moderation case for human review (no takedown)."""
        from modules.moderation.service import ModerationService
        try:
            await ModerationService(self.db).submit_report(
                reporter=_SYSTEM_REPORTER, target_type="listing", target_id=listing_id,
                reason="ai_fraud_signal",
                note=f"AI risk score {risk} — flags: {', '.join(flags) or 'none'}",
                target_context={"source": "ai", "ai_risk_score": risk, "ai_flags": flags})
            log.info("[ai] fraud signal -> moderation case for listing %s (risk=%.2f)",
                     listing_id, risk)
        except DomainError as e:
            if e.code != "DUPLICATE_REPORT":  # signal already recorded on this case
                log.warning("could not raise moderation signal: %s", e.code)

    # ---- queries ----
    async def latest_enrichment(self, listing_id: str) -> dict | None:
        job = await self.repo.latest("listing_enrichment", listing_id)
        return self._job_view(job) if job else None

    async def latest_fraud(self, listing_id: str) -> dict | None:
        job = await self.repo.latest("fraud_analysis", listing_id)
        return self._job_view(job) if job else None

    # ---- mapping / views ----
    def _map_enrichment(self, out: dict) -> tuple[list[AIAnalysis], list[AIRecommendation]]:
        analyses: list[AIAnalysis] = []
        brand = out.get("brand")
        if brand:
            analyses.append(AIAnalysis(kind="detected_brand", value=str(brand.get("value", "")),
                                       confidence=float(brand.get("confidence", 0))))
        cat = out.get("category")
        if cat:
            analyses.append(AIAnalysis(kind="category_suggestion", value=str(cat.get("value", "")),
                                       confidence=float(cat.get("confidence", 0))))
        q = out.get("quality_score")
        if q:
            analyses.append(AIAnalysis(kind="quality_score", value=str(q.get("value", "")),
                                       confidence=float(q.get("confidence", 0))))
        for attr in out.get("attributes", []) or []:
            analyses.append(AIAnalysis(kind=str(attr.get("kind", "attribute")),
                                       value=str(attr.get("value", "")),
                                       confidence=float(attr.get("confidence", 0))))
        recs = [AIRecommendation(kind=str(r.get("kind", "")), message=str(r.get("message", "")),
                                 confidence=float(r.get("confidence", 0)))
                for r in out.get("recommendations", []) or []]
        return analyses, recs

    def _job_view(self, job: AIJob) -> dict:
        return {
            "job_id": job.id, "objective": job.objective, "status": job.status,
            "subject_type": job.subject_type, "subject_id": job.subject_id,
            "provider": job.executions[-1].provider if job.executions else None,
            "model": job.executions[-1].model if job.executions else None,
            "prompt_version": job.executions[-1].prompt_version if job.executions else None,
            "analyses": [{"kind": a.kind, "value": a.value, "confidence": a.confidence}
                         for a in job.analyses],
            "recommendations": [{"kind": r.kind, "message": r.message, "confidence": r.confidence}
                                for r in job.recommendations],
            "created_at": job.audit.created_at,
        }
