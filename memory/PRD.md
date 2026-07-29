# PRD — AI-First C2C Fashion Marketplace ("ARCHIVE")

## Problem statement
Production-ready AI-first C2C fashion marketplace (clothing, footwear, bags, accessories),
Ukraine-first with EU expansion by design. Mandatory architecture: DDD + Clean Architecture +
Modular Monolith, aggregate boundaries, domain events, state machines, provider replaceability.
Spec repo (docs/) is the single source of truth. Reference product studied: Grailed.

## Stack decision (ADR-0001)
Architecture is mandatory but technology-neutral (STD-007 §18, STD-003 §22). Implemented on the
platform-native stack: Python FastAPI + React (CRA) + MongoDB, preserving all architectural rules.
Providers behind interfaces (LiqPay payments, Nova Poshta shipping) for later phases.

## Locked product decisions (Q1-Q12)
Payments: IPaymentProvider, LiqPay primary, config-selected. Escrow: capture immediately, payout 72h
after Completed (configurable) unless dispute/moderation/fraud; dispute freezes. Fee: seller-paid, %,
per-country config. Buy Now + Offers (offers default on, seller can disable). Refunds via dispute only.
Reputation owned by Identity (weighted avg + count, verified only, replaceable). MFA-ready not enforced.
GDPR: anonymize PII on erasure, retain financial/audit. Messaging: WebSockets from start. Taxonomy:
platform-owned via Administration. Team: 1-3 eng + AI; optimize for maintainability/long-term evolution.

## What's implemented (2026-06)
- Phase 0 Foundation: BuildingBlocks (AggregateRoot, DomainEvent, DomainError, AuditInfo, optimistic
  concurrency), Transactional Outbox + background relay + in-process event bus, Mongo (schema-per-module
  via collection prefixes), RBAC deps, DomainError->HTTP mapping.
- Phase 1 Identity: User aggregate + lifecycle state machine, register/login/refresh/logout/me,
  forgot/reset password, brute-force lockout, JWT httpOnly cookies, reputation value object.
- Phase 2 Listings: Listing aggregate + full lifecycle state machine, structured attributes, Money
  (minor units), image references, publication rules, create/publish/reprice/archive, owner authz.
- Phase 3 Search (MVP tier): Mongo-backed search with filters + facets + sort + pagination; hidden/sold
  excluded. Read-model views (CQRS-lite).
- Administration: platform-owned taxonomy (categories/brands/meta), seeded.
- Frontend (Swiss high-contrast design system): Home, Shop (facets/sort), Listing detail (gallery,
  attributes, Buy Now/Make Offer, seller reputation, escrow note), Auth, Sell (create+publish),
  Seller Dashboard. Sonner toasts, framer-motion available, phosphor icons.
- Domain events flowing through outbox verified (UserRegistered, ListingPublished).

## Deliverable 0 (analysis, no code): /app/analysis/*.md + FAANG spec review + ADR-0001.

## Next action items (backlog, priority order)
- P0 Phase 4 Offers -> Orders (atomic single acceptance, one active order per listing).
- P0 Phase 5 Payments (LiqPay adapter, escrow, idempotent capture) + Phase 6 Shipping (Nova Poshta).
- P1 Phase 7 Reviews (feeds Identity reputation) + Phase 8 Messaging (WebSockets).
- P1 Object storage for real image uploads (currently image URLs); Notifications module (Phase 9).
- P2 Moderation + full Administration UI (Phase 10); AI enrichment (Phase 11); Analytics (Phase 12).
- Author remaining spec additions: Consistency Model, Error-Code Registry, API envelope, SLOs.
- Add automated architecture tests (enforce DOC-005 §24) in CI.

## Not yet implemented / mocked
- Buy Now / Make Offer buttons are UI-only (toast) pending Offers/Orders/Payments phases.
- Image upload = URL input (object storage deferred).
- Email verification wired but auto-activated (not enforced in MVP).

## Update 2026-06 (Phase 4 + Phase 5 + atomic outbox)
- Phase 4 OFFERS (DOMAIN-004): Offer aggregate, turn-based negotiation, immutable revision history,
  atomic single-acceptance (offer_acceptances unique lock), events, expiration sweeper. Frontend: Make Offer + /offers.
