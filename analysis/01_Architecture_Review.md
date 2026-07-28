# 01 — Architecture Review

**Deliverable:** Architectural & Implementation Analysis (Phase 0 — no code)
**Source of truth:** `docs/` specification repository (BHy4uk/fashion-marketplace)
**Author role:** Lead Software Architect
**Date:** 2026-06

---

## 1. System Understanding (in one paragraph)

The platform is an **AI-first C2C fashion marketplace** (clothing, footwear, bags, accessories), launching in Ukraine with **European expansion baked into the architecture from day one** (multi-country, multi-currency, multi-language, multi-tax, multi-provider). It is explicitly **not** a retailer, auction, social network, or classifieds site. The engineering mandate is uncompromising: **Domain-Driven Design + Clean Architecture + Modular Monolith**, with strict domain ownership, aggregate boundaries, domain events, state machines, and infrastructure independence. Every external dependency (payment, shipping, auth, AI, cloud, storage) must be **replaceable**. One listing = one physical item (no quantities). AI **assists but never decides irreversibly**.

---

## 2. Bounded Contexts / Modules

The Domain Model (DOC-004) groups everything into **six top-level domains**, which decompose into **13 implementation modules** (one per domain spec). The mapping:

| # | Module | Top-level Domain | Aggregate Root(s) | Priority |
|---|--------|------------------|-------------------|----------|
| 1 | **Identity** | Identity | `User` (owns Profile, Session, RefreshToken, Device, EmailVerification, PasswordReset, ConnectedAccount) | Critical / MVP |
| 2 | **Listings** | Marketplace | `Listing` (owns Image, Attribute, Price, Condition, Analytics, AIAnalysis) | Critical / MVP |
| 3 | **Search** | Marketplace | `SearchQuery`, `SavedSearch` | Critical / MVP* |
| 4 | **Offers** | Commerce | `Offer` (owns OfferRevision, OfferHistory) | Critical / MVP |
| 5 | **Orders** | Commerce | `Order` (owns OrderItem, OrderStatusHistory) | Critical / MVP |
| 6 | **Payments** | Commerce | `Payment` (owns PaymentTransaction, Refund, PaymentAttempt) | Critical / MVP |
| 7 | **Shipping** | Commerce | `Shipment` (owns TrackingEvent, ShippingLabel, DeliveryConfirmation) | Critical / MVP |
| 8 | **Reviews** | Commerce | `Review` (owns ReviewResponse) | Critical / MVP |
| 9 | **Messaging** | Communication | `Conversation` (owns Message, Participant, Attachment, ReadReceipt) | Critical / MVP |
| 10 | **Notifications** | Communication | `Notification` (owns Recipient, Preference, Delivery) | High / MVP |
| 11 | **Moderation** | Platform | `ModerationCase` (owns Report, Evidence, Decision, Comment) | Critical / MVP |
| 12 | **Administration** | Platform | `PlatformConfiguration`, `FeatureFlag`, `PlatformAnnouncement` | Critical / MVP |
| 13 | **AI** | Artificial Intelligence | `AIJob`, `AIAnalysis`, `AIRecommendation` | Critical (but Phase 2 for features) |

\* Search is Critical but *eventually consistent* — MVP can ship with a simpler search backend and evolve (see Roadmap).

**Shared kernel (cross-cutting, not a business domain):** `SharedKernel` (Money, value-object base, Result type, `EntityId`), `BuildingBlocks` (aggregate base, domain-event base, outbox contracts, audit fields), and the in-process **event bus** contract.

---

## 3. Domain Boundaries & Ownership (the rules that must never break)

- **Every business capability belongs to exactly one domain** (DOC-004 §13, STD-007 §4). No capability is duplicated.
- **Aggregates are the only transactional consistency boundary.** Child entities mutate *only* through their aggregate root (DOC-004 §9, STD-004 §4).
- **No cross-module DB access, no cross-module direct calls into another aggregate's internals.** Modules talk through (a) published **contracts/interfaces** or (b) **Domain Events** (DOC-005 §4.5, §24).
- **AI owns no business entity.** It reads projections/inputs, emits `AIAnalysis`/`AIRecommendation`, and the owning domain decides (DOMAIN-013 §2, §14; BR-100..104).
- **Search owns no marketplace data** — only derived indexes; the index is always rebuildable from source (DOMAIN-003 INV-003/004).
- **Notifications own intent, not transport.** They are created *only* from domain events, never called directly by business services (DOMAIN-010 §7, INV-001).
- **Administration owns no business entity.** It delegates business actions to owning domains and never touches their persistence (DOMAIN-012 §14, INV-007).
- **Moderation references but never owns** Listings/Users/Messages/Reviews; it owns only Cases/Reports/Evidence/Decisions (DOMAIN-011 §2).

