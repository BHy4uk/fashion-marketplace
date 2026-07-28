# 03 — Technology Decisions (Chosen Stack)

Chosen because they best satisfy the **architecture** (DDD + Clean + Modular Monolith + replaceable providers + EU scale), not because they are popular. Each decision cites the spec constraint it serves. Deviations, if ever needed, require an ADR (DOC-005 §17).

| Concern | Decision | Primary justification (spec) |
|---|---|---|
| Backend | **.NET 9 / C#** | Best-fit for Clean Architecture + Modular Monolith; native DI, EF Core, OTel, background workers; clean microservice extraction path (DOC-005 §3, §4). `.vs` folder confirms .NET intent. |
| Frontend | **Next.js 15 + TypeScript (App Router)** | SSR/SEO/mobile-first/accessibility/PWA + future React Native reuse (DOC-000 §13; DOC-001 §3.10, §3.15). |
| Admin UI | **Separate Next.js (or React) app** consuming Administration APIs | Administration is its own bounded context; keep operator surface isolated (DOMAIN-012). |
| API | **REST + OpenAPI, `/api/v1`** | STD-002 mandates versioned REST; GraphQL is future. |
| Auth | **ASP.NET Core Identity + JWT (short-lived) + rotating refresh tokens; OIDC (Google/Apple) pluggable; MFA-ready** | DOMAIN-001; provider replaceability (DOC-000 §13). |
| Authorization | **RBAC (Guest/User/Moderator/Administrator) + resource-ownership checks, server-side** | DOMAIN-001 §8–9; BR-110..113; STD-005 §5. |
| Primary DB | **PostgreSQL 16, schema-per-module, no cross-schema FKs, ID-only references** | Modular Monolith isolation + microservice extraction (DOC-005 §3, §24). |
| ORM | **EF Core (Infrastructure layer only)** | Domain stays persistence-ignorant (STD-007 §7, §11). |
| Concurrency | **Optimistic (rowversion/`xmin`)** on Offer/Order/Payment | DOMAIN-004/005/006 §21. |
| Reliable events | **Transactional Outbox + background relay; in-process dispatcher (MediatR-style)** | STD-001 §7, §15 (publish post-commit + guaranteed eventual delivery). |
| Cache | **Redis** (cache, sessions/refresh, rate limit, idempotency keys, flag cache) | DOC-000 §13; DOMAIN-012 §19. |
| Search | **Postgres FTS (MVP) → Meilisearch/OpenSearch (scale) → pgvector (semantic/visual)**, behind `ISearchIndex` | DOMAIN-003 (provider-independent, rebuildable, eventually consistent). |
| Object storage | **S3-compatible (Cloudflare R2 or AWS S3); MinIO in dev**, referenced by immutable file IDs | STD-006. |
| Image processing | **ImageSharp/libvips async pipeline + CDN transforms** | STD-006 §10; Listings/Messaging background jobs. |
| Background jobs | **Hangfire on Postgres + .NET Hosted Services** | every domain's §Background Jobs; offer/notification expiration, reconciliation. |
| Notifications | **Domain-event-driven; adapters: In-App (Postgres+Redis) + Email (Resend/SES) v1; Push/SMS/Telegram later** | DOMAIN-010 §7, §9. |
| Payments | **Stripe Connect (escrow/payouts/SCA) behind `IPaymentProvider`; add a Ukraine-local provider (LiqPay/Fondy) at launch** | DOMAIN-006 (escrow, multi-provider, PCI/PSD2); DOC-000 §13. Test key available in env. |
| Shipping | **Carrier adapters behind `IShippingProvider`; launch: Nova Poshta + Ukrposhta; EU: aggregator (Sendcloud/Shippo) + DHL/InPost** | DOMAIN-007. |
| AI | **`IAiProvider` abstraction; OpenAI/Anthropic/Gemini interchangeable; versioned prompts; structured+confidence outputs; pgvector embeddings; async queue** | DOMAIN-013; STD-007 §12. Use Emergent Universal Key during build. |
| Messaging transport (future) | **RabbitMQ or Kafka on service extraction** | STD-001; DOC-005 §3. |
| Containerization | **Docker; managed Kubernetes (EKS/AKS/GKE) prod; Compose dev** | DOC-000 §13 (cloud-native, horizontal, zero-downtime). |
| IaC | **Terraform** | "no single cloud provider" (DOC-000 §13). |
| CI/CD | **GitHub Actions; trunk-based; preview envs; feature-flag releases** | DOC-000 §13. |
| Observability | **OpenTelemetry → Prometheus/Grafana/Loki/Tempo (or Grafana Cloud/Datadog)** | DOC-005 §19. |
| Errors | **Sentry** | DOC-005 §14, §19. |
| Testing | **xUnit + FluentAssertions; Testcontainers; WebApplicationFactory; Playwright; Pact** | DOC-005 §20. |
| Arch enforcement | **NetArchTest/ArchUnitNET tests in CI** enforcing DOC-005 §24 "prohibited practices" | turns architecture rules into failing builds. |
| Docs | **OpenAPI/Swagger; ADRs in `/docs/adr`; C4 diagrams; keep `docs/` spec authoritative** | STD-002 §21; DOC-005 §17. |
| Analytics | **Domain-event feed → Postgres materialized views (MVP) → ClickHouse/BigQuery; Metabase** | F16; DOC-000 §11 (no vanity metrics). |
| Secrets | **Cloud KMS / HashiCorp Vault; never in code/config** | STD-005 §10; DOMAIN-012 §22. |

## The three decisions that most protect the architecture

1. **Schema-per-module + ID-only cross-references.** This is what makes "future extraction to microservices without redesign" (DOC-005 §3) *true* rather than aspirational. Cross-schema FKs would silently couple modules.
2. **Transactional Outbox.** Without it, "publish events only after the transaction completes" **and** "guarantee eventual publication" (STD-001 §7, §15) cannot both hold. It is non-negotiable infrastructure.
3. **Automated architecture tests.** DOC-005 §24 lists prohibited practices (domain→infra references, cross-module DB access, business logic in controllers/repos). Encoding these as CI tests is the only way they survive contact with deadlines.

## Explicitly deferred (not chosen for v1, by design)

- GraphQL, gRPC, Kafka, ClickHouse, dedicated search cluster, push/SMS, native mobile — all have clean insertion points and are **not** required for a production MVP. Adding them early would violate DOC-001 §3.4 (simplicity over feature count) and DOC-005 §21 (no premature optimization).
