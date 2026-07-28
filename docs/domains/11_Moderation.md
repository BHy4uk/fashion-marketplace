# Moderation Domain Specification

**Version:** 1.0
**Status:** Approved
**Document ID:** DOMAIN-011

---

# 1. Purpose

The Moderation domain is responsible for maintaining marketplace integrity by investigating reported or automatically detected policy violations.

Moderation is centered around investigations rather than direct enforcement actions.

Every moderation decision is based on a Moderation Case.

---

# 2. Responsibilities

The Moderation domain owns:

- Moderation Cases
- Reports
- Evidence
- Investigation workflow
- Moderation decisions
- Case history
- Automated moderation signals

The Moderation domain does not own:

- Listings
- Users
- Messages
- Reviews
- Orders
- AI models

The Moderation domain references these entities but never owns them.

---

# 3. Aggregate Root

Aggregate Root

- ModerationCase

Child Entities

- Report
- Evidence
- ModerationDecision
- CaseComment

Value Objects

- CaseId
- ReportId
- EvidenceId
- DecisionId

---

# 4. Moderation Case Responsibilities

A Moderation Case represents an investigation into one or more potential policy violations.

Each Case owns:

- reports;
- evidence;
- investigation history;
- moderator decisions;
- referenced marketplace entities.

---

# 5. Report Responsibilities

A Report represents a submitted concern regarding marketplace behavior.

Reports may originate from:

- Buyers;
- Sellers;
- Moderators;
- Automated detection systems.

Reports never determine the outcome of a Case.

---

# 6. Evidence

Evidence may include:

- Listings
- Images
- Messages
- Reviews
- User profiles
- Audit records
- AI signals

Evidence is immutable once attached to a Case.

---

# 7. Invariants

### INV-001

Every Moderation Case has a unique identifier.

---

### INV-002

Every Report belongs to exactly one Moderation Case.

---

### INV-003

Evidence is immutable.

---

### INV-004

Moderation decisions are append-only.

---

### INV-005

Closed Cases cannot be modified.

---

### INV-006

Every Case has exactly one current lifecycle state.

---

### INV-007

Referenced marketplace entities remain external to the Case.

---

### INV-008

Moderation history is immutable.

---

# 8. Case Lifecycle

```
Created

↓

UnderReview

↓

Investigation

↓

DecisionMade

↓

Closed
```

Alternative lifecycle:

```
Dismissed
```

Closed Cases become read-only.

---

# 9. Case Creation

Cases may originate from:

- user reports;
- automated detection;
- moderator initiation;
- platform administration.

Multiple Reports may be merged into the same Case.

---

# 10. Investigation

Moderators may:

- collect evidence;
- review history;
- consult automated analysis;
- request additional review.

Investigations must remain fully auditable.

---

# 11. Decisions

Examples:

- No Action
- Warning
- Listing Hidden
- Listing Removed
- Message Hidden
- Review Hidden
- Temporary Suspension
- Permanent Suspension

Every decision records:

- timestamp;
- moderator;
- reason;
- referenced policies.

Decisions never overwrite previous decisions.

---

# 12. Automation

Automated systems may:

- flag suspicious activity;
- prioritize Cases;
- recommend actions.

Automated systems never make final moderation decisions.

---

# 13. Permissions

Reporter

May:

- submit Reports.

Moderator

May:

- investigate Cases;
- collect evidence;
- issue decisions;
- close Cases.

Administrator

May:

- inspect all Cases;
- override administrative metadata where permitted.

---

# 14. Domain Events

Examples:

- ModerationCaseCreated
- ReportSubmitted
- EvidenceAdded
- InvestigationStarted
- ModerationDecisionRecorded
- CaseClosed

Events represent completed moderation facts.

---

# 15. Validation

API

- report reason;
- attachment validity.

Application

- referenced entity existence;
- duplicate report detection.

Domain

- lifecycle transitions;
- evidence immutability;
- decision recording rules.

---

# 16. Error Scenarios

Examples:

- ModerationCaseNotFound
- ReportNotFound
- InvalidCaseState
- DuplicateReport
- UnauthorizedModerator
- EvidenceMissing

Errors must be deterministic.

---

# 17. Background Jobs

Background processing includes:

- duplicate report detection;
- AI signal ingestion;
- investigation prioritization;
- stale Case monitoring;
- moderation analytics.

---

# 18. Audit Requirements

The following actions are audited:

- report submission;
- evidence collection;
- moderation decisions;
- case closure;
- administrative actions.

Audit history is immutable.

---

# 19. Concurrency Requirements

Concurrent Reports concerning the same entity may be merged into a single Case.

Simultaneous moderator actions must preserve Case consistency.

Decision recording must be atomic.

---

# 20. Security Requirements

Moderation information is confidential.

Only authorized moderators and administrators may access Case details.

Evidence access follows the principle of least privilege.

---

# 21. Compliance Requirements

Moderation records must comply with applicable legal, privacy, and consumer protection regulations.

Evidence retention must satisfy legal retention requirements where applicable.

---

# 22. Non-Goals

The Moderation domain does not implement:

- user authentication;
- payment processing;
- search indexing;
- messaging;
- recommendation algorithms.

---

# 23. Extension Points

Future enhancements include:

- appeals;
- moderator collaboration;
- AI-assisted investigations;
- fraud scoring;
- trust scoring;
- automated policy classification;
- regional moderation policies.

Extensions must preserve auditability and investigation integrity.

---

# 24. Acceptance Criteria

The Moderation domain is complete when:

- every investigation is represented by a Moderation Case;
- Reports are linked to Cases;
- evidence is immutable;
- decisions are append-only;
- Cases follow the defined lifecycle;
- automated systems provide recommendations only;
- domain events are emitted correctly;
- automated tests validate lifecycle transitions, permissions, report merging, evidence handling, and concurrent investigations.