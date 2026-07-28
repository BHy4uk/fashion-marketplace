# 05 — Development Roadmap

Principle (DOC-001 §3.28, DOC-005 §23): **evolution, not big-bang.** Every phase ends **deployable** and **demoable**. Complexity is relative (1–5). Phases are ordered by the hard dependency chain in Product_Requirements §4.

Legend — Complexity: ◆1 trivial … ◆5 very hard.

---

## Phase 0 — Foundation & Walking Skeleton  ◆3  (deployable: "hello, authenticated world")

**Goal:** the modular-monolith skeleton runs end-to-end with one trivial vertical slice, so architecture is proven before features.

- Solution scaffold: `BuildingBlocks` (SharedKernel, Domain base, Application behaviors, Outbox, IntegrationEvents), `Marketplace.Api`, `Marketplace.Worker`.
- Postgres (schema-per-module), Redis, EF Core baseline, migration pipeline.
- **Transactional Outbox + in-process dispatcher** working with one demo event.
- **Architecture tests** enforcing layer/module boundaries (fail the build on violation).
- CI/CD (GitHub Actions), Docker images, Compose dev stack, health checks, structured logging, OTel, error envelope, correlation IDs.
- Next.js `web` shell + `admin` shell, i18n scaffolding, API client.

**Depends on:** nothing. **Exit:** one authenticated ping flows API→App→Domain→Infra, emits an event via outbox, worker consumes it, all boundary tests green in CI.

**Risks:** over-building BuildingBlocks. *Mitigation:* implement only what the demo slice needs.

---

## Phase 1 — Identity  ◆3  (deployable: real accounts)

- `User` aggregate + Profile/Session/RefreshToken/EmailVerification/PasswordReset; state machine (Registered→EmailPending→Active→Suspended→Deleted).
- Register, verify email, login, refresh, logout, revoke session, password reset; RBAC roles; server-side authZ + ownership; audit + security events; brute-force/rate-limit.
- Email adapter (transactional). Domain events: `UserRegistered`, `EmailVerified`, `SessionRevoked`, etc.
- **Auth is an integration** → run `integration_expert` before coding (JWT custom vs Emergent Google Auth).

**Depends on:** Phase 0. **Exit:** a user can register→verify→login→manage sessions; all flows audited & tested.

---

## Phase 2 — Listings + Media  ◆4  (deployable: sellers publish items)

- `Listing` aggregate + Image/Attribute/Price/Condition/Analytics; full lifecycle state machine (Draft→Ready→Published→Reserved→Sold→Archived→SoftDeleted).
- Structured attributes (brand/category/size/color/material/condition/gender/season).
- Object storage (S3-compat) with **immutable file IDs**, presigned upload, async image pipeline (thumbnails/optimized/EXIF strip), reference integrity.
- Publication rules (BR-010..018), soft delete, audit, permissions (owner/moderator/admin).
- Events: `ListingPublished`, `ListingPriceChanged`, `ListingReserved`, `ListingSold`, …

**Depends on:** Identity. **Exit:** seller creates draft → uploads photos → publishes; buyer views listing page (SSR/SEO). This is the **first real "wow."**

---

## Phase 3 — Search & Discovery (MVP tier)  ◆3  (deployable: buyers find items)

- `ISearchIndex` abstraction; **Postgres FTS** implementation; consume `ListingPublished/Updated/Sold/Hidden` via outbox → async index (eventual consistency).
- Keyword search, structured filters, facets, sorting, cursor pagination; hidden/sold exclusion (BR-020..024); saved searches (High).
- Rebuild-from-source job.

**Depends on:** Listings. **Exit:** search returns only public listings, filters/facets/sort deterministic, index rebuildable.

---

## Phase 4 — Offers → Orders  ◆5  (deployable: agreements form)

- `Offer` aggregate: create/counter/accept/reject/cancel/expire; **atomic single-acceptance** with optimistic concurrency; immutable history; async expiration job. Events incl. `OfferAccepted`.
- `Order` aggregate: created from accepted offer (and/or authorized direct buy); one active order per listing (concurrency-guarded); immutable totals; lifecycle Created→AwaitingPayment→…; consumes offer/payment/shipment events to advance state.
- Listing reservation on order creation (`ListingReserved`).

**Depends on:** Listings (+Identity). **Exit:** buyer offers → seller accepts → exactly one order created even under concurrent acceptance; fully audited.

---

## Phase 5 — Payments  ◆5  (deployable: money moves — the highest-risk phase)

