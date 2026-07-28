# 04 — Project / Repository Structure

A **Modular Monolith** in .NET. One deployable API host + one worker host + frontend apps. Each module is a vertical slice with four internal layers; the Domain layer of every module has **zero** infrastructure references (enforced by architecture tests).

```
fashion-marketplace/
├─ docs/                                # EXISTING spec repo — remains source of truth
│  ├─ foundation/ standards/ domains/
│  ├─ adr/                              # NEW: Architecture Decision Records (0001-*.md)
│  ├─ diagrams/                         # NEW: C4 context/container/component
│  └─ api/                              # NEW: generated OpenAPI snapshots
│
├─ src/
│  ├─ Bootstrap/
│  │  ├─ Marketplace.Api/               # single ASP.NET Core host; wires all module APIs
│  │  │  ├─ Program.cs  Middleware/  Endpoints/  appsettings*.json
│  │  └─ Marketplace.Worker/            # background host (Hangfire, outbox relay, indexers)
│  │
│  ├─ BuildingBlocks/                   # shared kernel — NO business rules
│  │  ├─ SharedKernel/                  # Money, EntityId<T>, ValueObject, Result, Error
│  │  ├─ Domain/                        # AggregateRoot, Entity, IDomainEvent, audit fields
│  │  ├─ Application/                    # ICommand/IQuery, IHandler, behaviors (validation,
│  │  │                                 #   authz, transaction, logging), IUnitOfWork
│  │  ├─ Infrastructure/                # Outbox, EF base, Redis, clock, correlation, idempotency
│  │  └─ IntegrationEvents/             # cross-module event contracts (public, versioned)
│  │
│  └─ Modules/
│     ├─ Identity/
│     │  ├─ Identity.Domain/            # User aggregate, Profile/Session/..., invariants, events
│     │  ├─ Identity.Application/       # RegisterUser, Login, VerifyEmail, RevokeSession (CQRS)
│     │  ├─ Identity.Infrastructure/    # EF (schema "identity"), token store, OIDC adapters
│     │  ├─ Identity.Api/               # controllers/endpoints (thin)
│     │  └─ Identity.Contracts/         # public interfaces + integration events others may use
│     ├─ Listings/            (Listings.Domain/Application/Infrastructure/Api/Contracts)
│     ├─ Search/
│     ├─ Offers/
│     ├─ Orders/
│     ├─ Payments/
│     ├─ Shipping/
│     ├─ Reviews/
│     ├─ Messaging/
│     ├─ Notifications/
│     ├─ Moderation/
│     ├─ Administration/
│     └─ AI/
│
├─ frontend/
│  ├─ web/                              # Next.js buyer/seller app (SSR/SEO, i18n, mobile-first)
│  │  ├─ app/  components/  features/  lib/api/  lib/i18n/  public/
│  └─ admin/                            # Next.js/React operator console (Administration + Moderation)
│
├─ tests/
│  ├─ Architecture.Tests/               # NetArchTest: enforce DOC-005 §24 (domain≠infra, no cross-module DB)
│  ├─ <Module>.Domain.Tests/           # pure unit tests per aggregate/state machine (no infra)
│  ├─ <Module>.Application.Tests/      # use-case tests with fakes
│  ├─ Integration.Tests/               # Testcontainers (Postgres/Redis), real repositories
│  ├─ Api.Tests/                        # WebApplicationFactory end-to-end HTTP
│  ├─ Contract.Tests/                   # Pact — module boundary contracts
│  └─ e2e/                              # Playwright — critical buyer/seller journeys
│
├─ deploy/
│  ├─ docker/                           # Dockerfiles (api, worker, web, admin)
│  ├─ compose/                          # docker-compose.dev.yml (pg, redis, minio, mailhog, meili)
│  ├─ k8s/                              # manifests / Helm charts (api, worker, web, admin, hpa)
│  └─ terraform/                        # cloud-agnostic IaC (vpc, db, redis, bucket, k8s, dns)
│
├─ .github/workflows/                   # ci.yml (build+test+arch+scan), cd.yml (deploy), preview.yml
├─ .editorconfig  Directory.Build.props  .globalconfig   # analyzers, nullable, warnings-as-errors
├─ Marketplace.sln
└─ README.md
```

## Conventions that enforce the architecture

- **Project reference rules (compile-time boundaries):**
  - `*.Domain` references **only** `BuildingBlocks/SharedKernel` + `BuildingBlocks/Domain`. Never EF, never another module.
  - `*.Application` references its own `*.Domain` + `BuildingBlocks/Application`. Never Infrastructure.
  - `*.Infrastructure` references `*.Application` + `*.Domain` (implements their interfaces).
  - `*.Api` references `*.Application` + `*.Contracts`.
  - A module may reference **only** another module's `*.Contracts` — never its Domain/Infrastructure. (Architecture test asserts this.)
- **One EF `DbContext` per module**, mapped to its own **schema**; migrations live in that module's Infrastructure.
- **Cross-module reads** go through `*.Contracts` interfaces (e.g., `IListingAvailabilityQuery`). **Cross-module writes** never happen directly — only via **integration events** in `BuildingBlocks/IntegrationEvents`.
- **Domain events** are internal to a module; **integration events** are the public, versioned contracts other modules subscribe to (published via outbox).
- **Vertical slice per use case** inside Application (`Features/Offers/AcceptOffer/{Command,Handler,Validator}.cs`) — cohesion over layering-by-type.
- **CQRS-lite**: Commands mutate through aggregates; Queries can bypass aggregates and read projections/read-models directly (DOC-005 §10).

## Deployables

| Artifact | Contents | Scales on |
|---|---|---|
| `Marketplace.Api` | all module `*.Api` + `*.Application` + `*.Infrastructure` | request load (HPA) |
| `Marketplace.Worker` | outbox relay, Hangfire jobs, search indexers, AI queue, reconciliation | job backlog |
| `frontend/web` | Next.js SSR | traffic (CDN + pods) |
| `frontend/admin` | operator console | low, internal |

This is a **single deployable application** (two hosts sharing the same solution) exactly as DOC-005 §3 requires, while each module can later be lifted into its own service with its `*.Contracts` already defined.
