# Reviews Domain Specification

**Version:** 1.0
**Status:** Approved
**Document ID:** DOMAIN-008

---

# 1. Purpose

The Reviews domain manages post-transaction feedback between marketplace participants.

Reviews provide trust signals by allowing Buyers and Sellers to evaluate each other after a completed Order.

Every Review is tied to a completed transaction.

---

# 2. Responsibilities

The Reviews domain owns:

- Review creation
- Review lifecycle
- Ratings
- Written feedback
- Reputation calculation inputs
- Review visibility
- Review moderation state

The Reviews domain does not own:

- Orders
- Listings
- Payments
- Messaging
- User Profiles

---

# 3. Aggregate Root

Aggregate Root

- Review

Child Entities

- ReviewResponse

Value Objects

- ReviewId
- Rating
- ReviewComment

---

# 4. Review Responsibilities

A Review represents feedback created after one completed Order.

Each Review references:

- one Order;
- one Author;
- one Recipient.

Reviews become part of the Recipient's reputation.

---

# 5. Invariants

### INV-001

Every Review references exactly one completed Order.

---

### INV-002

A Review has exactly one Author.

---

### INV-003

A Review has exactly one Recipient.

---

### INV-004

The Author and Recipient must be participants of the referenced Order.

---

### INV-005

A participant may submit at most one Review for the same Recipient per Order.

---

### INV-006

Published Reviews cannot be edited.

---

### INV-007

Deleted Reviews remain in audit history.

---

### INV-008

Every Review has exactly one current status.

---

# 6. Review Lifecycle

```
Draft

↓

Published
```

Alternative states:

```
Hidden

Removed
```

Reviews never return to Draft after publication.

---

# 7. Review Creation

A Review may be created only when:

- the referenced Order is Completed;
- the Author participated in the Order;
- the Recipient participated in the Order;
- no previous Review exists from the same Author to the same Recipient for that Order.

---

# 8. Ratings

Version 1 supports:

- Overall Rating (1–5)

Future versions may include:

- Communication
- Shipping Speed
- Item Accuracy
- Packaging

Rating scales are configurable.

---

# 9. Written Feedback

Reviews may include an optional written comment.

Comments:

- are immutable after publication;
- may be moderated;
- remain attached to the Review.

---

# 10. Seller Responses

Recipients may publish one response.

Responses:

- reference one Review;
- are immutable after publication;
- do not modify the original Review.

---

# 11. Reputation

The Reviews domain provides reputation inputs.

It does not calculate platform-wide reputation scores.

Reputation aggregation belongs to the Identity or Analytics domain.

---

# 12. Visibility

Possible visibility states:

- Public
- Hidden
- Removed

Hidden and Removed Reviews remain available for audit purposes.

---

# 13. Permissions

Buyer

May:

- review Sellers after completed Orders.

Seller

May:

- review Buyers after completed Orders;
- respond to Reviews.

Moderator

May:

- hide Reviews;
- remove Reviews according to moderation policies.

Administrator

Full administrative access.

---

# 14. Domain Events

Examples:

- ReviewCreated
- ReviewPublished
- ReviewHidden
- ReviewRemoved
- ReviewResponseCreated

Events represent completed business facts.

---

# 15. Validation

API

- rating range;
- comment length.

Application

- completed Order;
- review eligibility;
- duplicate review detection.

Domain

- lifecycle transitions;
- review invariants.

---

# 16. Error Scenarios

Examples:

- ReviewNotFound
- OrderNotCompleted
- DuplicateReview
- InvalidRating
- ReviewAlreadyPublished
- ReviewRemoved
- UnauthorizedReviewer

---

# 17. Background Jobs

Background processing includes:

- reputation aggregation;
- review indexing;
- spam detection;
- moderation assistance.

---

# 18. Audit Requirements

The following actions are audited:

- review publication;
- moderation actions;
- review responses;
- administrative removals.

Review history is immutable.

---

# 19. Concurrency Requirements

Concurrent Review creation for the same Author, Recipient, and Order must result in exactly one successful Review.

Duplicate submissions must fail deterministically.

---

# 20. Security Requirements

Only eligible participants may create Reviews.

Moderation actions require appropriate authorization.

Ownership validation is enforced server-side.

---

# 21. Compliance Requirements

Review retention and moderation must comply with applicable consumer protection and privacy regulations.

Personally identifiable information should not be exposed unnecessarily.

---

# 22. Non-Goals

The Reviews domain does not implement:

- reputation scoring algorithms;
- recommendation systems;
- fraud detection models;
- messaging;
- dispute resolution.

---

# 23. Extension Points

Future enhancements include:

- media attachments;
- verified authenticity badges;
- review editing window;
- AI-generated review summaries;
- multilingual translation;
- review voting;
- review reporting.

Extensions must preserve review authenticity and transaction linkage.

---

# 24. Acceptance Criteria

The Reviews domain is complete when:

- every Review references a completed Order;
- duplicate Reviews are prevented;
- publication is immutable;
- moderation preserves audit history;
- domain events are emitted correctly;
- review responses remain independent of original Reviews;
- automated tests validate lifecycle, permissions, moderation, and duplicate prevention.