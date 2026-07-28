# 02 — Technology Recommendations

For each concern: **why it fits**, **advantages**, **disadvantages**, **alternatives**, **long-term scalability**. Final picks are consolidated in `03_Technology_Decisions.md`.

> The spec is deliberately technology-neutral (STD-007 §18). The recommendation below is the smallest stack that faithfully satisfies **DDD + Clean Architecture + Modular Monolith + provider replaceability + EU-scale**. The repository's `.vs` folder signals a .NET/Visual Studio intent, which is also the strongest natural fit for this architecture.

---

## Backend platform & language — **.NET 9 / C#**

- **Why it fits:** C# + .NET is the reference ecosystem for Clean Architecture + Modular Monolith (strong typing, mature DI, source-generated mediators, first-class EF Core, best-in-class background workers, native OpenTelemetry). It maps 1:1 to the spec's layered structure and aggregate modelling.
- **Advantages:** excellent performance (Kestrel), rich async, superb tooling/refactoring, long LTS support, huge library ecosystem for payments/storage/observability, easy microservice extraction later.
- **Disadvantages:** heavier than Node for tiny services; Windows-heritage perception (irrelevant — Linux containers are first-class); smaller hiring pool than JS in some EU markets.
- **Alternatives:** **Java/Spring Modulith** (equally valid, more verbose); **Node/NestJS** (great DX, weaker for large domain models, no true parallelism); **Go** (fast, but DDD ergonomics and EF-equivalent maturity are weaker).
- **Scalability:** stateless horizontal scaling; module → microservice extraction path is well-trodden in .NET.

## Frontend — **Next.js (React, TypeScript) with App Router**

- **Why it fits:** spec mandates SSR-where-appropriate, SEO, mobile-first, accessibility, PWA/future-mobile (DOC-000 §13). Next.js delivers SSR/ISR/streaming + strong SEO + image optimization out of the box.
- **Advantages:** SEO + performance, huge ecosystem, React Native reuse path for future native app, Vercel or self-host.
- **Disadvantages:** App Router complexity; hydration pitfalls; SSR infra cost.
- **Alternatives:** **Remix** (excellent data-loading model), **Nuxt** (Vue), **Angular** (heavier). Plain SPA rejected — fails SEO requirement.
- **Scalability:** CDN + edge rendering; scales independently of backend.

## API style — **REST (OpenAPI) now, GraphQL-ready later**

- **Why it fits:** STD-002 explicitly prescribes versioned REST (`/api/v1`), resource nouns, standard status codes; GraphQL noted as *future*.
- **Advantages:** simplest, cache-friendly, universally consumable, easy versioning/deprecation.
- **Disadvantages:** over/under-fetching; many round-trips for rich screens.
- **Alternatives:** GraphQL (great for mobile fan-out; add later behind the same application layer), gRPC (ideal for internal module-to-microservice comms post-extraction).
- **Scalability:** stateless, CDN-cacheable GETs, cursor pagination for large sets.

## Authentication — **ASP.NET Core Identity + JWT access / rotating refresh tokens; OIDC providers pluggable**

- **Why it fits:** Identity spec (DOMAIN-001) = email+password v1, OAuth (Google/Apple) future, sessions, refresh tokens, device tracking, MFA-ready, RBAC. Provider must be replaceable (DOC-000 §13).
- **Advantages:** battle-tested hashing, lockout/brute-force, token lifecycle; OIDC swap without touching domain.
- **Disadvantages:** rolling your own token store needs care; refresh-token rotation/revocation must be explicit.
- **Alternatives:** **Keycloak** / **Auth0** / **Duende IdentityServer** (externalize IdP — good at scale but adds ops); **Emergent-managed Google Auth** for a fast social-login path.
- **Scalability:** stateless JWT verification scales horizontally; session/refresh store in Postgres+Redis.

## Primary database — **PostgreSQL 16**

- **Why it fits:** relational integrity for money/orders/audit; **schema-per-module** gives module isolation without cross-schema FKs; JSONB for flexible listing attributes; `pg_trgm`/`tsvector` for early search; strong concurrency (optimistic via `xmin`/version column). Empty DB spec means we set the standard — Postgres is the safe, scalable default.
- **Advantages:** ACID, mature, cheap, extensions (PostGIS for geo, `pgvector` for AI embeddings later), excellent EF Core support.
- **Disadvantages:** manual sharding at extreme scale; not a search engine.
- **Alternatives:** **SQL Server** (natural .NET pairing, licensing cost), **MySQL** (weaker JSON/extensions), **MongoDB** (rejected as system-of-record for financial invariants — but fine for read models).
- **Scalability:** read replicas, partitioning, Citus/Postgres sharding, per-module DB extraction later.

## Caching — **Redis**

