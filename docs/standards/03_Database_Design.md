# Database Design Standard

**Version:** 1.0
**Status:** Approved
**Document ID:** STD-003

---

# 1. Purpose

This document defines the database design standards for the marketplace.

The objective is to ensure consistency, integrity, maintainability, and scalability across the persistence layer.

This document defines logical persistence rules.

It does not prescribe any specific database engine or ORM.

---

# 2. Guiding Principles

The database exists to persist domain state.

Business rules belong to the Domain layer.

The database must never become the source of business logic.

Persistence should faithfully represent the domain model.

---

# 3. Aggregate Persistence

Each Aggregate Root owns its persistence boundary.

Child entities belong exclusively to their aggregate.

Aggregates reference other aggregates by identifier only.

Cross-aggregate ownership is prohibited.

---

# 4. Identity

Every Aggregate Root has a globally unique identifier.

Identifiers are immutable.

Database-generated sequential identifiers must never be exposed as business identifiers.

---

# 5. Foreign Keys

Foreign keys represent relationships.

They must never replace aggregate boundaries.

Cross-domain references should be minimized.

Aggregates communicate through identifiers and Domain Events.

---

# 6. Timestamps

Persistent entities should record:

- CreatedAt
- UpdatedAt

Business entities may additionally record domain-specific timestamps when required.

All timestamps should be stored in UTC.

---

# 7. Soft Delete

Business entities should prefer soft deletion.

Deleted records remain available for:

- audit;
- historical reporting;
- recovery when permitted.

Physical deletion should be reserved for infrastructure or regulatory requirements.

---

# 8. Auditability

Business-critical changes should remain auditable.

Audit information should not replace Domain Events.

The persistence model should support reconstruction of historical state where required.

---

# 9. Optimistic Concurrency

Aggregates should support optimistic concurrency.

Concurrent updates should be detectable.

Conflict resolution belongs to the application and domain layers.

---

# 10. Transactions

Transactions should remain scoped to a single aggregate whenever possible.

Distributed transactions should be avoided.

Cross-domain consistency should be achieved through Domain Events and eventual consistency.

---

# 11. Value Objects

Value Objects should be persisted together with their owning aggregate.

They do not require independent identity.

---

# 12. Collections

Collections belong to their owning aggregate.

Ordering should be deterministic when business meaning depends on order.

---

# 13. Indexing

Indexes should support business queries.

Indexes are implementation details.

Indexes must not influence domain modeling.

---

# 14. Normalization

The persistence model should avoid unnecessary duplication.

Controlled denormalization is acceptable when justified by performance or reporting requirements.

Business correctness takes precedence over optimization.

---

# 15. Schema Evolution

Database schemas evolve through versioned migrations.

Schema changes should preserve existing data whenever possible.

Breaking schema changes require explicit migration planning.

---

# 16. Historical Data

Historical business information should be preserved.

Business history should remain queryable without modifying historical records.

---

# 17. Read Models

Read models may differ from write models.

Read optimization must never compromise aggregate consistency.

Read models may be regenerated from authoritative data.

---

# 18. AI Data

AI-generated data should remain separate from core business state where practical.

AI enrichments must not overwrite authoritative business information.

Historical AI analyses should remain available.

---

# 19. File References

Binary files should not be stored directly within business aggregates.

Business entities should reference externally managed files through stable identifiers.

File lifecycle is governed by the File Storage Architecture.

---

# 20. Security

Sensitive data should be protected at rest.

Access to persisted data should follow the principle of least privilege.

Security implementation details are defined by the Security Architecture.

---

# 21. Backup and Recovery

The persistence layer must support reliable backup and recovery procedures.

Recovery processes should preserve business integrity and audit history.

---

# 22. Non-Goals

This document does not define:

- database engine selection;
- ORM implementation;
- SQL conventions;
- migration tooling;
- indexing strategy for a specific vendor;
- deployment configuration.

---

# 23. Compliance Checklist

Every persistence design should:

- preserve aggregate boundaries;
- use immutable identifiers;
- support optimistic concurrency;
- record timestamps in UTC;
- support auditability;
- preserve historical data;
- avoid business logic in the database;
- keep binary files outside business entities;
- support schema evolution.