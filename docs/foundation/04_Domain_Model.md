# 02.1_Domain_Model.md

# Domain Model

**Version:** 1.0  
**Status:** Approved  
**Document ID:** DOC-004

---

# 1. Purpose

This document defines the business domain model of the platform.

The domain model represents business concepts rather than database tables or API contracts.

Every feature, business rule, database schema, API endpoint, and service implementation must map back to this domain model.

This document is the single source of truth for business entities and their relationships.

---

# 2. Domain Overview

The platform consists of six primary business domains:

- Identity
- Marketplace
- Commerce
- Communication
- Platform
- Artificial Intelligence

Each domain owns its business entities and business logic.

---

# 3. Identity Domain

Responsible for user identity and access.

## User

Represents a registered platform user.

Responsibilities:

- authentication
- authorization
- account lifecycle
- security

A User may:

- own listings
- buy items
- sell items
- send offers
- receive offers
- participate in conversations
- receive notifications

---

## Profile

Represents the public identity of a user.

Contains:

- display information
- biography
- avatar
- reputation
- verification status
- statistics

Every User owns exactly one Profile.

---

## Session

Represents an authenticated login session.

Contains:

- device
- authentication token
- expiration
- location metadata

A User may own multiple Sessions.

---

# 4. Marketplace Domain

Responsible for everything related to selling products.

## Listing

The central entity of the marketplace.

Represents exactly one physical fashion item.

A Listing owns:

- photos
- pricing
- attributes
- publication status
- AI analysis
- analytics

A Listing belongs to exactly one seller.

---

## ListingImage

Represents a single uploaded image.

Contains:

- original image
- processed image
- thumbnails
- AI metadata

A Listing owns multiple ListingImages.

---

## ListingAttributes

Structured product information.

Examples:

- brand
- category
- size
- material
- color
- condition

Attributes exist independently from textual descriptions.

---

## ListingAnalytics

Aggregated listing metrics.

Contains:

- views
- favorites
- shares
- offer count
- conversion metrics

Analytics never affect marketplace behavior directly.

---

# 5. Commerce Domain

Responsible for transactions.

## Offer

Represents a negotiation proposal.

Contains:

- proposed price
- expiration
- sender
- recipient
- status

Offers belong to exactly one Listing.

---

## Order

Represents a completed purchase agreement.

Contains:

- buyer
- seller
- listing
- payment
- shipment
- order lifecycle

Each Order references exactly one Listing.

---

## Payment

Represents financial processing.

Contains:

- payment status
- transaction reference
- fees
- refund information

One Order owns one Payment.

---

## Shipment

Represents physical delivery.

Contains:

- carrier
- tracking
- shipment status
- delivery confirmation

One Order owns one Shipment.

---

## Review

Represents transaction feedback.

Contains:

- rating
- comment
- review author
- review recipient

A Review always references one completed Order.

---

# 6. Communication Domain

Responsible for user interaction.

## Conversation

Represents a communication channel.

Contains:

- participants
- messages
- unread counters

A Conversation may reference a Listing.

---

## Message

Represents one communication event.

Contains:

- sender
- content
- attachments
- timestamps

Messages belong to one Conversation.

---

## Notification

Represents information delivered to users.

Notification channels include:

- in-app
- email
- push

Notifications never contain business logic.

They communicate business events.

---

# 7. Platform Domain

Responsible for platform administration.

## ModerationCase

Represents an investigation.

Contains:

- reported object
- reporter
- moderator
- evidence
- decision

---

## Report

Represents a user complaint.

May reference:

- Listing
- User
- Message

---

## AuditLog

Immutable platform history.

Stores:

- actor
- action
- timestamp
- affected entity
- previous values
- new values

AuditLog is append-only.

---

## FeatureFlag

Represents runtime feature configuration.

Allows:

- gradual rollout
- A/B testing
- emergency disabling

---

## Configuration

Represents configurable business settings.

Examples:

- supported countries
- shipping providers
- payment providers
- AI providers

---

# 8. AI Domain

Responsible for intelligent automation.

## AIJob

Represents one AI processing task.

Examples:

- image recognition
- translation
- moderation
- pricing

AIJobs are asynchronous.

---

## AIAnalysis

Stores AI-generated results.

May include:

- detected brand
- detected category
- confidence
- recommendations

AIAnalysis never replaces original user data.

---

## Recommendation

Represents personalized recommendations.

Generated from:

- browsing history
- purchases
- favorites
- AI models

Recommendations are temporary.

They should not become permanent business records.

---

# 9. Aggregate Roots

Aggregate roots define transactional boundaries.

Current aggregate roots:

- User
- Listing
- Order
- Conversation
- ModerationCase
- Configuration

All child entities must be modified through their aggregate root.

---

# 10. Ownership Model

User

owns

- Profile
- Listings
- Sessions

Listing

owns

- Images
- Attributes
- Analytics

Order

owns

- Payment
- Shipment

Conversation

owns

- Messages

ModerationCase

owns

- Evidence
- Decisions

---

# 11. Cross-Domain Relationships

User

↓

creates

↓

Listing

↓

receives

↓

Offer

↓

becomes

↓

Order

↓

creates

↓

Payment

↓

creates

↓

Shipment

↓

creates

↓

Review

Communication operates independently:

Conversation

↓

Message

Platform supervision:

Report

↓

ModerationCase

↓

Decision

AI interacts with every domain but owns no business entities outside the AI domain.

---

# 12. Entity Lifecycle

Every entity should define its lifecycle.

Minimum lifecycle states:

Created

↓

Active

↓

Completed

↓

Archived

↓

Soft Deleted

Not every entity requires every state, but lifecycle behavior must always be explicitly defined.

---

# 13. Domain Ownership Rules

Each business capability must belong to exactly one domain.

Business logic must never be duplicated across domains.

Cross-domain communication should occur through well-defined interfaces or domain events.

---

# 14. Entity Design Rules

Every entity should:

- have a stable identifier;
- encapsulate its own business invariants;
- expose behavior rather than public mutable state;
- maintain audit information;
- support optimistic concurrency where appropriate.

Entities should not contain infrastructure concerns.

---

# 15. Future Extensibility

New domains may be added without modifying existing domain responsibilities.

Examples:

- Subscription Domain
- Advertising Domain
- Loyalty Domain
- Warehouse Domain
- Enterprise Seller Domain

Existing domains should evolve through extension rather than redesign.

The domain model should remain stable over the lifetime of the platform.