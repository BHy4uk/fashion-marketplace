# ADR-0001 — Implementation stack for the Modular Monolith

**Status:** Accepted · **Date:** 2026-06

## Context
The specification mandates DDD + Clean Architecture + Modular Monolith with domain events,
aggregate boundaries, state machines, and provider replaceability. STD-007 §18 and STD-003 §1/§22
explicitly state the specification is **technology- and engine/ORM-neutral**: the implementer may
choose techniques provided the architecture and business behavior are preserved.

The runtime platform (Kubernetes ingress + supervisor) is natively wired for a **Python FastAPI**
backend on port 8001 (`/api` prefix) and a **React** frontend on port 3000, with **MongoDB** provided.

## Decision
Implement the mandated architecture on the platform-native stack:
- **Backend:** Python 3.11 + FastAPI (layered per module: `domain` → `application` → `infrastructure` → `api`).
- **Persistence:** MongoDB (aggregate-per-document, reference-by-ID, `version` for optimistic
  concurrency, UTC timestamps, soft delete, collection-prefix "schema-per-module" isolation).
  Compliant with STD-003 which forbids prescribing an engine/ORM.
- **Domain events:** in-process dispatcher + **Transactional Outbox** collection + background relay.
- **Providers behind interfaces:** `IPaymentProvider` (LiqPay first), `IShippingProvider`
  (Nova Poshta first), `IAiProvider`, `IFileStorage`, `ISearchIndex` — all config-selected.
- **Frontend:** React (CRA) SPA, mobile-first, per design_guidelines.json.

## Consequences
- All architectural rules (aggregate ownership, domain events, state machines, infra independence)
  are preserved; only the language/engine differ from the earlier .NET recommendation.
- Future extraction to services remains possible: modules keep isolated collections + published
  contracts + events.
- If a future requirement demands .NET/PostgreSQL specifically, this ADR is superseded by a new ADR;
  the domain layer is written to be portable (no framework leakage).