- **Why it fits:** distributed cache requirement (DOC-000 §13), feature-flag cache (DOMAIN-012 §19), session/refresh, rate limiting, idempotency keys, facet caches.
- **Advantages:** ubiquitous, fast, supports pub/sub, streams (usable as lightweight bus early).
- **Disadvantages:** in-memory cost; must treat as ephemeral (never system of record).
- **Alternatives:** Valkey (OSS fork), Memcached (cache-only), in-proc `IMemoryCache` (single-node only).
- **Scalability:** Redis Cluster / managed (ElastiCache, Azure Cache).

## Search — **Phase-1: PostgreSQL FTS → Phase-2: OpenSearch/Elasticsearch → Phase-3: vector (semantic/visual)**

- **Why it fits:** Search spec demands typo tolerance, facets, synonyms(future), semantic/visual(future) and **provider independence** with a rebuildable index (DOMAIN-003). Start simple (Postgres FTS satisfies MVP), abstract behind `ISearchIndex`, upgrade without domain change.
- **Advantages of OpenSearch:** best-in-class facets, relevance tuning, typo tolerance, horizontal scaling.
- **Disadvantages:** operational heaviness; eventual consistency (already assumed by spec §6).
- **Alternatives:** **Meilisearch/Typesense** (lightweight, great DX, excellent for MVP+), **Algolia** (managed, costs scale), **pgvector** for embeddings.
- **Scalability:** dedicated cluster, sharded indexes, async indexing via outbox events.

## Object storage — **S3-compatible (AWS S3 / Cloudflare R2 / MinIO for dev)**

- **Why it fits:** STD-006 — files are infrastructure, referenced by immutable IDs, provider-swappable, lifecycle-managed, CDN-served.
- **Advantages:** cheap, durable, presigned uploads (offload from API), lifecycle rules, versioning.
- **Disadvantages:** eventual consistency on some ops; egress cost (mitigate with CDN).
- **Alternatives:** Azure Blob, GCS, Cloudflare R2 (zero egress — attractive for image-heavy fashion). MinIO for local/dev.
- **Scalability:** effectively unlimited; CDN in front.

## Messaging / event bus — **In-process dispatcher + Transactional Outbox now; RabbitMQ/Kafka when extracting services**

- **Why it fits:** Modular Monolith = in-process events during v1 (STD-001), but the outbox makes delivery reliable and the transport swappable for later microservice extraction.
- **Advantages:** simplest correct implementation; no extra infra for MVP; outbox guarantees at-least-once.
- **Disadvantages:** in-proc bus can't cross processes (fine until extraction); outbox relay adds a worker.
- **Alternatives:** **RabbitMQ** (routing, at scale), **Kafka** (event log/replay, analytics streaming), **Azure Service Bus** (managed).
- **Scalability:** swap dispatcher for broker without changing domain event code.

## Background jobs — **.NET Hosted Services + a durable scheduler (Hangfire or Quartz.NET on Postgres)**

- **Why it fits:** every domain lists background jobs (expiration, reconciliation, indexing, cleanup, retries). Offer/notification expiration and payment reconciliation are business-critical.
- **Advantages:** Postgres-backed persistence (Hangfire), retries, dashboards; no extra infra.
- **Disadvantages:** Hangfire dashboard needs securing; heavy schedules may need dedicated workers.
- **Alternatives:** **Quartz.NET**, cloud-native (AWS EventBridge/Lambda), Temporal (durable workflows — great later for saga orchestration).
- **Scalability:** dedicated worker pods; partitioned queues.

## Notifications delivery — **Adapter per channel: Email (Resend/SendGrid), In-App (Postgres+Redis), Push/SMS later**

- **Why it fits:** Notifications domain owns *intent*, transport is infra (DOMAIN-010). v1 = In-App + Email.
- **Alternatives:** Postmark, Amazon SES (cheap at scale), Firebase Cloud Messaging (push), Twilio (SMS), Telegram (relevant for Ukraine market).
- **Scalability:** queue-driven, provider-swappable, digesting later.

## AI integration — **Provider-abstracted (`IAiProvider`); OpenAI / Anthropic / Gemini interchangeable; pgvector for embeddings**

- **Why it fits:** AI domain mandates provider abstraction, versioned prompts, structured+versioned outputs, confidence scores, human oversight (DOMAIN-013). Never bound to one vendor (DOC-000 §13).
- **Advantages:** vision models for image→attributes, LLMs for titles/descriptions/translation, embeddings for semantic/visual search.
- **Disadvantages:** cost/latency (must be async), non-determinism (validate all outputs), prompt-injection risk.
- **Alternatives:** Azure OpenAI (compliance), Mistral, local models (Llama/Qwen) for cost/privacy; the **Emergent Universal LLM key** for OpenAI/Anthropic/Gemini text + Gemini image during build.
- **Scalability:** queue + batch + cache; per-provider routing; A/B prompt testing later.

## Image processing — **ImageSharp (in-process) or a serverless resizer; CDN-level transforms**

- **Why it fits:** Listings/Messaging need thumbnails, optimized variants, EXIF strip, validation (STD-006 §10). Derived files are infra artifacts; originals stay authoritative.
- **Alternatives:** libvips/sharp sidecar, Cloudinary/imgix (managed transforms), Cloudflare Images.
- **Scalability:** async pipeline off the request path; CDN caching.

