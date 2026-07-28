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

## Next phases (post Phase 7)
- Phase 8 Reviews (DOMAIN-008, feeds Identity reputation) — now unblocked (orders reach Completed).
- Phase 9 Messaging (WebSockets). Phase 10 Notifications. Phase 11 Moderation+Admin UI. Phase 12 AI+Analytics.

## Carried technical debt (Phase 7)
- Shipment: no pagination; single parcel/seat; buyer shipping address not collected at checkout
  (dispatch accepts optional to_address/parcel). Sandbox delivery requires buyer confirmation
  (real carriers auto-deliver via sweeper). Search still coupled inside Listings.
