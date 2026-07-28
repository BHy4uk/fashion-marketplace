# 08 — Risk Register & Mitigations

Severity = Impact × Likelihood. Each risk cites the spec area it threatens and a concrete mitigation that stays inside the approved architecture.

---

## Technical risks

**R-T1 — Distributed transaction / eventual-consistency bugs (HIGH).**
Cross-domain workflows (Offer→Order→Payment→Shipping) span aggregates; naive coding creates lost updates or dual writes. *Mitigation:* Transactional Outbox for all events; idempotent consumers (STD-001 §11); optimistic concurrency on contended aggregates; sagas modeled as event choreography with compensations; contract tests on module boundaries.

**R-T2 — Search index drift (MEDIUM).** Index diverges from source under failures. *Mitigation:* index is derived & always rebuildable (DOMAIN-003 INV-004); nightly reconciliation job; version/`updatedAt` guards to drop stale updates.

**R-T3 — File/reference integrity (MEDIUM).** Orphaned files or dangling references. *Mitigation:* immutable file IDs (STD-006 §5); reference-counting; orphan-sweeper job; never physically delete referenced files.

**R-T4 — Payment idempotency & webhook replay (HIGH).** Duplicate captures/refunds. *Mitigation:* idempotency keys, dedup on provider callbacks, refund ≤ captured invariant, reconciliation jobs (DOMAIN-006 §21).

---

## Architectural risks

**R-A1 — Boundary erosion under deadline pressure (HIGH).** Teams add cross-schema FKs / direct cross-module calls, silently killing the microservice-extraction promise. *Mitigation:* **automated architecture tests** (NetArchTest) in CI enforcing DOC-005 §24; schema-per-module with no cross-schema FKs; PR checklist = DOC-005 §25.

**R-A2 — Anemic domain / logic leaking to controllers or EF (MEDIUM).** *Mitigation:* domain unit tests with no infra references; code review against STD-007 §23; rich aggregates own invariants/state machines.

**R-A3 — Modular monolith becomes a distributed monolith on extraction (MEDIUM).** *Mitigation:* stable, versioned `*.Contracts` + integration events now; extract only when metrics justify (M9).

**R-A4 — Empty Database Design standard leads to inconsistent persistence (MEDIUM).** `standards/03_Database_Design.md` is blank. *Mitigation:* author it first (see Spec Review §Q); codify schema-per-module, audit fields, soft delete, concurrency, ID strategy before Phase 2.

---

## Business risks

**R-B1 — Cold-start / supply-demand chicken-egg (HIGH).** No sellers → no buyers. *Mitigation:* seller-first launch, low-friction listing (AI assist in M1 accelerates), seed curated inventory, focus Ukraine streetwear/archive community first.

**R-B2 — Trust failure = brand death (HIGH).** One high-profile scam erodes trust. *Mitigation:* escrow by default, reviews, moderation, verified delivery, dispute flow prioritized; "trust > growth" (DOC-000 §13).

**R-B3 — Take-rate/fee model undefined (MEDIUM).** Spec mentions fees/payouts but not amounts. *Mitigation:* make fees configuration-driven (Administration) so pricing can iterate without redeploy; decide policy pre-launch (Open Question).

---

## Operational risks

**R-O1 — Kubernetes ops overhead too early (MEDIUM).** *Mitigation:* start on managed K8s or a PaaS; Terraform keeps it portable; add complexity only with scale.

**R-O2 — Background-job backlog (offer/notification expiration, reconciliation) (MEDIUM).** *Mitigation:* dedicated worker host, monitored queues, alerting on lag, idempotent retries.

**R-O3 — Data loss / no DR (HIGH).** Financial & audit records must survive. *Mitigation:* PITR backups, tested restores, append-only financial history (BR-054), immutable audit log.

---

## AI risks

**R-AI1 — Hallucinated/incorrect attributes auto-applied (HIGH).** *Mitigation:* AI advisory-only, seller confirms, confidence surfaced not guaranteed (BR-100/102/103); structured output validation before consumption.

**R-AI2 — Prompt injection via user content/images (MEDIUM).** *Mitigation:* validate/sanitize model I/O, treat outputs as untrusted, least-data-to-provider (STD-005 §17, DOMAIN-013 §22).

**R-AI3 — Provider cost/latency/outage (MEDIUM).** *Mitigation:* async queues, caching, provider abstraction + fallback routing, budget alerts.

**R-AI4 — Regulatory (EU AI Act / disclosure) (MEDIUM).** *Mitigation:* disclose AI assistance where required, keep executions auditable & traceable (DOMAIN-013 §23).

---

## Security risks

**R-S1 — AuthZ bypass / IDOR (HIGH).** *Mitigation:* server-side authZ + ownership on every op (BR-110..113), integration tests for access control, deny-by-default.

**R-S2 — Secret leakage (HIGH).** *Mitigation:* KMS/Vault, no secrets in code/config/events (STD-005 §10, STD-001 §17), rotation, scanning in CI.

**R-S3 — Malicious uploads (MEDIUM).** *Mitigation:* type/size/MIME validation, async malware scan, EXIF strip, files untrusted until validated (STD-006 §8).

**R-S4 — Payment fraud / account takeover (HIGH).** *Mitigation:* MFA-ready, device tracking, anomaly detection, rate limiting, SCA via provider.

---

## Scalability risks

**R-SC1 — DB hotspots on Listings/Search/Orders (MEDIUM).** *Mitigation:* read replicas, CQRS read models, caching, cursor pagination, later partitioning/extraction (M9).

**R-SC2 — Image/media bandwidth cost (MEDIUM).** *Mitigation:* CDN, R2 (zero egress), responsive variants, lazy loading.

**R-SC3 — Event volume at scale (LOW→MEDIUM).** *Mitigation:* outbox now → broker (Kafka) later without domain change (STD-001).

---

## Maintenance risks

**R-M1 — Documentation drift (MEDIUM).** Spec is source of truth but code may diverge. *Mitigation:* ADRs for every deviation (DOC-005 §17), OpenAPI generated from code, keep `docs/` updated with each phase (STD-008 §20).

**R-M2 — Test rot / slow suites (MEDIUM).** *Mitigation:* fast pure-domain unit tests as the majority; Testcontainers for integration; parallelized CI; tests reference BR IDs for traceability (BR §19).

**R-M3 — Dependency/vendor lock-in (MEDIUM).** *Mitigation:* every external provider behind an interface (DOC-001 §3.21); prefer OSS/portable defaults; Terraform multi-cloud.

---

## Top 5 to watch from day one
1. R-A1 boundary erosion (kills the whole architectural premise).
2. R-T4/R-T1 payment & event correctness (money must be right).
3. R-B2 trust failure (existential for a marketplace).
4. R-1 payment-provider country coverage in Ukraine (validate before Phase 5).
5. R-O3 DR for financial/audit data.
