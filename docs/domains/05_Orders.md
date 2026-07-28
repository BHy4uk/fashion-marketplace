# Orders Domain Specification

**Version:** 1.0
**Status:** Approved
**Document ID:** DOMAIN-005

---

# 1. Purpose

The Orders domain manages completed purchase agreements between buyers and sellers.

An Order represents the contractual agreement resulting from an accepted purchase, regardless of payment or shipping status.

Orders are immutable business records that preserve the complete transaction history.

---

# 2. Responsibilities

The Orders domain owns:

- Order creation
- Order lifecycle
- Order state transitions
- Buyer/Seller agreement
- Order cancellation rules
- Order history
- Order totals

The Orders domain does not own:

- Listings
- Offers
- Payment execution
- Shipping execution
- Reviews
- Messaging

---

# 3. Aggregate Root

Aggregate Root

- Order

Child Entities

- OrderItem
- OrderStatusHistory

Value Objects

- OrderId
- Money
- OrderNumber
- OrderStatus

---

# 4. Order Responsibilities

An Order represents one completed purchase agreement.

Each Order references exactly:

- one Buyer;
- one Seller;
- one Listing (Version 1);
- one accepted Offer (if applicable).

Future versions may support multiple OrderItems.

---

# 5. Invariants

### INV-001

Every Order belongs to exactly one Buyer.

---

### INV-002

Every Order belongs to exactly one Seller.

---

### INV-003

Every Order references exactly one Listing.

---

### INV-004

Order identifiers never change.

---

### INV-005

Order monetary values are immutable after creation.

---

### INV-006

An Order can never return to a previous lifecycle state.

---

### INV-007

Deleting Orders is prohibited.

---

### INV-008

Every Order maintains a complete state history.

---

### INV-009

An Order always has exactly one current status.

---

# 6. Order Lifecycle

```
Created

↓

AwaitingPayment

↓

Paid

↓

PreparingShipment

↓

Shipped

↓

Delivered

↓

Completed
```

Alternative terminal states:

```
Canceled

Refunded

Closed
```

State transitions are strictly validated.

---

# 7. Order Creation

An Order may be created only when:

- the Listing is available;
- the Buyer is active;
- the Seller is active;
- the purchase has been authorized by business rules;
- no existing active Order references the same Listing.

Order creation is atomic.

---

# 8. Order State Transitions

Allowed transitions include:

- Created → AwaitingPayment
- AwaitingPayment → Paid
- Paid → PreparingShipment
- PreparingShipment → Shipped
- Shipped → Delivered
- Delivered → Completed

Exceptional transitions:

- AwaitingPayment → Canceled
- Paid → Refunded
- Delivered → Closed (administrative)

Transitions outside the state machine are prohibited.

---

# 9. Listing Interaction

Order creation affects the Listing lifecycle.

When an Order is created:

- the Listing becomes unavailable for new purchases;
- new Offers cannot be accepted;
- search visibility is updated according to business rules.

The Listing remains part of the Order history even if later archived.

---

# 10. Buyer Responsibilities

The Buyer may:

- view Orders;
- complete payment;
- track shipment;
- confirm delivery;
- request support where applicable.

The Buyer may not modify Order data.

---

# 11. Seller Responsibilities

The Seller may:

- prepare shipment;
- provide shipment details;
- monitor Order progress.

The Seller may not modify completed financial records.

---

# 12. Cancellation Rules

Cancellation is permitted only in allowed lifecycle states.

Cancellation policies are defined by business rules.

Cancellation never deletes the Order.

Cancellation is recorded permanently.

---

# 13. Financial Information

The Order stores:

- agreed purchase price;
- currency;
- platform fees (if applicable);
- totals.

Payment processing belongs to the Payments domain.

---

# 14. Shipping Integration

Shipping information is referenced through the Shipment entity.

The Orders domain tracks shipment status but does not manage carrier integrations.

---

# 15. Permissions

Buyer

May:

- view own Orders;
- confirm receipt where applicable.

Seller

May:

- manage fulfillment;
- update shipment progress through the Shipping domain.

Moderator

Read access for dispute resolution.

Administrator

Full administrative access.

---

# 16. Domain Events

Examples:

- OrderCreated
- OrderCanceled
- OrderPaid
- OrderPrepared
- OrderShipped
- OrderDelivered
- OrderCompleted
- OrderRefunded
- OrderClosed

Events represent completed business facts.

---

# 17. Validation

API

- identifiers;
- request format.

Application

- Buyer ownership;
- Seller ownership;
- Listing availability.

Domain

- lifecycle transitions;
- financial invariants;
- cancellation rules.

---

# 18. Error Scenarios

Examples:

- OrderNotFound
- InvalidOrderState
- ListingAlreadySold
- PaymentRequired
- ShipmentNotReady
- OrderAlreadyCompleted
- CancellationNotAllowed
- UnauthorizedAccess

Errors must be deterministic.

---

# 19. Background Jobs

Background processing includes:

- automatic Order expiration;
- payment timeout handling;
- delivery reminders;
- completion reminders;
- analytics aggregation.

---

# 20. Audit Requirements

The following actions are audited:

- Order creation;
- status changes;
- cancellation;
- refunds;
- administrative actions.

Audit history is immutable.

---

# 21. Concurrency Requirements

Concurrent Order creation for the same Listing is prohibited.

The platform must guarantee that:

- only one active Order may exist for a Listing;
- duplicate purchases cannot occur;
- concurrent requests are resolved atomically.

---

# 22. Security Requirements

Order data is visible only to authorized participants and platform administrators.

Sensitive financial information must never be exposed unnecessarily.

All ownership checks are enforced server-side.

---

# 23. Non-Goals

The Orders domain does not implement:

- payment gateway integrations;
- shipment provider integrations;
- recommendation logic;
- AI pricing;
- review management.

---

# 24. Extension Points

Future enhancements include:

- multi-item Orders;
- bundle purchases;
- split shipments;
- partial fulfillment;
- international tax calculation;
- gift Orders;
- business invoices.

Extensions must preserve Order immutability.

---

# 25. Acceptance Criteria

The Orders domain is complete when:

- Orders are immutable business records;
- lifecycle transitions are enforced;
- only one active Order exists per Listing;
- Listing availability is updated correctly;
- all state changes are audited;
- domain events are emitted correctly;
- concurrent purchase attempts are prevented;
- automated tests validate all lifecycle transitions and failure scenarios.