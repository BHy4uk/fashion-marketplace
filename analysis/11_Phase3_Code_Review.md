# 11 — Phase 3 Code Review (pre-Phase-4)

## Compliant
- Domain layers pure; no framework/DB in domain (STD-007 §7). ✓
- Explicit state machines, validated transitions, events on transition (STD-004). ✓
- Optimistic concurrency via version + guarded replace_one (STD-003 §9). ✓
- Money = integer minor units; soft delete; UTC; audit fields; DomainError→HTTP. ✓

## Deviations / technical debt
| # | Item | Severity | Plan |
|---|------|----------|------|
| 1 | `Listings.service` reads `identity_users` collection directly (cross-module DB access) | HIGH (boundary) | Introduce `*.Contracts`; Offers uses them from day one; refactor Listings later. |
| 2 | Search lives inside Listings (not its own Search bounded context, DOMAIN-003) | MEDIUM | Extract to Search module when indexing backend upgrades. |
| 3 | Outbox = 2 writes (save + insert_many), not one ACID tx | HIGH (before Payments) | Move to Mongo multi-doc transaction (replica set) or embed events in aggregate doc. |
| 4 | Email verification auto-activated (spec says mandatory) | LOW | Enforce in a later hardening pass. |
| 5 | `ListingService.archive` dead code (router uses `remove`) | LOW | Remove or expose seller-archive UI. |

## Aggregate boundary / coupling
- Only violation: Listings→identity_users (item 1). No circular deps. Domain events used correctly.

## Simplification opportunities
- Consolidate `Money` into the shared kernel (done in Phase 4) to avoid per-module duplication.
- `_view` projection could become an explicit read-model later.

## Verdict
Architecture is fundamentally sound. Items 1 and 3 are the priorities; item 3 must be resolved before
Payments (Phase 5). Phase 4 introduces the contracts pattern to stop boundary drift.
