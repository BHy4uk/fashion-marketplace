# Fashion Marketplace — Architectural & Implementation Analysis (Master Report)

**Deliverable 1 (no code):** complete project analysis of the AI-first C2C fashion marketplace specified in `docs/`.
**Role:** Lead Software Architect · **Source of truth:** the specification repository (specification always wins).
**Reference product studied:** Grailed (fashion resale; seller-driven listings, offers/negotiation, curated designer/streetwear/archive, strong filters, seller ratings, escrow-style payments, price-drop alerts). We adopt its *patterns*, never its branding/UI/workflow.

> This master report synthesizes everything and links to the detailed structured documents. Read this first; drill into the numbered docs for depth.

## Document index
| # | Document | Covers |
|---|----------|--------|
| 01 | [Architecture Review](01_Architecture_Review.md) | modules, boundaries, responsibilities, communication, lifecycle, dependencies |
| 02 | [Technology Recommendations](02_Technology_Recommendations.md) | every stack area with why/pros/cons/alternatives/scalability |
| 03 | [Technology Decisions](03_Technology_Decisions.md) | the chosen stack + justifications |
| 04 | [Project Structure](04_Project_Structure.md) | full repo/solution layout + boundary-enforcing conventions |
| 05 | [Development Roadmap](05_Development_Roadmap.md) | phased, deployable milestones + dependencies + complexity |
| 06 | [MVP Definition](06_MVP_Definition.md) | smallest production-ready scope + rationale + acceptance journey |
| 07 | [Future Roadmap](07_Future_Roadmap.md) | post-MVP milestones M1–M10 |
| 08 | [Risks](08_Risks.md) | technical/architectural/business/operational/AI/security/scale/maintenance + mitigations |
| 09 | [Open Questions](09_Open_Questions.md) | only what the spec cannot answer (with safe defaults) |
| 10 | [Specification Review](10_Specification_Review.md) | FAANG-level critique: contradictions, gaps, opportunities, what's already optimal |

---

## 1. Architecture review (summary)
An **AI-first C2C fashion marketplace**, Ukraine-first, EU-ready by construction. **Modular Monolith** of **13 modules** grouped into 6 domains (Identity; Marketplace: Listings, Search; Commerce: Offers, Orders, Payments, Shipping, Reviews; Communication: Messaging, Notifications; Platform: Moderation, Administration; AI). Each module has four inward-pointing layers (API→Application→Domain←Infrastructure). Modules communicate **only** via published `*.Contracts` interfaces (reads) and **Domain Events via a transactional outbox** (write-side facts). Aggregate roots own their state machines and invariants; child entities never mutate independently. Persistence is **schema-per-module, no cross-schema FKs, ID-only references** — the property that makes future service extraction real. AI owns no business data; Search owns only rebuildable indexes; Notifications are event-sourced intent; Administration delegates and never bypasses domain rules. *(Full detail → doc 01.)*

## 2–3. Technology (recommendation → decision)
**.NET 9 / C#** backend (best natural fit for DDD+Clean+Modular Monolith; `.vs` folder confirms intent) · **Next.js/TS** web (SSR/SEO/mobile-first) + separate **admin** app · **REST/OpenAPI `/api/v1`** · **ASP.NET Core Identity + JWT/refresh, OIDC-pluggable, RBAC** · **PostgreSQL 16** (schema-per-module) + **EF Core** in Infrastructure only · **Redis** (cache/sessions/rate-limit/idempotency/flags) · **Search: Postgres FTS → Meilisearch/OpenSearch → pgvector**, behind `ISearchIndex` · **S3-compatible storage** (R2/S3, MinIO dev) with immutable file IDs · **Transactional Outbox + in-process dispatcher** now, broker later · **Hangfire** background jobs · **Notifications:** In-App + Email v1 · **Payments: Stripe Connect + a Ukraine-local provider** behind `IPaymentProvider` · **Shipping: Nova Poshta + Ukrposhta** behind `IShippingProvider` · **AI:** `IAiProvider` (OpenAI/Anthropic/Gemini interchangeable), versioned prompts, structured+confidence outputs · **Docker + managed Kubernetes + Terraform** · **GitHub Actions** CI/CD · **OpenTelemetry → Grafana stack + Sentry** · **xUnit/Testcontainers/Playwright/Pact** + **NetArchTest architecture tests**. The three architecture-defining choices: **schema-per-module + ID-only refs**, **transactional outbox**, and **automated architecture tests**. *(Full matrix → docs 02, 03.)*