- `Payment` aggregate: create/authorize/capture/settle/refund; **idempotent capture**, refund ≤ captured, immutable history; webhook verification; reconciliation jobs.
- `IPaymentProvider` + **Stripe Connect** adapter (escrow/payouts/fees/SCA) + Ukraine-local provider adapter.
- Emits `PaymentCaptured/Failed/Refunded`; **Orders** consumes to move AwaitingPayment→Paid/Refunded. Payments never mutates Order (DOMAIN-006 §14).

**Depends on:** Orders. **Exit:** authorized→captured→settled with idempotent duplicate-callback handling; refunds respect invariants; reconciliation green. Validate country coverage early (**Risk R-1**).

---

## Phase 6 — Shipping  ◆4  (deployable: items ship & deliver)

- `Shipment` aggregate: lifecycle Created→…→Delivered (+Returned/Canceled/Lost); append-only tracking; immutable delivery confirmation; label generation.
- `IShippingProvider` + **Nova Poshta** + **Ukrposhta** adapters; async carrier sync; verified callbacks.
- Emits `ShipmentDelivered`; **Orders** consumes to move Delivered→Completed.

**Depends on:** Orders (+Payments for eligibility). **Exit:** paid order → label → tracking → delivery confirmation → order completes.

---

## Phase 7 — Reviews & Reputation  ◆2  (deployable: trust signals)

- `Review` aggregate: one per author→recipient per **completed** order; immutable after publish; seller response; hide/remove via moderation.
- Reputation **inputs** exposed to Identity/Analytics (Reviews does not compute platform score).

**Depends on:** Orders completion. **Exit:** completed order unlocks review; duplicates blocked; reputation input visible on profile.

---

## Phase 8 — Messaging  ◆4  (deployable: buyer/seller talk)

- `Conversation` (contextual to Listing/Offer/Order) + immutable `Message` + per-participant read receipts + image attachments (async virus scan/thumbnail).
- Dedupe conversations per context+participants; participant authZ; moderation hide.

**Depends on:** Listings/Offers/Orders (context). **Exit:** contextual chat with attachments, read status, audit.

---

## Phase 9 — Notifications  ◆3  (runs alongside from Phase 1; formalized here)  (deployable: users kept informed)

- `Notification` created **only** from domain events; preferences per type; templates (versioned, localized); **idempotent** (no dup per event); In-App + Email adapters; delivery retries.

**Depends on:** event producers across phases. **Exit:** key events (offer/order/payment/shipment/message) produce idempotent, preference-aware notifications.

---

## Phase 10 — Moderation + Administration  ◆4  (deployable: operable platform)

- **Administration:** PlatformConfiguration (versioned/atomic activation), FeatureFlags (rollout/kill-switch, cached), Announcements, Maintenance mode, admin RBAC, audit; delegates business actions to owning domains.
- **Moderation:** Reports → `ModerationCase` → evidence (immutable) → append-only decisions → close; report merging; automation recommends only.

**Depends on:** most domains (references). **Exit:** operators configure platform, toggle features, run maintenance; reports become investigable cases with auditable decisions.

---

## Phase 11 — AI Enrichment  ◆5  (Phase 2 product tier; deployable, additive)

- `IAiProvider` abstraction; `AIJob`→`AIAnalysis`/`AIRecommendation`; versioned prompts; structured+confidence outputs; async queue; audit; human-in-the-loop.
- First use cases: image→attributes, title/description generation, category/brand detection (all **advisory**, seller confirms — BR-101/103).
- Then: translation (Messaging/Listings), semantic/visual search (pgvector), moderation signals, price suggestions.

**Depends on:** Listings/Search/Messaging/Moderation. **Exit:** AI enrich flow produces editable suggestions; nothing auto-published; all executions auditable.

---

## Phase 12 — Analytics & Hardening  ◆3  (ongoing)

- Event-driven read models/materialized views → dashboards (Metabase); seller/buyer/marketplace metrics tied to DOC-000 §11 (no vanity metrics).
- Perf passes (caching, N+1, pagination), security audit/pen-test, load tests, DR drills, docs & ADR consolidation.

---

## Dependency graph (phases)

```
0 ─ 1 ─ 2 ─ 3
        │
        └─ 4 ─ 5 ─ 6 ─ 7
9 (notifications) consumes events from 1,4,5,6,8 (built incrementally)
8 (messaging) after 2/4
10 (moderation+admin) after most; admin partly needed early (flags) — pull a thin slice into Phase 0/1
11 (AI) additive after 2/3/8/10
12 (analytics/hardening) continuous
```

## Cross-cutting done in every phase (definition of done — DOC-002 §6, STD-008 §25)
Business rules implemented · invariants enforced · state machine validated · domain events emitted via outbox · authZ + ownership server-side · audit complete · unit+integration+API tests (referencing BR IDs) · OpenAPI updated · no architecture-test violations.
