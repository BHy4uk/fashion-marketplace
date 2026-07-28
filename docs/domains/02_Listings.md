# Listings Domain Specification

**Version:** 1.0
**Status:** Approved
**Document ID:** DOMAIN-002

---

# 1. Purpose

The Listings domain is responsible for representing fashion items offered for sale on the marketplace.

It owns the complete lifecycle of every listing, including creation, enrichment, publication, visibility, availability, archival, and removal.

The Listing is the central business entity of the marketplace.

Nearly every other domain interacts with Listings but does not own them.

---

# 2. Responsibilities

The Listings domain owns:

- Listing creation
- Listing editing
- Publication
- Draft management
- Visibility
- Listing lifecycle
- Images
- Structured attributes
- Pricing
- Availability
- AI enrichment
- Listing analytics

The Listings domain does not own:

- Orders
- Payments
- Shipping
- Reviews
- Messaging
- Notifications
- Search indexing implementation

---

# 3. Aggregate Root

Aggregate Root

- Listing

Child Entities

- ListingImage
- ListingAttribute
- ListingPrice
- ListingCondition
- ListingAnalytics
- ListingAIAnalysis

Value Objects

- ListingId
- Money
- Brand
- Category
- Size
- Color
- Material
- Condition
- Slug

---

# 4. Listing Responsibilities

A Listing represents exactly one physical fashion item.

A Listing owns:

- seller
- photos
- structured metadata
- textual description
- publication state
- pricing
- availability
- analytics

A Listing never owns:

- offers
- orders
- payments

Those belong to other domains.

---

# 5. Invariants

### INV-001

A Listing always belongs to exactly one seller.

---

### INV-002

A Listing represents exactly one physical item.

---

### INV-003

Only one published version of a Listing may exist.

---

### INV-004

A sold Listing can never become Published again.

---

### INV-005

Every published Listing contains all mandatory information.

---

### INV-006

A Listing always has exactly one current price.

---

### INV-007

A Listing always has one lifecycle state.

---

### INV-008

Every image belongs to exactly one Listing.

---

### INV-009

Listing identifiers never change.

---

# 6. Listing Lifecycle

```

Draft

↓

Ready

↓

Published

↓

Reserved

↓

Sold

↓

Archived

↓

Soft Deleted

```

Transitions must always follow the defined state machine.

Skipping states is prohibited.

---

# 7. Publication Rules

A listing may be published only if:

- seller account is active;
- mandatory fields are completed;
- at least one valid image exists;
- category is selected;
- price is specified;
- condition is specified.

Publication automatically creates:

- publication timestamp;
- search indexing request;
- AI enrichment request;
- analytics initialization.

---

# 8. Editing Rules

The seller may edit:

- description
- images
- price
- attributes

The seller may not edit:

- seller identity
- listing identifier
- historical analytics

Certain edits may require search re-indexing.

---

# 9. Visibility

Possible visibility states:

- Public
- Hidden
- Moderation
- Archived

Visibility controls discoverability.

Visibility does not change ownership.

---

# 10. Images

Images belong exclusively to Listings.

Each image stores:

- original file
- optimized versions
- thumbnail
- metadata
- AI analysis

Images may be reordered.

Deleting an image never affects audit history.

---

# 11. Structured Attributes

Attributes are stored separately from free text.

Examples:

- Brand
- Category
- Gender
- Size
- Material
- Color
- Condition
- Style
- Season

Structured attributes are used for:

- filtering
- recommendations
- analytics
- AI

---

# 12. Pricing

Each Listing owns one active price.

Future capabilities:

- price history
- negotiated prices
- automatic recommendations

The Listings domain never processes payments.

---

# 13. Availability

Possible availability states:

- Available
- Reserved
- Sold

Only Available listings may receive new offers.

---

# 14. AI Integration

AI may assist with:

- title generation
- description generation
- category recognition
- brand recognition
- color recognition
- material detection
- condition estimation
- duplicate detection
- prohibited item detection

AI recommendations require seller confirmation.

---

# 15. Listing Analytics

Analytics are informational only.

Examples:

- Views
- Favorites
- Shares
- Offers
- Conversion rate

Analytics never affect ownership or business rules.

---

# 16. Permissions

Seller

May:

- create
- edit
- archive
- publish

May not:

- edit another seller's listings

Moderator

May:

- hide
- restore
- moderate

Administrator

Full permissions.

---

# 17. Domain Events

Examples:

- ListingCreated
- ListingUpdated
- ListingPublished
- ListingArchived
- ListingHidden
- ListingPriceChanged
- ListingReserved
- ListingSold
- ListingDeleted
- ListingImagesUpdated

Events describe completed business facts.

---

# 18. Validation

API

- Required fields
- Formats
- Image limits

Application

- Seller permissions
- Account state
- Moderation state

Domain

- Lifecycle transitions
- Invariants
- Publication rules

---

# 19. Error Scenarios

Examples:

- ListingNotFound
- InvalidStateTransition
- MissingMandatoryFields
- SellerSuspended
- DuplicateListing
- InvalidCategory
- InvalidPrice
- ImageUploadFailed

---

# 20. Background Jobs

Background processing includes:

- image optimization;
- thumbnail generation;
- AI analysis;
- search indexing;
- recommendation updates;
- analytics aggregation.

---

# 21. Audit Requirements

The following actions are audited:

- creation;
- publication;
- editing;
- archival;
- deletion;
- price changes;
- moderation actions.

Historical listing data must never be lost.

---

# 22. Non-Goals

The Listings domain does not implement:

- purchasing;
- messaging;
- negotiations;
- payments;
- shipment;
- reviews.

Those belong to separate domains.

---

# 23. Extension Points

Future enhancements:

- multi-item bundles;
- video support;
- 360° images;
- authenticity certificates;
- AI-generated measurements;
- automatic repricing;
- digital wardrobe import;
- seller inventory synchronization.

---

# 24. Acceptance Criteria

The Listings domain is complete when:

- lifecycle is enforced;
- invariants are enforced;
- publication rules are validated;
- permissions are enforced;
- AI integration is asynchronous;
- audit history is complete;
- all domain events are emitted;
- automated tests cover every lifecycle transition.