---

## 4. Layered Structure (identical in every module)

Per DOC-005 §6, each module has four layers with dependencies pointing **inward only**:

```
   API  ────────►  Application  ────────►  Domain  ◄────────  Infrastructure
 (thin HTTP)      (use cases,             (entities,          (EF Core, providers,
                   orchestration,          aggregates,         storage, messaging —
                   authorization,          value objects,      implements interfaces
                   transactions)           invariants,         defined by Domain/App)
                                           domain events,
                                           state machines)
```

- **API** — controllers/minimal endpoints, serialization, authN. **Zero business logic.**
- **Application** — CQRS-style commands/queries, orchestration, authZ checks, transaction boundaries, calls repositories & domain services via interfaces.
- **Domain** — pure business. **No framework, no DB, no provider references.** Owns invariants, lifecycle state machines, domain events.
- **Infrastructure** — EF Core repositories, provider adapters (Stripe/Nova Poshta/AI/email/storage), outbox, message bus impl. Implements interfaces declared inward.

This is the **Dependency Rule** of Clean Architecture; the Domain is the stable core (DOC-005 §4.2, §7; STD-007 §7).

---

## 5. Communication Between Modules

Two sanctioned channels only:

1. **Synchronous, read-side:** a module may query another module through a **published application interface** (e.g., Orders asks Listings "is this listing available?" via `IListingAvailabilityQuery`). No direct entity/DB access.
2. **Asynchronous, write-side facts:** **Domain Events** (STD-001). Events are past-tense facts (`OfferAccepted`, `PaymentCaptured`), owned & published only by the owning domain, immutable, idempotent for consumers, ordered only within an aggregate.

**Reliability:** Events are persisted with the aggregate change in the **same DB transaction** via the **Transactional Outbox pattern**, then dispatched by a background relay (STD-001 §15 "reliable eventual publication"). This is mandatory to satisfy "publish only after transaction completes" + "guaranteed eventual delivery."

**Key cross-domain workflow (the marketplace spine):**

```
UserRegistered → (Listings) ListingPublished → (Search) ListingIndexed
                                              → (AI) AIAnalysisPublished
Buyer offer → OfferAccepted → (Orders) OrderCreated + (Listings) ListingReserved
OrderCreated → (Payments) PaymentCreated → PaymentAuthorized → PaymentCaptured
PaymentCaptured → (Orders) Order: AwaitingPayment→Paid → (Shipping) ShipmentCreated
ShipmentDelivered → (Orders) Delivered→Completed → (Reviews) review window opens
Every step → (Notifications) user-facing notification (idempotent)
```

Note the **ownership discipline**: Payments never sets Order state; it emits `PaymentCaptured` and *Orders* decides to move `AwaitingPayment→Paid` (DOMAIN-006 §14, DOMAIN-005 §8). Same for Shipping (DOMAIN-007 §13).

---

## 6. Lifecycle / State Machines (Domain-owned, DOC-004 §12, STD-004)

| Aggregate | States (happy path) | Terminal / alternate |
|-----------|--------------------|-----------------------|
| User | Registered → EmailPending → Active | Suspended → Deleted(soft) |
| Listing | Draft → Ready → Published → Reserved → Sold → Archived | SoftDeleted |
| Offer | Draft → Submitted → Active → Accepted | Rejected / Expired / Canceled |
| Order | Created → AwaitingPayment → Paid → PreparingShipment → Shipped → Delivered → Completed | Canceled / Refunded / Closed |
| Payment | Created → PendingAuthorization → Authorized → Captured → Settled | Failed / Canceled / Refunded / PartiallyRefunded |
| Shipment | Created → AwaitingShipment → LabelGenerated → ReadyForPickup → InTransit → OutForDelivery → Delivered | Returned / Canceled / Lost |
| Review | Draft → Published | Hidden / Removed |
| Conversation | Created → Active → Archived → Closed | — |
| Message | Draft → Sent → Delivered → Read | Hidden |
| ModerationCase | Created → UnderReview → Investigation → DecisionMade → Closed | Dismissed |
| Notification | Created → Scheduled → Queued → Delivered | Failed / Expired / Canceled |
| Configuration | Draft → Validated → Active → Superseded | — |
| FeatureFlag | Created → Enabled → Disabled → Archived | — |
| AIJob | Created → Queued → Running → Completed | Failed / Canceled / Expired |

