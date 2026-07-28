# Offers Domain Specification

**Version:** 1.0
**Status:** Approved
**Document ID:** DOMAIN-004

---

# 1. Purpose

The Offers domain manages price negotiations between buyers and sellers.

It governs the lifecycle of offers, counter-offers, acceptance, rejection, expiration, and cancellation.

An accepted offer establishes the commercial agreement that may result in an Order.

The Offers domain never processes payments or shipping.

---

# 2. Responsibilities

The Offers domain owns:

- Offer creation
- Counter-offers
- Offer expiration
- Offer acceptance
- Offer rejection
- Offer cancellation
- Negotiation history
- Offer validation

The Offers domain does not own:

- Listings
- Orders
- Payments
- Shipping
- Messaging
- Reviews

---

# 3. Aggregate Root

Aggregate Root

- Offer

Child Entities

- OfferRevision
- OfferHistory

Value Objects

- OfferId
- Money
- ExpirationTime
- OfferStatus

---

# 4. Offer Responsibilities

An Offer represents a proposal to purchase one Listing at a specific price.

Each Offer references exactly:

- one Buyer;
- one Seller;
- one Listing.

Offers maintain a complete negotiation history.

---

# 5. Invariants

### INV-001

An Offer belongs to exactly one Listing.

---

### INV-002

An Offer belongs to exactly one Buyer.

---

### INV-003

An Offer belongs to exactly one Seller.

---

### INV-004

A Buyer cannot submit an offer on their own Listing.

---

### INV-005

Only one Offer may be accepted for a Listing.

---

### INV-006

Accepted Offers cannot be modified.

---

### INV-007

Expired Offers cannot be accepted.

---

### INV-008

Rejected Offers cannot become Active again.

---

### INV-009

Canceled Offers cannot become Active again.

---

### INV-010

Offers cannot exist for Sold Listings.

---

# 6. Offer Lifecycle

```
Draft

↓

Submitted

↓

Active

↓

Accepted

or

Rejected

or

Expired

or

Canceled
```

State transitions are strictly validated.

Skipping states is prohibited.

---

# 7. Counter-Offers

The seller may respond with a counter-offer.

A counter-offer:

- references the previous negotiation;
- proposes a new price;
- resets the expiration period;
- becomes the active negotiation.

Counter-offers preserve the complete negotiation history.

---

# 8. Offer Creation Rules

An offer may be created only if:

- Listing is Available;
- Buyer is active;
- Seller is active;
- Buyer is not the seller;
- Offer price is valid;
- Listing accepts offers.

Offer validation occurs before persistence.

---

# 9. Offer Acceptance

Accepting an offer:

- locks the negotiation;
- marks the Offer as Accepted;
- prevents other Offers from being accepted;
- initiates Order creation;
- generates notifications.

Acceptance is an atomic business operation.

---

# 10. Offer Rejection

A seller may reject an Offer.

Rejected Offers:

- remain visible in history;
- cannot be reactivated;
- may be followed by a new Offer.

---

# 11. Offer Cancellation

A Buyer may cancel an active Offer before acceptance.

Canceled Offers:

- remain in history;
- cannot be restored;
- do not affect Listing availability.

---

# 12. Offer Expiration

Offers expire automatically after the configured validity period.

Expired Offers:

- cannot be accepted;
- remain visible in history;
- may be replaced by new Offers.

Expiration is processed asynchronously.

---

# 13. Negotiation History

The complete negotiation history is immutable.

History includes:

- submitted offers;
- counter-offers;
- timestamps;
- participants;
- state changes.

Historical negotiations are never modified.

---

# 14. Listing Interaction

Offer actions affect Listing availability only after acceptance.

Creating an Offer never reserves a Listing.

Only acceptance may trigger reservation or Order creation, according to business rules.

---

# 15. Permissions

Buyer

May:

- create Offers;
- cancel own Offers;
- view own negotiation history.

Seller

May:

- accept Offers;
- reject Offers;
- submit counter-offers;
- view Offers for owned Listings.

Moderator

Read-only access where required for investigations.

Administrator

Full administrative access.

---

# 16. Domain Events

Examples:

- OfferCreated
- OfferSubmitted
- OfferAccepted
- OfferRejected
- OfferCanceled
- OfferExpired
- CounterOfferCreated

Events represent completed business facts.

---

# 17. Validation

API

- required fields;
- valid currency;
- positive price.

Application

- Listing ownership;
- account status;
- Listing availability.

Domain

- lifecycle transitions;
- negotiation rules;
- business invariants.

---

# 18. Error Scenarios

Examples:

- ListingNotAvailable
- CannotOfferOwnListing
- OfferAlreadyAccepted
- OfferExpired
- OfferCanceled
- InvalidOfferState
- SellerSuspended
- BuyerSuspended
- ListingSold

Business errors must be deterministic.

---

# 19. Background Jobs

Background processing includes:

- Offer expiration;
- notification delivery;
- stale negotiation cleanup;
- analytics aggregation.

---

# 20. Audit Requirements

The following actions are audited:

- Offer creation;
- counter-offers;
- acceptance;
- rejection;
- cancellation;
- expiration.

Negotiation history must be immutable.

---

# 21. Concurrency Requirements

The Offers domain must prevent race conditions.

Acceptance must be performed using optimistic concurrency or equivalent transactional protection.

If multiple acceptance attempts occur simultaneously:

- exactly one succeeds;
- all others fail deterministically.

---

# 22. Security Requirements

Only authorized participants may view Offer details.

Offer identifiers must not expose sequential business information.

All state transitions are validated server-side.

---

# 23. Non-Goals

The Offers domain does not implement:

- payment processing;
- shipment;
- messaging transport;
- review creation;
- recommendation logic.

---

# 24. Extension Points

Future enhancements include:

- automatic seller responses;
- AI-assisted price suggestions;
- offer templates;
- bundle offers;
- multi-item negotiations;
- seller auto-accept rules;
- buyer auto-counter strategies.

Extensions must preserve negotiation history and existing invariants.

---

# 25. Acceptance Criteria

The Offers domain is complete when:

- lifecycle transitions are enforced;
- only one Offer can be accepted for a Listing;
- counter-offers preserve negotiation history;
- acceptance is atomic;
- expiration is automatic;
- audit history is immutable;
- domain events are emitted correctly;
- concurrent acceptance scenarios are fully tested.