- Atomic OUTBOX: events embedded in aggregate document ($set+$push single atomic write), relay dispatches
  + $pull. Solves the "2-write" debt (blocking prereq for Payments). All 3->4 repos migrated.
- Phase 5 ORDERS (DOMAIN-005): Order aggregate (immutable totals, full lifecycle state machine, status
  history), event-driven creation from OfferAccepted (idempotent, atomic order_listing_locks + unique offer_id),
  seller-paid 10% platform fee (PLATFORM_FEE_PERCENT), buyer cancel (AwaitingPayment->Canceled). Choreography:
  OrderCreated -> Listings.reserve; OrderCanceled -> Listings.release + Offers.release_lock. Frontend: /orders.
- Listings->Contracts refactor: Listings now reads Identity via IdentityContract (no cross-module DB access).
- Tests: 46/46 pytest (backend_test.py + test_offers.py + test_orders.py). iteration_2 & iteration_3 reports.

## Carried technical debt
- Orders: no pagination on list; cancel lock-release not reconciled on failure (future reconciler).
- Search still inside Listings (not own bounded context); email verification auto-activated.

## Phase 6 PAYMENTS (next) — decisions locked
- LiqPay primary via IPaymentProvider (config-selected); Stripe/Adyen/Fondy/WayForPay addable w/o redesign.
- Capture immediately; funds held; payout released 72h after Order Completed (configurable) unless
  dispute/moderation/fraud; dispute freezes. Escrow lives ONLY in Payments. Orders reacts to PaymentCaptured
  (-> Paid) via events. NEEDS: LiqPay public_key + private_key from user (sandbox ok).

## Update 2026-06 (Phase 6 PAYMENTS + ESCROW) — COMPLETE & TESTED (67/67)
- Payment aggregate (DOMAIN-006): money lifecycle Created->PendingAuthorization->Authorized->Captured->Settled
  (+Failed/Canceled/Refunded); append-only PaymentTransaction ledger; escrow (held on capture; release_at set
  on OrderCompleted; released by sweeper). Events: PaymentCreated/Initiated/Authorized/Captured/ReleaseScheduled/
  Released/Refunded/Failed.
- IPaymentProvider abstraction + SandboxProvider (default, deterministic, no keys) + LiqPayProvider (sha3-256
  signed data, hold/capture/refund; PAYMENT_PROVIDER + LIQPAY_PUBLIC_KEY/LIQPAY_PRIVATE_KEY to activate).
- Choreography: buyer POST /api/payments/checkout -> capture into escrow -> PaymentCaptured -> Orders.mark_paid
  (AwaitingPayment->Paid). OrderCompleted -> Payments.schedule_release(+72h). OrderCanceled -> Payments.refund.
  Escrow release sweeper (60s) settles due payouts. Payments NEVER mutates Orders (events only).
- OrderContract added (Payments reads Orders via contract, no cross-module DB). Unique order_id (1 payment/order).
- Frontend: /orders 'Pay now' -> sandbox capture -> status flips to Paid; humanized status labels.
- Config: PAYMENT_PROVIDER=sandbox, PAYOUT_HOLD_HOURS=72, PLATFORM_FEE_PERCENT=10.

## To activate real LiqPay (Phase 6 go-live)
Set in backend/.env: PAYMENT_PROVIDER=liqpay, LIQPAY_PUBLIC_KEY, LIQPAY_PRIVATE_KEY (sandbox_i.../sandbox_...
from LiqPay dashboard), LIQPAY_SANDBOX=true, BACKEND_PUBLIC_URL=<preview/prod url>. Webhook: /api/payments/webhook/liqpay.

## Next phases
- Phase 8 Reviews (feeds Identity reputation), Phase 9 Messaging (WebSockets).

## Update 2026-06 (Phase 7 SHIPPING + closed escrow loop) — COMPLETE & TESTED (84/84)
- Shipment aggregate (DOMAIN-007): carrier-AGNOSTIC fulfilment lifecycle
  Pending->LabelCreated->Dispatched->InTransit->Delivered (+Returned/Canceled); append-only
  normalized TrackingEvent history; optimistic concurrency + embedded-events atomic outbox;
  unique order_id (one shipment/order).