**Hard rules:** transitions are explicit, validated, never skip mandatory intermediate states (BR-043), never mutated outside the aggregate, and successful transitions **emit domain events** (STD-004 §10, §11, §20).

---

## 7. Dependencies Between Domains (build order)

```
Identity ──► Listings ──► Search
                 │
                 ├──► Offers ──► Orders ──► Payments ──► Shipping ──► Reviews
                 │
Cross-cutting (consume events from everyone): Notifications, Moderation, AI, Administration, Analytics
```

`Product_Requirements §4` fixes this dependency chain. Identity is the root; nothing works without it. Orders sits at the center of Commerce and depends on Offers (accepted offer → order) but can also be created via a direct "Buy Now" if the spec later allows (currently Order is created from an accepted offer or an authorized purchase — DOMAIN-005 §7 leaves room for direct buy).

---

## 8. Persistence & Data Ownership

- **Modular Monolith DB strategy:** single physical database, **one schema per module** (e.g., `identity`, `listings`, `orders`). **No foreign keys across schemas** — cross-module references are by **ID value only** (this is what preserves future extraction to microservices; DOC-005 §3, §24 "no direct database coupling").
- **Soft delete everywhere** (BR-016, BR-004, BR-054). Physical deletion is prohibited for business/financial records.
- **Append-only** for financial, offer, order, message, moderation, audit history (BR-034/044/054/120, plus per-domain immutability invariants).
- **Mandatory audit fields on every entity:** `CreatedAt, CreatedBy, UpdatedAt, UpdatedBy` (BR-123). Plus a global immutable **AuditLog** (DOC-004 §7).
- **Optimistic concurrency** required where invariants are contended — especially Offer acceptance, Order creation per listing, Payment capture (DOMAIN-004 §21, DOMAIN-005 §21, DOMAIN-006 §21).

> ⚠️ `docs/standards/03_Database_Design.md` is **empty**. This is the single most important spec gap — see `10_Specification_Review.md`.

---

## 9. Non-Functional Backbone

- **API-first, REST, versioned `/api/v1/`**, resource-nouns, standard status codes, cursor/page pagination, consistent error envelope with correlation IDs (STD-002).
- **Async-first** for AI, email/push, image processing, search indexing, analytics, recommendations (DOC-005 §12).
- **Security server-side always**: authN establishes identity, authZ enforced before every business op, ownership checks mandatory, defense-in-depth, immutable audit, rate limiting, least privilege (STD-005, BR-110..113).
- **Files are infrastructure**; domains store only **immutable file identifiers**, never URLs/buckets/paths (STD-006 §5). Provider-swappable object storage.
- **Observability**: structured logging, metrics, tracing-readiness, health checks, audit logging (DOC-005 §19).
- **i18n from v1**: no logic bound to a single country; currency/tax/shipping/payment/language all configuration-driven (DOC-000 §4, §12; DOC-001 §3.16).

---

## 10. Responsibilities Summary (who does what)

- **Identity**: accounts, sessions, RBAC (Guest/User/Moderator/Administrator), verification, security events.
- **Listings**: the central entity — lifecycle, images, structured attributes, pricing, availability, analytics, AI-enrichment requests.
- **Search**: derived indexes, full-text + facets + filters + sort + saved searches; never returns hidden/unauthorized content.
- **Offers**: negotiation lifecycle; exactly one acceptance per listing (atomic); immutable history.
- **Orders**: immutable purchase agreement; one active order per listing; owns lifecycle & totals; decides how payment/shipment events affect state.
- **Payments**: authorize/capture/settle/refund via swappable providers; idempotent; never stores card data; never mutates Orders.
- **Shipping**: shipment lifecycle & carrier adapters; append-only tracking; immutable delivery confirmation; never mutates Orders.
- **Reviews**: post-completed-order feedback; one per author→recipient per order; immutable after publish; supplies reputation *inputs* only.
- **Messaging**: contextual conversations (Listing/Offer/Order); immutable messages; per-participant read state; async attachment scanning.
- **Notifications**: transform domain events → user notifications; preference-aware; idempotent; transport-agnostic.
- **Moderation**: investigation-centric (Cases); append-only decisions; automation recommends, humans decide.
- **Administration**: config, feature flags, announcements, maintenance mode; delegates business actions; never bypasses domain invariants.
- **AI**: provider-agnostic jobs → structured, versioned, confidence-scored analyses & advisory recommendations; irreversible actions require human/domain approval.
