# 10 — Specification Review (FAANG-level architecture review)

Reviewing `docs/` as if in a senior design review. I flag **contradictions**, **hidden assumptions**, **scalability**, **maintainability**, **missing specs**, and **opportunities** — and, per instruction, I explicitly call out where the spec is **already optimal** and should not be changed. Changes are proposed only with architectural justification; the spec wins by default.

---

## A. Overall assessment

This is an **unusually strong, internally coherent specification** — well above typical startup docs. It correctly separates Vision → Principles → Business Rules → Domain Model → Architecture → Domain specs → Standards, and it maintains a consistent ubiquitous language across all 27 documents. The DDD/Clean/Modular-Monolith stance is applied *consistently*, not name-dropped. Ownership rules (AI owns nothing; Search owns derived data; Notifications own intent not transport; Administration delegates) are exactly right and are the parts I recommend **keeping untouched**.

**Verdict:** ready to implement, subject to closing the gaps below. None of the gaps require architectural redesign — they are *completions*, not corrections.

---

## B. Contradictions & tensions (must resolve)

**C1 — Order creation trigger is ambiguous.** DOMAIN-004 §9 says accepting an offer "initiates Order creation"; DOMAIN-005 §7 says an order needs "the purchase has been authorized by business rules" and references "one accepted Offer (if applicable)". Meanwhile BR-042: "An order cannot exist without successful payment authorization." These three can conflict: does Order exist *before* payment (state `AwaitingPayment` implies yes) or only *after* authorization (BR-042 implies no)? **Resolution:** treat BR-042 as "an order cannot *proceed past Created/AwaitingPayment* without payment authorization," i.e., Order is created on offer acceptance in `Created→AwaitingPayment`, and payment authorization is required to leave `AwaitingPayment`. The Order lifecycle itself supports this reading. **Recommend clarifying BR-042 wording** to remove the surface contradiction.

**C2 — Reputation ownership undecided.** DOMAIN-008 §11 assigns reputation aggregation to "the Identity **or** Analytics domain." "Exactly one domain owns each capability" (DOC-004 §13) forbids "or." **Resolution needed** (see Open Question Q7). Not a redesign — a one-line ownership decision.

**C3 — "No business rule may exist exclusively in the frontend" vs. UX targets.** BR-132 + DOC-005 §7 forbid frontend business logic; fine. But the sub-1-minute listing UX (DOC-000 §9) plus AI assist implies significant client interactivity. **No real contradiction** — it just must be enforced that client-side validation is *duplicated* server-side, never *authoritative*. Flagging as an implementation discipline, not a spec change.

**C4 — Offer vs. direct purchase.** DOMAIN-002 §13 "Only Available listings may receive new offers" and the Orders spec's "authorized purchase" imply Buy-Now exists, but no domain document specifies a Buy-Now command or its rules. **Gap, not contradiction** — see Q5.

---

## C. Hidden assumptions (make explicit)

- **HA1 — Single-item inventory forever in v1.** BR-018 (one listing = one physical item) is a strong, clean constraint that simplifies Orders/Offers/Payments enormously. It is **optimal for fashion resale** and should stay. Just note that "quantity" appears nowhere by design — good.
- **HA2 — Eventual consistency is acceptable for search/notifications/AI but NOT for money/orders/offers.** The spec implies this (Search §6 "eventually consistent"; Payments/Orders demand atomicity) but never states the consistency policy globally. **Recommend adding** a one-paragraph "Consistency Model" to Architecture Principles.
- **HA3 — Currency/tax are per-listing/per-order snapshots.** Multi-currency is required, but the spec doesn't say money values are captured at transaction time. `Money` as an immutable value object with currency, snapshotted on Order (BR-044 immutability), is the correct implied model. **Recommend stating it.**
- **HA4 — One active market at launch despite multi-country architecture.** Correctly assumed; just ensure feature flags gate market activation.
- **HA5 — Time & idempotency.** Many rules assume UTC timestamps and idempotency keys but only Payments/Notifications state it. **Recommend** a global "all timestamps UTC; externally-triggered commands carry idempotency keys" rule.

---

## D. Scalability review

- **Optimal:** schema-per-module + events + rebuildable search + async-first + stateless services give a clean scale-out and extraction path. Keep as is.
- **Watch:** the spec says "future extraction to microservices without redesign" (DOC-005 §3) — this is only true if **no cross-schema FKs and no cross-module DB reads** are ever introduced. The spec *states* the rule (§24) but doesn't give an *enforcement mechanism*. **Opportunity:** mandate automated architecture tests (add to Standards). This is the single highest-leverage addition.
- **Gap:** no stated SLOs (latency/throughput targets) beyond qualitative "fast." **Recommend** adding target SLOs for the critical paths named in DOC-005 §21 (auth, search, listing retrieval, checkout, messaging) so performance regressions are objectively detectable (DOC-001 §3.14 already calls regressions "defects" — give them numbers).
- **Gap:** no rate-limit/quotas numbers, no pagination max sizes. STD-002 §9 says "avoid unbounded collections" — good — but pick concrete caps.

