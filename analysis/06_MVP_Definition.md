# 06 — MVP Definition

**Definition:** the smallest **production-ready** slice that lets a real seller list a real item and a real buyer purchase, pay, receive, and review it — with trust and safety intact — in **Ukraine**, on an architecture ready for EU expansion.

The MVP is derived directly from Product_Requirements §5 "Phase 1 (MVP)". Every included capability maps to the mission (DOC-000 §2): make selling easier, buying faster, increase trust, reduce manual work, improve discovery, improve transaction success.

## In scope (and why each belongs)

| Capability | Why it is in the MVP (not optional) |
|---|---|
| **Identity** (register, verify, login, sessions, RBAC, password reset) | Nothing on the platform can happen without authenticated identity (Req §4 root dependency; BR-010, BR-110). |
| **Profiles** (public profile, seller/buyer info, reputation display) | Buyer confidence questions "can I trust the seller?" must be answerable (DOC-001 §3.7). |
| **Listings** (draft→publish, photos, structured attributes, pricing, lifecycle) | The central marketplace entity; without it there is no supply (DOMAIN-002; DOC-001 §3.6). |
| **Search & Discovery** (keyword + filters + facets + sort, MVP tier) | "Search over navigation" is a core principle; discovery in <10s (DOC-000 §9; DOC-001 §3.5). Postgres FTS is enough for launch. |
| **Offers & Negotiation** (create/counter/accept/reject/expire, atomic acceptance) | Negotiation is the defining fashion-resale interaction (Grailed pattern); Critical in Req §5. |
| **Orders** (immutable agreement, lifecycle, one active order per listing) | The commercial contract; the spine of commerce (DOMAIN-005). |
| **Payments** (authorize/capture/refund, escrow, fees, idempotent) | No order without authorized payment (BR-042); trust requires secure funds handling (DOC-001 §3.2). |
| **Shipping** (labels, tracking, delivery confirmation; Nova Poshta/Ukrposhta) | Physical delivery is the fulfillment half of the transaction (DOMAIN-007). |
| **Reviews & Reputation** (post-order rating + response) | Trust engine; drives repeat buyers/sellers, a primary success metric (DOC-000 §11). |
| **Messaging** (contextual buyer↔seller chat + images) | Buyers ask before buying; reduces failed transactions (DOMAIN-009). |
| **Notifications** (in-app + email, event-driven) | Users must never guess system state (DOC-001 §3.13); keeps transactions moving. |
| **Moderation** (reports → cases → decisions) | Trust above everything; a marketplace without moderation degrades immediately (DOC-001 §3.2; DOMAIN-011). |
| **Administration** (config, feature flags, maintenance, admin RBAC) | Required to *operate* safely and to gate risky launches behind flags (DOMAIN-012). |
| **Security & Infra** (server-side authZ, audit, rate limiting, logging, health, backups, storage, CDN) | Non-negotiable production baseline (STD-005; DOC-000 §13). |
| **Localization foundation** (currency/language/tax/shipping as config, UAH + Ukrainian/English) | i18n must exist in v1 even with one active market (DOC-000 §4, §12). |

## Explicitly OUT of the MVP (and why)

| Excluded | Reason |
|---|---|
| **AI features** (auto-listing, semantic/visual search, price suggestions, AI moderation) | Req §5 places these in Phase 2/3. They are *enhancements*, not required for a working transaction. Architecture reserves clean insertion points (DOMAIN-013). Including them early violates DOC-001 §3.4 (simplicity) and adds cost/latency/non-determinism risk. |
| **Recommendations, collections, follows** | High/Medium priority; Phase 2. Discovery works via search alone at launch. |
| **Push/SMS/Telegram/WhatsApp** | In-app + email suffice for MVP (DOMAIN-010 §9 lists them as future). |
| **Advanced analytics/BI** | Medium priority (Req §5 Phase 3); event stream is captured from day one, dashboards come later. |
| **Multi-item orders, bundles, split shipments, auctions, rental, crypto/NFT, live/social** | Out of scope by DOC-000 §14 and per-domain "one listing = one item" (BR-018). |
| **Second country / multi-currency checkout live** | Architecture supports it; only Ukraine is *activated* at launch (DOC-000 §4). |

## MVP acceptance (end-to-end journey that must pass in production)

1. Seller registers, verifies email, creates a listing with photos + structured attributes, publishes.
2. Listing appears in search with correct filters/facets; hidden/sold never appear.
3. Buyer discovers it, messages the seller, submits an offer; seller counters; buyer accepts.
4. Acceptance atomically creates exactly one Order (even under concurrency); listing becomes Reserved.
5. Buyer pays (escrow held); Payment captured → Order Paid; seller notified.
6. Seller generates a Nova Poshta label; tracking flows; delivery confirmed → Order Completed; funds released per policy.
7. Both parties review; reputation updates; a bad actor can be reported → moderated.
8. Operators can toggle a feature flag and enter maintenance mode without a deploy.

Every step is authorized server-side, audited, event-driven, and covered by automated tests referencing the relevant Business Rule IDs.

## MVP guardrails (from principles)
- **Trust > convenience** at every conflict (DOC-001 §5 hierarchy).
- **Mobile-first** UI (DOC-001 §3.10).
- **Structured data first** — attributes over free text (DOC-001 §3.9).
- **Listing creation < 1 min, discovery < 10 s** as UX targets (DOC-000 §9).
