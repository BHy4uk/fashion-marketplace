# Messaging Domain Specification

**Version:** 1.0
**Status:** Approved
**Document ID:** DOMAIN-009

---

# 1. Purpose

The Messaging domain enables structured communication between marketplace participants.

All conversations are contextual and exist only in relation to a business object such as a Listing, Offer, Order, or future Support Case.

The Messaging domain provides secure, auditable, and asynchronous communication while remaining independent of business workflows.

---

# 2. Responsibilities

The Messaging domain owns:

- Conversations
- Messages
- Conversation participants
- Read status
- Attachments
- Conversation lifecycle
- Message visibility
- Conversation archiving

The Messaging domain does not own:

- Listings
- Offers
- Orders
- Notifications
- Moderation decisions
- User Profiles

---

# 3. Aggregate Root

Aggregate Root

- Conversation

Child Entities

- Message
- ConversationParticipant
- MessageAttachment
- ReadReceipt

Value Objects

- ConversationId
- MessageId
- AttachmentId

---

# 4. Conversation Responsibilities

A Conversation represents the communication context between participants.

A Conversation owns:

- participants;
- messages;
- read state;
- archive state;
- reference to the originating business object.

A Conversation may reference exactly one:

- Listing
- Offer
- Order
- Support Case (future)

---

# 5. Message Responsibilities

A Message represents one immutable communication event.

Each Message contains:

- author;
- content;
- creation timestamp;
- optional attachments.

Messages never own business logic.

---

# 6. Invariants

### INV-001

Every Message belongs to exactly one Conversation.

---

### INV-002

Every Conversation contains at least two participants.

---

### INV-003

Only Conversation participants may send Messages.

---

### INV-004

Messages are immutable after publication.

---

### INV-005

Deleting Messages is prohibited.

---

### INV-006

Conversation identifiers never change.

---

### INV-007

Every Message has exactly one author.

---

### INV-008

Conversation participants are unique.

---

### INV-009

Every Conversation references one business context.

---

# 7. Conversation Lifecycle

```
Created

↓

Active

↓

Archived

↓

Closed
```

Closed Conversations become read-only.

---

# 8. Message Lifecycle

```
Draft

↓

Sent

↓

Delivered

↓

Read
```

Alternative state:

```
Hidden
```

Messages never return to previous states.

---

# 9. Conversation Creation

A Conversation may be created only when:

- a valid business context exists;
- participants are authorized;
- duplicate active Conversation does not already exist for the same context and participants.

The platform should reuse existing Conversations whenever appropriate.

---

# 10. Attachments

Messages may include attachments.

Supported Version 1 types:

- Images

Future support:

- PDF
- Video
- Voice
- Documents

Attachments are immutable.

Virus scanning and content validation occur asynchronously.

---

# 11. Read Status

Read status is maintained per participant.

Read receipts contain:

- participant;
- timestamp.

Read status never modifies Message content.

---

# 12. Visibility

Messages may be:

- Visible
- Hidden by Moderation

Hidden Messages remain available for audit purposes.

---

# 13. Permissions

Participant

May:

- send Messages;
- read Messages;
- upload attachments;
- archive own Conversations.

Moderator

May:

- inspect Conversations;
- hide Messages according to moderation policy.

Administrator

Full administrative access.

---

# 14. Domain Events

Examples:

- ConversationCreated
- MessageSent
- MessageDelivered
- MessageRead
- AttachmentUploaded
- ConversationArchived
- ConversationClosed
- MessageHidden

Events represent completed communication facts.

---

# 15. Validation

API

- message length;
- attachment size;
- attachment type.

Application

- participant authorization;
- conversation existence;
- upload limits.

Domain

- lifecycle transitions;
- participant invariants;
- conversation uniqueness.

---

# 16. Error Scenarios

Examples:

- ConversationNotFound
- ParticipantNotAuthorized
- ConversationClosed
- InvalidAttachment
- AttachmentTooLarge
- DuplicateConversation
- MessageHidden
- UnsupportedMediaType

Errors must be deterministic.

---

# 17. Background Jobs

Background processing includes:

- attachment optimization;
- virus scanning;
- media thumbnail generation;
- attachment cleanup;
- read receipt aggregation.

---

# 18. Audit Requirements

The following actions are audited:

- conversation creation;
- message publication;
- moderation actions;
- attachment uploads;
- conversation closure.

Message history is immutable.

---

# 19. Concurrency Requirements

Simultaneous Messages from multiple participants must preserve chronological ordering.

Duplicate message submission must be prevented.

Read status updates must be idempotent.

---

# 20. Security Requirements

Only authorized participants may access Conversations.

Attachment downloads require authorization.

Sensitive metadata must not be exposed.

Message identifiers must not reveal business information.

---

# 21. Compliance Requirements

Message retention must comply with applicable legal and privacy requirements.

Content removal through moderation must preserve auditability where legally permitted.

---

# 22. Non-Goals

The Messaging domain does not implement:

- push notifications;
- email delivery;
- recommendation systems;
- social networking;
- public chat rooms;
- live streaming.

---

# 23. Extension Points

Future enhancements include:

- typing indicators;
- reactions;
- message editing window;
- message quoting;
- voice messages;
- video attachments;
- end-to-end encryption;
- support conversations;
- AI translation.

Extensions must preserve message immutability and conversation integrity.

---

# 24. Acceptance Criteria

The Messaging domain is complete when:

- every Conversation has a valid business context;
- Messages are immutable;
- participant authorization is enforced;
- duplicate Conversations are prevented;
- attachments are processed asynchronously;
- read status is tracked independently;
- domain events are emitted correctly;
- automated tests validate lifecycle transitions, permissions, attachments, and concurrent messaging scenarios.