- IShippingProvider port + SandboxShippingProvider (default, no keys, deterministic) +
  NovaPoshtaProvider (real API v2.0: InternetDocument.save for waybill, TrackingDocument.
  getStatusDocuments for tracking, InternetDocument.delete for cancel; StatusCode->normalized
  status map). Adding UPS/DHL/FedEx/Meest/Ukrposhta = new adapter only, no domain change.
  Selected via SHIPPING_PROVIDER + NOVAPOSHTA_API_KEY(+sender refs) env.
- Choreography (Orders holds ZERO carrier logic): OrderPaid -> Shipping.create_for_order
  (Shipment Pending) -> ShipmentCreated -> Order Paid->PreparingShipment. Seller POST
  /dispatch -> provider waybill + ShipmentDispatched -> Order PreparingShipment->Shipped.
  Buyer POST /confirm-delivery (or carrier tracking sweep) -> ShipmentDelivered ->
  Order Shipped->Delivered->Completed -> OrderCompleted -> Payments.schedule_release.
  ESCROW LOOP NOW CLOSES END-TO-END (payout release_at set on completion).
- Shipping events: ShipmentCreated/LabelCreated/Dispatched/InTransit/Delivered/Returned/Canceled.
- APIs: GET /api/shipments/order/{order_id}; POST /api/shipments/{id}/dispatch (seller);
  POST /api/shipments/{id}/track; POST /api/shipments/{id}/confirm-delivery (buyer).
- Background tracking sweeper (120s) polls carrier for in-flight shipments (auto-delivery for
  real carriers). Reads Orders ONLY via OrderContract. Shipping NEVER mutates Orders.
- Frontend /orders: seller "Dispatch shipment", buyer "Confirm delivery", carrier+tracking#+status line.
- Config: SHIPPING_PROVIDER=sandbox (default), NOVAPOSHTA_* placeholders in backend/.env.
- Tests: 84/84 pytest (added test_shipping.py: 17 tests — aggregate SM, provider abstraction,
  status mapping, full escrow-loop choreography, authz).

## To activate real Nova Poshta (Phase 7 go-live)
Set in backend/.env: SHIPPING_PROVIDER=novaposhta, NOVAPOSHTA_API_KEY, and sender refs
(NOVAPOSHTA_SENDER_CITY/REF/ADDRESS/CONTACT/PHONE from the NP business account + directory APIs).
Recipient refs (city_ref/recipient_ref/address_ref/contact_ref/phone) passed per-dispatch in to_address.

## Update 2026-06 (Phase 9 MESSAGING — real-time WebSockets) — COMPLETE & TESTED (119/119 backend, frontend 100%)
- Conversation aggregate (DOMAIN-009): tied to exactly one business context (listing|order for MVP),
  >=2 participants, embedded immutable Messages (INV-004/007 — never deleted, only hidden),
  per-participant ReadReceipts, lifecycle Active<->Archived->Closed. Unique dedup_key
  (context+sorted participants) => reuse existing conversation, deterministic dup failure (§9,§15).
- Real-time transport: in-process ConnectionManager (user_id -> sockets); message send PERSISTS
  (history/audit) AND BROADCASTS live to connected participants (~0.5s observed). WebSocket
  /api/ws/messages authenticated via httpOnly access_token cookie (or ?token= fallback); accepts
  client send/read/ping frames. FIX: WS send_json can't serialize datetime -> emit ISO strings.
- Events: ConversationCreated / MessageSent / MessageRead / ConversationArchived / ConversationClosed / MessageHidden.
- Reads context via Listing/Order contracts + Identity contract only (no cross-module DB).
- APIs: POST /api/conversations (start/reuse); GET /api/conversations (list + unread + counterparty);
  GET /api/conversations/{id}/messages (history, marks read); POST .../messages (send);
  POST .../read; POST .../archive; POST .../close (mod/admin); POST .../messages/{mid}/hide (mod/admin).
- Frontend: new /messages two-pane chat page (WebSocket live indicator, unread badges, real-time
  incoming), 'Message seller' on ListingDetail, 'Message buyer/seller' per order on Orders, Messages nav link.
- Tests: 18 in test_messaging.py (domain, REST, authz, dedup/reuse, read receipts, moderation,
  and REAL WebSocket delivery via websockets lib). Full backend suite 119/119. Frontend flow test 100% (iteration_6).