## 4. Project structure (summary)
Single .NET solution: `BuildingBlocks/*` (shared kernel — no business rules), `Modules/<Name>/{Domain,Application,Infrastructure,Api,Contracts}`, two hosts (`Marketplace.Api`, `Marketplace.Worker`), `frontend/{web,admin}`, `tests/{Architecture,Domain,Application,Integration,Api,Contract,e2e}`, `deploy/{docker,compose,k8s,terraform}`. Compile-time project references enforce the dependency rule; one `DbContext`/schema per module; cross-module writes only via integration events. *(Full tree + conventions → doc 04.)*

## 5. Development roadmap (summary)
**P0** foundation/walking skeleton (outbox + arch tests + CI) → **P1** Identity → **P2** Listings+Media (first wow) → **P3** Search MVP → **P4** Offers→Orders → **P5** Payments (highest risk) → **P6** Shipping → **P7** Reviews → **P8** Messaging → **P9** Notifications (incremental) → **P10** Moderation+Administration → **P11** AI enrichment → **P12** Analytics+Hardening. Every phase ends deployable; ordering follows the hard dependency chain (Identity→Listings→Search→Offers→Orders→Payments→Shipping→Reviews). *(Complexity, dependencies, per-phase exits → doc 05.)*

## 6. MVP (summary)
Everything needed for one real transaction with trust intact in Ukraine: Identity, Profiles, Listings, Search (FTS tier), Offers, Orders, Payments (escrow), Shipping (Nova Poshta/Ukrposhta), Reviews, Messaging, Notifications (in-app+email), Moderation, Administration, Security/Infra, and the i18n *foundation* (UAH + Ukrainian/English). **Excluded:** AI features, recommendations/collections/follows, push/SMS, BI, multi-item/auctions/crypto/social, live second market — all with clean insertion points. Each inclusion/exclusion is justified against the mission and Product_Requirements §5. *(Acceptance journey → doc 06.)*

## 7. Future roadmap (summary)
M1 AI Seller Assistant → M2 Intelligent Discovery (semantic/visual/recs) → M3 Trust & Safety 2.0 → **M4 European Expansion** (the core vision) → M5 Seller Analytics → M6 Engagement (push/Telegram/SMS) → M7 Payments features → M8 Native Mobile → M9 Scale/Service-Extraction → M10 New bounded contexts. *(Rationale/KPIs → doc 07.)*

## 8. Risks (top 5)
1) **Architectural boundary erosion** (kills the extraction promise) → enforce with CI architecture tests + schema-per-module. 2) **Payment/event correctness** → outbox + idempotency + reconciliation. 3) **Trust failure** → escrow, reviews, moderation, disputes first-class. 4) **Payment-provider Ukraine coverage** → validate before Phase 5; local provider ready. 5) **DR for financial/audit data** → PITR + tested restores + append-only history. *(Full register across 8 categories → doc 08.)*

## 9. Open questions (only unanswerable-from-spec)
The empty **Database Design** standard (Q1), **launch payment provider** (Q2), **escrow/fund-release policy** (Q3), **fee model** (Q4), **Buy-Now vs offer-only** (Q5), return/refund window (Q6), **reputation ownership+formula** (Q7), MFA-in-MVP (Q8), GDPR erasure vs append-only (Q9), real-time chat expectation (Q10), category taxonomy source (Q11), team/timeline/budget (Q12). All have safe defaults; none block Phase 0; Q1–Q4 needed before Phases 2/5. *(Details + defaults → doc 09.)*

## 10. Specification review (headline)
The spec is **unusually strong and internally coherent** — implement as written. Resolve a few *completions/tensions*: Order-creation-vs-BR-042 wording (C1), reputation ownership "or" (C2), and author the missing specs (empty DB standard, consistency model, error-code registry, concrete API envelope, SLOs, fee/escrow, taxonomy, GDPR retention, localization). Highest-ROI additions: **encode "Prohibited Practices" as CI architecture tests** and **name the Outbox/Inbox pattern**. Explicitly optimal and to be left unchanged: domain/aggregate ownership, AI-as-advisory, event-only notifications, derived-rebuildable search, Payments-never-mutates-Orders choreography, one-item listings, soft-delete/append-only/audit, provider replaceability, and the "specification wins" governance. *(Full critique → doc 10.)*

---

## Recommended immediate next steps
1. **You:** answer Open Questions Q1–Q4 (DB standard, payment provider, escrow, fees).
2. **Me (on your go):** begin **Phase 0 — foundation/walking skeleton** (BuildingBlocks, outbox, one vertical slice, CI + architecture tests) — the smallest thing that proves the architecture end-to-end and stays deployable.
3. In parallel, I can author the missing standards (Database Design, Consistency Model, Error-Code Registry, API envelope) as spec additions for your approval before Phase 2.

No implementation has begun. Awaiting your review and direction.
