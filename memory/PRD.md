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
