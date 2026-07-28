# Payments Domain Specification

**Version:** 1.0
**Status:** Approved
**Document ID:** DOMAIN-006

---

# 1. Purpose

The Payments domain is responsible for processing financial transactions associated with Orders.

It manages payment authorization, capture, settlement, refunds, reconciliation, and communication with external payment providers.

The Payments domain never creates or owns Orders.

---

# 2. Responsibilities

The Payments domain owns:

- Payment creation
- Payment authorization
- Payment capture
- Refund processing
- Payment status
- Provider integration
- Payment reconciliation
- Financial transaction history

The Payments domain does not own:

- Orders
- Listings
- Offers
- Shipping
- Reviews

---

# 3. Aggregate Root

Aggregate Root

- Payment

Child Entities

- PaymentTransaction
- Refund
- PaymentAttempt

Value Objects

- PaymentId
- Money
- Currency
- ProviderReference
- TransactionReference

---

# 4. Payment Responsibilities

A Payment represents the execution of a financial obligation for one Order.

Each Payment references exactly one Order.

A Payment records all financial activity related to that Order.

---

# 5. Invariants

### INV-001

Every Payment references exactly one Order.

---

### INV-002

Payment identifiers never change.

---

### INV-003

Every provider transaction is unique.

---

### INV-004

Captured payments cannot become authorized again.

---

### INV-005

Refunded amounts cannot exceed captured amounts.

---

### INV-006

Payment history is immutable.

---

### INV-007

External provider references are immutable.

---

### INV-008

Every Payment has exactly one current status.

---

# 6. Payment Lifecycle

```
Created

↓

PendingAuthorization

↓

Authorized

↓

Captured

↓

Settled
```

Alternative states:

```
Failed

Canceled

Refunded

PartiallyRefunded
```

All transitions must follow the defined state machine.

---

# 7. Payment Creation

A Payment may be created only when:

- an Order exists;
- the Order requires payment;
- no active Payment already exists for the same obligation.

Payment creation never creates an Order.

---

# 8. Authorization

Authorization verifies that funds are available.

Authorization does not complete the transaction.

Authorization may expire according to provider rules.

---

# 9. Capture

Capture transfers authorized funds.

Capture completes the financial obligation.

Capture must be idempotent.

---

# 10. Settlement

Settlement confirms that funds have been successfully transferred.

Settlement may occur asynchronously.

Settlement information originates from the payment provider.

---

# 11. Refunds

Refunds may be:

- Full
- Partial

Refunds:

- always reference the original Payment;
- are immutable;
- never modify historical transactions.

---

# 12. Payment Attempts

Multiple payment attempts may exist.

Each attempt stores:

- provider;
- timestamp;
- outcome;
- failure reason.

Attempts are retained permanently.

---

# 13. External Providers

Supported providers are interchangeable.

Examples:

- Stripe
- Adyen
- PayPal
- Apple Pay
- Google Pay

Provider-specific logic belongs exclusively to infrastructure adapters.

---

# 14. Order Interaction

The Payments domain informs the Orders domain through domain events.

Payment never changes Order state directly.

The Orders domain decides how payment events affect the Order lifecycle.

---

# 15. Permissions

Buyer

May:

- initiate payment;
- view payment history for own Orders.

Seller

May:

- view payment status for completed sales.

Administrator

May:

- inspect payment history;
- investigate failed transactions.

Financial operations remain provider-controlled.

---

# 16. Domain Events

Examples:

- PaymentCreated
- PaymentAuthorized
- PaymentCaptured
- PaymentSettled
- PaymentFailed
- PaymentRefunded
- PartialRefundIssued
- PaymentCanceled

Events represent completed financial facts.

---

# 17. Validation

API

- payment request format;
- supported currencies;
- provider selection.

Application

- Order existence;
- ownership validation;
- payment eligibility.

Domain

- lifecycle transitions;
- refund limits;
- payment invariants.

---

# 18. Error Scenarios

Examples:

- PaymentNotFound
- AuthorizationFailed
- CaptureFailed
- ProviderUnavailable
- PaymentExpired
- DuplicateCapture
- RefundLimitExceeded
- CurrencyMismatch

Errors must be deterministic.

---

# 19. Background Jobs

Background processing includes:

- settlement synchronization;
- provider reconciliation;
- expired authorization cleanup;
- payment retry scheduling;
- refund reconciliation.

---

# 20. Audit Requirements

The following actions are audited:

- payment creation;
- authorization;
- capture;
- settlement;
- refunds;
- provider callbacks;
- administrative investigations.

Financial audit history is immutable.

---

# 21. Concurrency Requirements

Payment execution must be idempotent.

Concurrent capture requests must result in:

- exactly one successful capture;
- deterministic failure for duplicates.

Duplicate provider callbacks must be safely ignored.

---

# 22. Security Requirements

Sensitive payment information is never stored unless required.

The platform must never store raw payment card data.

All provider communication must be authenticated and encrypted.

Webhook requests must be verified.

---

# 23. Compliance Requirements

The Payments domain must support compliance with applicable financial and payment regulations.

Examples include:

- PCI DSS
- PSD2 / Strong Customer Authentication (where applicable)
- GDPR and other applicable privacy regulations

Compliance requirements should be satisfied primarily through provider integrations rather than custom implementations where appropriate.

---

# 24. Non-Goals

The Payments domain does not implement:

- Order creation;
- shipment management;
- recommendation logic;
- marketplace search;
- AI services.

---

# 25. Extension Points

Future enhancements include:

- multi-provider routing;
- split payments;
- escrow support;
- marketplace commissions;
- installment payments;
- store credit;
- gift cards;
- cryptocurrency providers.

Extensions must preserve financial auditability.

---

# 26. Acceptance Criteria

The Payments domain is complete when:

- payment lifecycle is enforced;
- capture is idempotent;
- refunds respect financial invariants;
- provider integrations are interchangeable;
- payment history is immutable;
- domain events are emitted correctly;
- reconciliation is supported;
- automated tests cover successful, failed, refunded, duplicate, and concurrent payment scenarios.