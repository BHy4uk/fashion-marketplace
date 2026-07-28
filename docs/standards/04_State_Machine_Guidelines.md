# State Machine Guidelines

**Version:** 1.0
**Status:** Approved
**Document ID:** STD-004

---

# 1. Purpose

This document defines the standards for modeling lifecycle state machines across the marketplace.

State machines ensure that business entities transition between valid states while preserving domain invariants.

These guidelines apply to every Aggregate Root with a business lifecycle.

---

# 2. Guiding Principles

A state machine represents the lifecycle of a business entity.

It defines:

- valid states;
- valid transitions;
- transition rules;
- terminal states;
- business events produced by transitions.

State machines belong to the Domain layer.

---

# 3. When to Use a State Machine

A state machine should be used when:

- an entity has multiple business states;
- transitions are restricted;
- transition rules affect business behavior;
- invalid transitions must be prevented.

Simple flags should not be modeled as state machines.

---

# 4. State Ownership

Each Aggregate Root owns its own state machine.

No external domain may directly change another aggregate's state.

State transitions occur only through aggregate behavior.

---

# 5. States

States represent stable business conditions.

Examples:

Draft

Published

Reserved

Sold

Archived

States are business concepts.

They are not technical implementation details.

---

# 6. Transitions

Transitions represent valid business operations.

Every transition must be explicitly defined.

Undefined transitions are prohibited.

---

# 7. Transition Validation

Every transition must validate:

- current state;
- business invariants;
- permissions where applicable;
- required business conditions.

Invalid transitions must be rejected.

---

# 8. Terminal States

Terminal states cannot transition further unless explicitly defined.

Examples:

Canceled

Completed

Closed

Deleted

Terminal states should remain stable.

---

# 9. Reversible and Irreversible Transitions

Some transitions may be reversible.

Examples:

Draft → Published → Draft

Others are irreversible.

Examples:

Paid

Delivered

Refunded

Irreversible transitions should reflect irreversible business facts.

---

# 10. Transition Side Effects

State transitions may produce:

- Domain Events;
- audit entries;
- background jobs;
- notifications.

State transitions must not directly invoke infrastructure services.

---

# 11. Domain Events

Successful transitions should publish Domain Events.

Events describe completed business facts.

Examples:

ListingPublished

OfferAccepted

OrderCanceled

PaymentCaptured

ShipmentDelivered

---

# 12. Aggregate Consistency

State transitions must preserve aggregate invariants.

The aggregate must never enter an invalid state.

Validation occurs before the transition completes.

---

# 13. Concurrency

Concurrent transitions must be detected.

Only one valid transition should succeed.

Conflict resolution belongs to the application layer.

---

# 14. Transition Granularity

One transition represents one business operation.

Transitions should remain focused and atomic.

Business workflows may consist of multiple transitions across different aggregates.

---

# 15. State Representation

States should be represented explicitly.

State values should remain stable.

Meaning should not change over time.

---

# 16. State History

Business entities should preserve significant state transitions for audit purposes.

Historical transitions should not be rewritten.

---

# 17. Cross-Domain Coordination

State transitions affect only the owning aggregate.

Other domains react through Domain Events.

Aggregates never transition each other's state directly.

---

# 18. Error Handling

Invalid transitions should return deterministic business errors.

Errors should explain why the requested transition is not allowed.

State should remain unchanged after a failed transition.

---

# 19. Testing

Every state machine should be fully testable.

Tests should verify:

- valid transitions;
- invalid transitions;
- terminal states;
- event publication;
- invariant preservation;
- concurrency behavior.

---

# 20. Prohibited Practices

The following are prohibited:

- modifying state outside the aggregate;
- bypassing transition validation;
- changing state directly through persistence;
- skipping intermediate states;
- coupling transitions to infrastructure;
- using state as a permission system.

---

# 21. Non-Goals

This document does not define:

- workflow engines;
- BPMN;
- orchestration tools;
- infrastructure messaging;
- UI behavior.

---

# 22. Compliance Checklist

Every state machine should:

- belong to a single aggregate;
- define explicit states;
- define explicit transitions;
- protect business invariants;
- publish Domain Events;
- support auditability;
- detect concurrent updates;
- reject invalid transitions;
- remain independent of infrastructure.