## Carried technical debt (Phase 9)
- ConnectionManager is single-pod in-memory; horizontal scale needs a Redis pub/sub broadcast bus.
- Text-only (image attachments + async virus scan deferred per user). No message pagination.
- Offer-context conversations not supported (listing + order only, per user choice).

## Update 2026-06 (Phase 10 NOTIFICATIONS — event-sourced, in-app + email) — COMPLETE & TESTED (131/131 backend, frontend 100%)
- Notification aggregate (DOMAIN-010): created ONLY from completed business events (§7);
  lifecycle Created->Queued->Delivered|Failed (+Canceled/Expired); per-recipient read status;
  delivery attempt records. IDEMPOTENT via unique index (event_id, recipient_id) — redelivered
  events never duplicate (INV-008/§20). Delivery failures never touch business flow (INV-005).
- Provider-independent delivery (same pattern as Payments/Shipping): EmailProvider abstraction
  with SandboxEmailProvider (default, console/log, no keys) + ResendEmailProvider (real, sync SDK
  via asyncio.to_thread). Switch via EMAIL_PROVIDER=resend + RESEND_API_KEY + SENDER_EMAIL, no code
  change. SendGrid/SES/Mailgun = new adapter only.
- Channels: In-App (real-time over the shared /api/ws/messages WebSocket) + Email (gated by prefs).
  Per-user preferences (notification_preferences): email_enabled, in_app_enabled, muted_types —
  evaluated before delivery (INV-007).
- Subscribes (via outbox) to OfferAccepted, PaymentCaptured, ShipmentDispatched, ShipmentDelivered,
  OrderCompleted, ReviewPublished, MessageSent. Templates map each event -> recipient-specific specs.
  Reads recipient contact via IdentityContract.contact() only (no cross-module DB).
- Events: NotificationCreated/Queued/Delivered/Failed/Read.
- APIs: GET /api/notifications; GET /api/notifications/unread-count; POST /{id}/read; POST /read-all;
  GET/PUT /api/notifications/preferences.
- Frontend: NotificationBell in the top nav — live badge (WebSocket), dropdown list, mark-all-read,
  click-to-navigate. Verified real-time badge increment without reload (iteration_7, 100%).
- Tests: 12 in test_notifications.py (domain, provider abstraction, templates, idempotency,
  event-sourced creation, preferences, read status, real-time WS delivery). Full backend 131/131.

## To activate real email (Phase 10 go-live)
Set backend/.env: EMAIL_PROVIDER=resend, RESEND_API_KEY=re_..., SENDER_EMAIL=<verified sender>. Restart backend.

## Carried technical debt (Phase 10)
- Two brief concurrent /api/ws/messages sockets when on /messages (bell + chat) — no functional
  impact (badge increments by exactly 1); proper fix = one shared app-level WebSocket context.
- No scheduled/delayed/expiring notifications, no digesting, no email retry queue (immediate delivery only).
- In-app record always created (in_app_enabled currently informational; muting affects email only).

## Update 2026-06 (Phase 11 MODERATION + ADMIN UI) — COMPLETE & TESTED (145/145 backend, frontend 100%)
- ModerationCase aggregate (DOMAIN-011): investigation-centric. References marketplace
  entities but never owns them (INV-007). Evidence immutable (INV-003), decisions
  APPEND-ONLY (INV-004), closed/dismissed cases read-only (INV-005). Lifecycle
  Created->UnderReview->Investigation->DecisionMade->Closed (+Dismissed).
- Report intake: any authenticated user reports a target (listing|review|message|user).
  Reports MERGE into the existing open case for a target (§9); duplicate report by same
  reporter rejected (§15/§16 DUPLICATE_REPORT).
- Decision actions: NoAction, Warning, ListingHidden, ListingRemoved, MessageHidden,
  ReviewHidden, ReviewRemoved, TemporarySuspension, PermanentSuspension. ENFORCEMENT is
  delegated to owning modules (application layer): Reviews.hide/remove, Messaging.hide_message,
  Listings.moderate_takedown (NEW), Identity.suspend (NEW). Enforce-before-record so a failed
  enforcement aborts cleanly.
- APIs: POST /api/moderation/reports (any user); GET /api/moderation/cases[?status], /stats,
  /cases/{id}; POST /cases/{id}/{assign|investigate|evidence|comment|decision|close|dismiss}
  (all moderator/admin via require_roles — moderation data confidential §13/§20).
