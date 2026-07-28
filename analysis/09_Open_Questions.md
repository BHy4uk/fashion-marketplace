# 09 — Open Questions (only what the spec cannot answer)

These are **not** answered anywhere in `docs/`. I have proposed the smallest architecture-consistent default for each so implementation is never blocked; please confirm or correct. Questions whose answers already exist in the spec have been deliberately excluded.

---

### Q1 — Database Design standard is empty
`standards/03_Database_Design.md` contains no content. All other standards are complete. **Proposed default:** PostgreSQL, schema-per-module, no cross-schema FKs, ID-only references, `bigint`/`uuid` surrogate keys + public opaque IDs, mandatory audit columns (BR-123), soft delete, optimistic concurrency via version column. **Confirm** or provide the intended standard.

### Q2 — Payment provider(s) for the Ukraine launch
Spec lists Stripe/Adyen/PayPal as *examples* and mandates multi-provider, but doesn't name the launch provider. **Stripe Connect coverage/onboarding in Ukraine is uncertain.** **Proposed default:** Stripe Connect (EU) + one Ukraine-local provider (LiqPay or Fondy) behind `IPaymentProvider`. **Which local provider do you have a merchant relationship with?**

### Q3 — Escrow & fund-release policy
BR-051/062 say payouts occur after settlement and delivery may not auto-release funds "if additional verification is required." The exact release trigger and hold window are unspecified. **Proposed default:** release to seller X days after Delivered/Completed, minus platform fee; disputes freeze release. **Specify X and the dispute hold rules.**

### Q4 — Platform fee / take-rate model
Fees and payouts are referenced (F09, BR-050) but no rate/structure is given. **Proposed default:** config-driven percentage + optional fixed fee, per-country, stored in Administration config. **Provide the intended fee model** (buyer-side, seller-side, or split; %/flat).

### Q5 — Direct "Buy Now" vs offer-only
DOMAIN-005 §7 allows an order from "an accepted Offer (if applicable)" or an authorized purchase — implying a direct buy path. It's not explicit whether every listing supports Buy Now, offers, or both. **Proposed default:** listings support both; seller may disable offers per listing. **Confirm.**

### Q6 — Return / refund policy window
Payments supports refunds and Orders has Refunded/Closed states, but the consumer return window and who bears return shipping are unspecified (EU consumer law may apply post-expansion). **Proposed default:** configurable return window per region; MVP (Ukraine C2C) = no statutory cooling-off, refunds only for non-delivery/not-as-described via dispute. **Confirm policy.**

### Q7 — Reputation score formula & ownership
Reviews provide *inputs*; DOMAIN-008 §11 says aggregation belongs to "Identity or Analytics" — it doesn't decide which, nor the formula. **Proposed default:** Identity owns a `ReputationScore` value object computed from Review events (avg rating + volume + recency). **Which domain owns it, and what formula?**

### Q8 — MFA in v1 scope
Identity lists MFA and "sensitive operations require re-authentication when appropriate," but Authentication §7 says v1 = email+password only. **Is MFA required for MVP, or MFA-ready (schema/hooks) with enforcement deferred?** **Proposed default:** MFA-ready, enforcement in M3.

### Q9 — Data residency & GDPR posture for EU expansion
Compliance is required (STD-005 §23) but residency (EU-region storage), DSAR/erasure workflow vs. "preserve business history" (BR-004/121) tension is unspecified. **Proposed default:** anonymize PII on erasure while retaining append-only financial/audit records; EU-region storage from M4. **Confirm the erasure-vs-retention reconciliation.**

### Q10 — Real-time messaging transport
Messaging is "asynchronous" and Notifications lists WebSocket as *future*. Is near-real-time chat (typing/instant delivery) expected at MVP, or is polling/email-notified async acceptable? **Proposed default:** async with in-app + email notifications for MVP; WebSocket/SSE in M6.

### Q11 — Categories & attribute taxonomy source
Listings need a structured brand/category/size taxonomy (DOC-001 §3.9) but no canonical taxonomy is provided. **Proposed default:** platform-managed seed taxonomy (Administration config) covering the included categories (DOC-000 §5), extensible. **Do you have an existing taxonomy/brand list to import?**

### Q12 — Team, timeline, budget envelope
Not a spec item, but needed to turn "relative complexity" into a real schedule and to right-size infra (managed K8s vs PaaS). **How many engineers, target launch date, and infra budget?**

---

**Note:** All 12 have safe defaults; none block starting Phase 0. Q1–Q4 should be resolved before Phase 2 (Listings persistence) and Phase 5 (Payments) respectively.
