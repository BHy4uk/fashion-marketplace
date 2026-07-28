# Domain Events Standard

**Version:** 1.0
**Status:** Approved
**Document ID:** STD-001

---

# 1. Purpose

This document defines the standard for Domain Events across the marketplace.

Domain Events are the primary mechanism for communicating completed business facts between domains while preserving domain boundaries and aggregate ownership.

This standard applies to every domain in the system.

---

# 2. Guiding Principles

Domain Events exist to communicate business facts.

A Domain Event:

- describes something that has already happened;
- is immutable;
- belongs to the domain that owns the business fact;
- may be consumed by zero or more other domains.

Domain Events never transfer ownership of business entities.

---

# 3. What Is a Domain Event

A Domain Event represents a completed business occurrence that is meaningful to the business domain.

Examples:

- UserRegistered
- ListingPublished
- OfferAccepted
- OrderCreated
- PaymentCaptured
- ShipmentDelivered
- ReviewPublished

Events describe facts.

They do not describe intentions or requests.

---

# 4. What Is NOT a Domain Event

The following are not Domain Events:

- API requests
- Commands
- Queries
- Database changes
- Infrastructure notifications
- Cache updates
- Logging events
- External provider callbacks

Infrastructure events should never leak into the domain model.

---

# 5. Ownership

Every Domain Event is owned by exactly one domain.

Examples:

Identity

- UserRegistered

Listings

- ListingPublished

Offers

- OfferAccepted

Orders

- OrderCreated

Payments

- PaymentCaptured

Only the owning domain may publish the event.

Other domains may consume it but never publish it on behalf of another domain.

---

# 6. Naming Convention

Domain Events use the following convention:

<Entity><PastTenseVerb>

Examples:

- ListingPublished
- ListingArchived
- OrderCreated
- OrderCanceled
- PaymentCaptured
- ShipmentDelivered
- ReviewPublished

Events must describe completed facts.

Names must never contain imperative verbs.

Incorrect:

- PublishListing
- CreateOrder
- CapturePayment

---

# 7. Event Timing

Events are published only after the business transaction has been successfully completed.

Business state must already be valid.

Consumers should be able to assume the event represents truth.

---

# 8. Event Immutability

Domain Events are immutable.

Published events are never modified.

Corrections are represented by new events.

Example:

Incorrect:

Update OrderCreated

Correct:

OrderCorrected

---

# 9. Event Payload

Event payloads should contain only information required by consumers.

Typical payload includes:

- Event ID
- Event Type
- Aggregate ID
- Aggregate Version
- Occurred At (UTC)
- Correlation ID
- Causation ID

Business-specific fields may be included when required.

Payloads should avoid unnecessary duplication.

---

# 10. Aggregate Version

Events should include the aggregate version when supported.

Consumers may use the version to detect stale or duplicate processing.

---

# 11. Idempotency

Consumers must assume events may be delivered more than once.

Event processing must be idempotent.

Duplicate event delivery must not produce duplicate business effects.

---

# 12. Ordering

Ordering is guaranteed only within a single aggregate.

Cross-aggregate ordering must never be assumed.

Consumers should be resilient to out-of-order delivery.

---

# 13. Event Consumption

Consumers should:

- validate event schema;
- ignore unknown optional fields;
- remain tolerant of future schema evolution;
- avoid direct dependencies on publisher internals.

Consumers must not mutate publisher-owned aggregates.

---

# 14. Event Versioning

Breaking changes require a new event version.

Existing consumers should continue functioning during migration.

Versioning strategy must preserve backward compatibility whenever possible.

---

# 15. Event Reliability

Publishing Domain Events must be reliable.

If event publication fails, the platform must ensure eventual publication through a reliable delivery mechanism.

Implementation details are infrastructure concerns.

---

# 16. Domain Boundaries

Domain Events communicate business facts.

They do not replace domain ownership.

Receiving an event does not grant authority to modify another domain's aggregates.

Each domain remains responsible for enforcing its own invariants.

---

# 17. Security

Sensitive information should never be included unless required.

Personally identifiable information should be minimized.

Secrets, credentials, and tokens must never appear in Domain Events.

---

# 18. Audit

Every published Domain Event is part of the platform's audit history.

Events should remain traceable to:

- aggregate;
- business transaction;
- initiating request;
- authenticated actor where applicable.

---

# 19. Prohibited Practices

The following are prohibited:

- Publishing events before transaction completion.
- Mutating published events.
- Publishing another domain's events.
- Encoding business commands as events.
- Using events for synchronous request/response communication.
- Including infrastructure-specific implementation details.
- Treating events as the system of record.

---

# 20. Examples

Good

- UserRegistered
- ListingPublished
- OfferRejected
- OrderCreated
- PaymentCaptured
- ShipmentDelivered
- ReviewPublished

Bad

- PublishListing
- CreateOrder
- ProcessPayment
- UpdateShipment
- SendNotification

---

# 21. Compliance Checklist

Every Domain Event should satisfy the following:

- Represents a completed business fact.
- Is published only by the owning domain.
- Is immutable.
- Uses past-tense naming.
- Contains a stable schema.
- Includes sufficient identifiers.
- Is safe for duplicate delivery.
- Preserves domain boundaries.
- Does not expose infrastructure concerns.