- Frontend: /admin/moderation dashboard (stats bar, status filters, case queue, case detail with
  reports/evidence/decisions/comments + investigate/comment/decision/close/dismiss). 'Admin' nav
  link shown only for staff. ReportButton on ListingDetail ('Report listing').
- Tests: 14 in test_moderation.py (domain lifecycle, append-only decisions, read-only closed,
  report merge + dedup, permissions, ENFORCEMENT — ListingRemoved takes down listing,
  PermanentSuspension blocks login, dismiss, stats). Full backend 145/145. Frontend 100% (iteration_8).

## Carried technical debt (Phase 11)
- Suspension is one-way (no reactivate endpoint yet); TemporarySuspension has no auto-expiry.
- No automated detection/AI signals feeding cases (manual reports only) — Phase 12.
- No SLA timers, case priority is set to 'normal' (not auto-escalated); no evidence file uploads.
- No pagination on the case queue.

## Next phase (final)
- Phase 12 AI Enrichment + Analytics/Hardening (listing auto-tagging/quality, fraud signals into
  Moderation, seller/marketplace analytics, rate limiting + hardening).

## Update 2026-06 (Phase 8 REVIEWS + reputation choreography) — COMPLETE & TESTED (101/101)
- Review aggregate (DOMAIN-008): tied to exactly one Completed order; one Author + one Recipient
  (both order participants); publish-immediately (Draft skipped, Grailed-style); immutable after
  publish (INV-006); Rating 1–5 + optional comment (<=2000). Lifecycle Published<->Hidden->Removed
  (Removed terminal, kept for audit INV-007). Single immutable ReviewResponse child (§10).
- Both directions (buyer->seller AND seller->buyer). Duplicate prevention via unique compound index
  (order_id, author_id, recipient_id) => deterministic failure under concurrency (INV-005, §19).
- Reputation choreography (Identity OWNS reputation, Q7/§11): Review.create emits ReviewPublished
  (rating + recipient) -> Identity.on_review_published applies it to the recipient's reputation.
  IDEMPOTENT for at-least-once delivery via unique per-review guard (identity_applied_reviews);
  redelivered events never double-count. Reviews NEVER writes identity_users.
- Events: ReviewPublished / ReviewResponseCreated / ReviewHidden / ReviewUnhidden / ReviewRemoved.
- Reads Orders via OrderContract + Identity via IdentityContract only (no cross-module DB).
- APIs: POST /api/reviews (participant, completed order); GET /api/reviews/eligibility/{order_id};
  GET /api/reviews/user/{user_id} (public, published only + reputation summary);
  GET /api/reviews/order/{order_id} (participants; staff see all incl. removed);
  POST /api/reviews/{id}/response (recipient only, once);
  POST /api/reviews/{id}/hide|unhide|remove (moderator/admin, require_roles).
- Frontend: /orders shows a star-rating ReviewForm on Completed orders (both boxes) with eligibility
  gating + "You reviewed this transaction" state. Seller reputation on ListingDetail reflects updates.
- Config: none new. Tests: 101/101 pytest (added test_reviews.py: 17 — aggregate lifecycle, rating
  validation, eligibility, duplicate prevention, both-directions, responses, moderation, reputation update).

## Carried technical debt (Phase 8)
- Reputation is applied on publish but NOT reversed when a review is later Hidden/Removed (MVP;
  a reputation reconciler is future work). No review pagination. Multi-dimension ratings (communication/
  shipping/accuracy/packaging) deferred (§8 future). Review UI wired to the tested API contract and
  compiles clean, but not yet browser click-tested end-to-end. Search still coupled inside Listings.

## Carried technical debt (Phase 7)
- Shipment: no pagination; single parcel/seat; buyer shipping address not collected at checkout
  (dispatch accepts optional to_address/parcel). Sandbox delivery requires buyer confirmation
  (real carriers auto-deliver via sweeper). Search still coupled inside Listings.

## Update 2026-06 (Phase 12 AI ENRICHMENT + ANALYTICS + HARDENING) — COMPLETE & TESTED (160/160 backend, frontend smoke-verified)
- AI bounded context (DOMAIN-013): AIJob aggregate (objective+subject, lifecycle
  Created->Queued->Running->Completed/Failed; immutable analyses + advisory
  recommendations; every execution records provider/model/prompt_version/status).
  AI is ADVISORY ONLY — it never mutates listings/orders/users.