## Payments — **Stripe primary (Connect for marketplace payouts/escrow); provider-abstracted for Adyen/PayPal/local**

- **Why it fits:** Payments spec: escrow, fees, payouts, refunds, idempotency, PCI/PSD2/SCA, **multi-provider** (DOC-000, DOMAIN-006). Stripe Connect handles seller onboarding, split payments, held funds, and SCA out of the box — offloading PCI.
- **Advantages:** never touch card data; webhooks; strong SCA support; test key available in-environment.
- **Disadvantages:** Stripe availability/fees vary by country (**Ukraine coverage is a launch risk — see Risks**); Connect complexity.
- **Alternatives:** **Adyen** (strong EU/global), **Mangopay/Lemonway** (EU marketplace escrow specialists), **LiqPay/Fondy/Portmone** (Ukraine-local). The abstraction is what matters — likely **Stripe (EU) + a Ukraine-local provider** at launch.
- **Scalability:** provider routing by country; idempotent capture; reconciliation jobs.

## Shipping integrations — **Adapter per carrier; Ukraine launch = Nova Poshta + Ukrposhta; EU = DHL/DPD/InPost**

- **Why it fits:** Shipping spec: carrier-agnostic adapters, labels, tracking, delivery confirmation (DOMAIN-007). Nova Poshta is the dominant UA carrier and must be a first-class adapter.
- **Alternatives:** aggregators (Shippo, EasyPost, Sendcloud — one integration, many carriers) to accelerate EU expansion.
- **Scalability:** aggregator + direct adapters; async tracking sync.

## Infrastructure & containerization — **Docker; Kubernetes (managed) for prod; Compose for dev**

- **Why it fits:** spec requires cloud-native, horizontal scaling, zero-downtime, IaC (DOC-000 §13).
- **Advantages:** portable (no cloud lock-in — a spec constraint), rolling deploys, autoscaling.
- **Disadvantages:** K8s ops overhead — mitigate with managed (EKS/AKS/GKE) or start with a PaaS.
- **Alternatives:** ECS/Fargate, Nomad, Fly.io/Render (fast MVP), plain VMs (rejected long-term).
- **IaC:** **Terraform** (cloud-agnostic) — matches "no single cloud provider."

## CI/CD — **GitHub Actions (build/test/scan/deploy); trunk-based + preview envs**

- **Alternatives:** GitLab CI, Azure DevOps. **Scalability:** matrix builds, container scanning, progressive delivery via feature flags (Administration domain already provides them).

## Monitoring / Observability / Logging — **OpenTelemetry → Prometheus + Grafana + Loki + Tempo (or Datadog/Grafana Cloud managed)**

- **Why it fits:** DOC-005 §19 demands structured logs, metrics, tracing-readiness, health checks. .NET has native OTel.
- **Alternatives:** ELK/OpenSearch for logs, Sentry for errors, Datadog (managed all-in-one).
- **Scalability:** sampling, retention tiers.

## Testing — **xUnit + FluentAssertions (unit), Testcontainers (integration), WebApplicationFactory (API), Playwright (E2E), Pact (contract)**

- **Why it fits:** DOC-005 §20 requires unit/integration/API/E2E/contract; domain rules testable without infra (pure domain). Contract tests protect module boundaries pre-extraction.

## Documentation — **OpenAPI/Swagger (API), ADRs in-repo (`/docs/adr`), C4 diagrams, DocFX or Docusaurus site**

- **Why it fits:** STD-002 §21 endpoint docs; DOC-005 §17 ADRs govern deviations. Keep the existing `docs/` spec as the living source of truth.

## Development tooling — **EditorConfig + Roslyn analyzers + architecture tests (NetArchTest/ArchUnitNET), Husky/pre-commit, Conventional Commits**

- **Why it fits:** the architecture's "prohibited practices" (DOC-005 §24) can be **enforced automatically** — e.g., "Domain must not reference Infrastructure/EF" as a failing test. This is the single highest-leverage tooling decision.

## Deployment — **Managed K8s, blue-green/rolling, DB migrations gated, feature-flag-guarded releases**

- **Scalability:** HPA on API + workers; DB read replicas; CDN for static/media.

## Performance — **CDN, Redis caching, cursor pagination, async off-path work, N+1 guards, output caching for public search/listing reads**

## Security — **TLS everywhere, secret manager (Vault/cloud KMS), OWASP hardening, rate limiting, WAF, audit log, least privilege, dependency scanning**

## Administration — **built-in Administration module (config, flags, announcements, maintenance) + separate admin UI app; RBAC roles (Ops/Support/Finance/Trust&Safety/Auditor)**

## Analytics — **event stream → warehouse (start with Postgres read models/materialized views → ClickHouse/BigQuery at scale); Metabase/Superset dashboards**

- **Why it fits:** F16 Analytics is Medium priority; success metrics are conversion/retention (DOC-000 §11), not vanity. Domain events are the natural analytics feed.
