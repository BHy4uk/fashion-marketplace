# 02_Business_Rules.md

# Business Rules

**Version:** 1.0  
**Status:** Approved  
**Document ID:** DOC-003

---

# 1. Purpose

This document defines the global business rules governing the behavior of the platform.

Business rules describe **what the system is allowed to do**, **what it must do**, and **what it must never do**.

All functional modules, APIs, database operations, background jobs, and user interfaces must comply with these rules.

If implementation conflicts with a business rule, the implementation is incorrect.

---

# 2. Rule Format

Each business rule has a unique identifier.

Format:

BR-001

BR-002

...

Business rule identifiers are immutable.

Deleted rules must never be reused.

---

# 3. User Rules

### BR-001

A user may own only one personal account.

Duplicate personal accounts are prohibited.

---

### BR-002

A user may simultaneously act as both buyer and seller.

Roles are determined by performed actions, not by separate account types.

---

### BR-003

A suspended user may not:

- publish listings;
- edit listings;
- purchase items;
- send offers;
- send messages.

---

### BR-004

Deleting a user account must never silently delete business history.

Historical transactions must remain preserved.

---

### BR-005

User reputation must never be manually modified except by authorized administrators with an auditable reason.

---

# 4. Listing Rules

### BR-010

Only authenticated users may create listings.

---

### BR-011

Only the listing owner may edit a listing.

Exceptions:

- moderators;
- administrators.

---

### BR-012

Published listings must contain all mandatory information.

Incomplete listings cannot be published.

---

### BR-013

A listing may have only one active published version.

---

### BR-014

A sold listing cannot return to Published status.

---

### BR-015

Archived listings remain available for analytics and historical records.

---

### BR-016

Deleted listings are never physically removed from the database.

Soft deletion must be used.

---

### BR-017

Listings participating in active orders cannot be deleted.

---

### BR-018

One listing represents exactly one physical item.

Selling multiple quantities through a single listing is not supported.

---

# 5. Search Rules

### BR-020

Only publicly available listings appear in search results.

---

### BR-021

Reserved listings may appear in search but must be clearly marked.

---

### BR-022

Sold listings are excluded from default search results.

---

### BR-023

Search ranking must not depend on paid promotion in Version 1.

---

### BR-024

Search results should prioritize relevance over publication date.

---

# 6. Offer Rules

### BR-030

Offers may only be created for published listings.

---

### BR-031

A seller may accept only one offer.

Acceptance automatically invalidates all remaining active offers.

---

### BR-032

Expired offers cannot be accepted.

---

### BR-033

Accepted offers become binding until cancelled according to platform rules.

---

### BR-034

Offer history is immutable.

---

# 7. Order Rules

### BR-040

Each order references exactly one listing.

---

### BR-041

An order must always have one buyer and one seller.

---

### BR-042

An order cannot exist without successful payment authorization.

---

### BR-043

Order status changes must follow the approved state machine.

Status transitions may never skip mandatory intermediate states.

---

### BR-044

Completed orders are immutable.

---

### BR-045

Cancelled orders remain visible in history.

---

### BR-046

Every order must maintain a complete audit trail.

---

# 8. Payment Rules

### BR-050

Platform fees must be calculated before payment confirmation.

---

### BR-051

Seller payouts must never occur before payment settlement.

---

### BR-052

Refunds must always reference an existing transaction.

---

### BR-053

Payment operations must be idempotent.

Repeated requests must never create duplicate transactions.

---

### BR-054

Financial records must never be physically deleted.

---

# 9. Shipping Rules

### BR-060

Shipment cannot begin before payment confirmation.

---

### BR-061

Tracking information becomes immutable once generated, except by authorized integrations.

---

### BR-062

Delivery confirmation changes the order state but does not automatically release funds if additional verification is required.

---

# 10. Review Rules

### BR-070

Reviews may only be created after a completed order.

---

### BR-071

Reviews must always reference an order.

---

### BR-072

Users cannot review themselves.

---

### BR-073

Reviews are immutable after publication except through moderation.

---

# 11. Messaging Rules

### BR-080

Messages may only be exchanged between authenticated users.

---

### BR-081

System messages cannot be deleted by users.

---

### BR-082

Message history participating in disputes must be preserved.

---

# 12. Moderation Rules

### BR-090

Moderation actions require authenticated moderator identity.

---

### BR-091

Every moderation action must generate an audit log.

---

### BR-092

Moderators may hide listings but cannot permanently delete historical business records.

---

### BR-093

Administrative overrides must remain traceable.

---

# 13. AI Rules

### BR-100

AI recommendations are advisory.

Users remain responsible for final decisions.

---

### BR-101

AI-generated content must always be editable before publication.

---

### BR-102

AI confidence scores must never be presented as guarantees.

---

### BR-103

AI must never automatically publish listings.

---

### BR-104

AI may assist moderation but cannot permanently suspend users without human approval.

---

# 14. Security Rules

### BR-110

Every sensitive operation requires authorization.

---

### BR-111

Permission checks must occur on the server.

Frontend validation is never sufficient.

---

### BR-112

Users may access only resources they own unless explicitly granted broader permissions.

---

### BR-113

All security-related events must be logged.

---

# 15. Data Rules

### BR-120

Business records are append-only whenever practical.

---

### BR-121

Historical business data must be preserved.

---

### BR-122

Timestamps are immutable after creation unless explicitly defined otherwise.

---

### BR-123

Every entity must support audit information.

Minimum audit fields:

- CreatedAt
- CreatedBy
- UpdatedAt
- UpdatedBy

---

# 16. Platform Rules

### BR-130

Every business operation must be deterministic.

The same input under the same conditions must produce the same business result.

---

### BR-131

Business logic must exist only in the backend.

---

### BR-132

No business rule may exist exclusively in the frontend.

---

### BR-133

Business rules must not depend on UI implementation.

---

### BR-134

Business rules must not depend on a specific API protocol.

---

### BR-135

External integrations must not bypass business rules.

---

# 17. Rule Lifecycle

Every new business rule must include:

- unique identifier;
- description;
- affected domains;
- rationale;
- version introduced.

Rules should never be silently modified.

Breaking changes require a new document version.

---

# 18. Rule Priority

If multiple business rules conflict, priority is determined as follows:

1. Security
2. Financial correctness
3. Legal compliance
4. Data integrity
5. Business consistency
6. User experience
7. Performance

Lower-priority rules must never violate higher-priority rules.

---

# 19. Compliance

Every implementation must be traceable back to one or more business rules.

Every automated test validating business behavior should reference the corresponding Business Rule ID.

Business rules are the authoritative source of platform behavior.