- IAIProvider port + SandboxAIProvider (default, deterministic, seeded by input hash,
  no keys — full CI) + LLMProvider (Emergent Universal LLM key, gpt-5.4-mini, strict
  JSON). Switch via AI_PROVIDER=sandbox|llm (AI_MODEL, EMERGENT_LLM_KEY). Versioned,
  append-only prompts (prompts.py, ACTIVE per objective).
- Choreography: ListingPublished -> AI auto-enriches (detected brand, suggested
  category, quality score 0-100, condition estimate, seller recommendations) AND
  fraud-scores (risk 0-1 + flags: replica/fake/mirror/aaa/wire transfer/gift card/
  off-platform/whatsapp/telegram/price_too_low). Idempotent (skips if a completed job
  for the subject exists). When risk >= AI_FRAUD_THRESHOLD (0.75) it opens/merges a
  Moderation case via a "system-ai" report (reason=ai_fraud_signal) for HUMAN review —
  NO automatic takedown. Reads listing content only via ListingContract.detail.
- AI APIs: GET /api/ai/listings/{id} (enrichment; owner or staff), POST
  /api/ai/listings/{id}/enrich (re-run; owner or staff), GET /api/ai/listings/{id}/fraud
  (moderator/admin only).
- Analytics bounded context (DOMAIN-012, read-only, never writes): GET
  /api/analytics/seller (net revenue, completed orders, pending escrow payout, active/
  total listings by state, sales, offers received+accept rate, rating); GET
  /api/analytics/marketplace (staff: GMV, platform fees, orders by status, users,
  listings by state, open cases + AI fraud signals, top brands/categories).
- Hardening: RateLimitMiddleware (in-memory sliding window keyed by real client IP via
  X-Forwarded-For) — login/register 100/60s, forgot/reset-password 5/300s; returns 429
  RATE_LIMITED; toggle RATE_LIMIT_ENABLED (default on). SecurityHeadersMiddleware
  (X-Content-Type-Options, X-Frame-Options=DENY, Referrer-Policy, X-XSS-Protection,
  Permissions-Policy).
- Frontend: /analytics (seller dashboard, stat cards + listings-by-state), /admin/analytics
  (marketplace overview: GMV/fees/orders/users/listings, status+state bar charts, top
  brands/categories), AIInsights panel on ListingDetail for owner/staff (quality bar,
  detected attribute badges, recommendations, "advisory only" note, Analyse/Refresh).
  Nav: "Analytics" (all users), "Insights" (staff -> marketplace analytics).
- Config: AI_PROVIDER=sandbox, AI_MODEL=gpt-5.4-mini, AI_FRAUD_THRESHOLD=0.75,
  EMERGENT_LLM_KEY set. Tests: test_ai.py (15: domain lifecycle, sandbox determinism,
  fraud flags, enrichment/fraud API authz, publish->enrich+fraud->moderation
  choreography, seller+marketplace analytics shape/authz, security headers, rate limit).
  Full backend 160/160.

## To activate real LLM enrichment (Phase 12 go-live)
Set backend/.env: AI_PROVIDER=llm (AI_MODEL=gpt-5.4-mini, EMERGENT_LLM_KEY already set).
Restart backend. Sandbox remains the deterministic default for CI/local.

## Carried technical debt (Phase 12)
- Rate limiter is single-pod in-memory (move to Redis for multi-pod). No AI job pagination/
  history UI. AI re-enrichment is manual (owner/staff button); auto only on first publish.
- Fraud signal opens a case but does not auto-prioritise/escalate. Analytics has no date-range
  filters or time-series (point-in-time aggregates only).

## Remaining backlog (post Phase 12)
- P2: Extract Search into its own bounded context (currently in Listings).
- P2: Redis pub/sub for WebSocket ConnectionManager (multi-pod messaging/notifications).
- P2: Pagination on Orders/Payments/Shipments/Reviews/Messaging/Moderation/AI lists.
- P2: Messaging attachments (object storage + async virus scan); scheduled/expiring
  notifications + email retry queue; temporary-suspension auto-expiry + reactivate endpoint.
- P3: Frontend double-WS-connection cleanup (shared app-level WebSocket context).