---

## E. Maintainability review

- **Optimal:** immutable events, append-only history, ADR governance, "evolution over revolution," ubiquitous language. This is a maintainer's dream. Keep.
- **Gap — versioning strategy for events** exists (STD-001 §14) but no concrete scheme (e.g., `v1` suffix, schema registry). **Recommend** picking one before the first cross-module event ships.
- **Gap — error-code catalog.** Every domain lists error scenarios (e.g., `OfferAlreadyAccepted`) and STD-002 §14 mandates error codes, but there is **no central error-code registry**. **Recommend** a single `Error Codes` standard mapping stable codes ↔ HTTP statuses ↔ BR IDs. Prevents drift across 13 modules.
- **Gap — API pagination/filtering concrete contract.** STD-002 describes principles but not the exact envelope (page/pageSize vs cursor, response metadata shape). **Recommend** a concrete API response/error envelope spec so all 13 modules are consistent from endpoint #1.

---

## F. Missing specifications (should be authored)

1. **`03_Database_Design.md` is empty** — highest priority; blocks consistent persistence (Q1).
2. **Consistency Model** (strong vs eventual per operation class) — see HA2.
3. **Error-Code Registry** — see §E.
4. **API envelope & pagination concrete contract** — see §E.
5. **SLO / performance budget document** — see §D.
6. **Fee/escrow/payout policy** — business input needed (Q3, Q4).
7. **Category & attribute taxonomy** — the structured-data principle needs a canonical taxonomy (Q11).
8. **Data-retention & GDPR erasure vs. append-only reconciliation** (Q9) — tension between BR-004/121 (preserve history) and the right to erasure.
9. **Localization spec** — how currency/tax/language/address formats are modeled (referenced everywhere, specified nowhere).
10. **Testing/coverage policy** — DOC-005 §20 lists test types; add coverage expectations and the BR-ID traceability convention (BR §19 implies it).

---

## G. Opportunities (optional, justified)

- **O1 — Encode "Prohibited Practices" (DOC-005 §24) as CI architecture tests.** Turns prose rules into build failures. Highest ROI; no downside.
- **O2 — Outbox + Inbox pattern** explicitly named in the events standard, so every team implements reliable delivery identically (the standard says "guarantee eventual publication" but leaves the mechanism open — naming it prevents divergence).
- **O3 — Read models / CQRS projections** as first-class in the Domain Model doc. The spec already separates commands/queries (DOC-005 §10); making read models explicit improves list/search/dashboard performance without touching aggregates.
- **O4 — A "Ports & Adapters" appendix** enumerating every required provider interface (`IPaymentProvider`, `IShippingProvider`, `IAiProvider`, `ISearchIndex`, `IFileStorage`, `IEmailSender`, `IEventBus`). The replaceability principle (DOC-001 §3.21) is stated repeatedly; listing the ports operationalizes it.
- **O5 — Idempotency-key standard** for all state-changing POSTs (STD-002 §15 allows it; make it a convention for offer/order/payment/message creation).

---

## H. What is already optimal — do NOT change

- **Domain ownership & aggregate boundaries** (DOC-004) — precise and correct.
- **AI as a non-owning, advisory, human-in-the-loop bounded context** (DOMAIN-013, BR-100..104) — exactly the right posture; resist any pressure to let AI auto-act.
- **Notifications-from-events-only + idempotent** (DOMAIN-010) — textbook correct.
- **Search owns only derived, rebuildable indexes** (DOMAIN-003) — correct.
- **Payments never mutates Orders; Orders decides on events** (DOMAIN-006 §14) — correct choreography, preserves ownership.
- **One listing = one item** (BR-018) — the right simplifying constraint for the vertical.
- **Soft delete + append-only history + immutable audit** (BR-004/016/044/054/120..123) — essential for a financial marketplace; keep strict.
- **Provider replaceability across payment/shipping/auth/AI/cloud** (DOC-000 §13) — strategically correct for an EU-expansion product.
- **The document hierarchy & "specification wins" rule** (STD-007 §2, §3) — keep as the governance backbone.

---

## I. Reviewer's bottom line

The architecture is sound and should be implemented **as written**. The work before Phase-2 coding is *completion* (author the empty DB standard, decide reputation ownership, pin down fee/escrow/consistency/error-code/API-envelope specifics) and *enforcement* (architecture tests + outbox). None of these alter the design; they harden it. I recommend proceeding to Phase 0 (foundation/walking skeleton) immediately, in parallel with resolving Open Questions Q1–Q4.
