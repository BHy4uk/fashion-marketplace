# Shipping Domain Specification

**Version:** 1.0
**Status:** Approved
**Document ID:** DOMAIN-007

---

# 1. Purpose

The Shipping domain manages the physical fulfillment and delivery of purchased items.

It coordinates shipment creation, carrier integration, shipment tracking, delivery confirmation, and shipping lifecycle management.

The Shipping domain is responsible for logistics but never owns Orders or Listings.

---

# 2. Responsibilities

The Shipping domain owns:

- Shipment creation
- Shipment lifecycle
- Carrier integration
- Tracking information
- Delivery confirmation
- Shipping labels
- Shipping history

The Shipping domain does not own:

- Orders
- Payments
- Listings
- Offers
- Reviews

---

# 3. Aggregate Root

Aggregate Root

- Shipment

Child Entities

- ShipmentTrackingEvent
- ShippingLabel
- DeliveryConfirmation

Value Objects

- ShipmentId
- TrackingNumber
- CarrierCode
- ShippingAddress
- DeliveryMethod

---

# 4. Shipment Responsibilities

A Shipment represents the logistics process for fulfilling one Order.

Each Shipment references exactly one Order.

A Shipment records the complete delivery lifecycle.

---

# 5. Invariants

### INV-001

Every Shipment references exactly one Order.

---

### INV-002

Shipment identifiers never change.

---

### INV-003

Tracking numbers are unique within the same carrier.

---

### INV-004

Shipment history is immutable.

---

### INV-005

A Delivered Shipment cannot return to In Transit.

---

### INV-006

Every Shipment has exactly one current status.

---

### INV-007

Delivery confirmation belongs to exactly one Shipment.

---

# 6. Shipment Lifecycle

```
Created

↓

AwaitingShipment

↓

LabelGenerated

↓

ReadyForPickup

↓

InTransit

↓

OutForDelivery

↓

Delivered
```

Alternative terminal states:

```
Returned

Canceled

Lost
```

Lifecycle transitions must follow the defined state machine.

---

# 7. Shipment Creation

A Shipment may be created only when:

- an eligible Order exists;
- payment requirements have been satisfied according to business rules;
- shipping information is complete.

Shipment creation never creates or modifies an Order.

---

# 8. Carrier Integration

Supported carriers are interchangeable.

Examples:

- DHL
- UPS
- FedEx
- Nova Poshta
- InPost

Carrier-specific logic belongs exclusively to infrastructure adapters.

Business rules must remain carrier-independent.

---

# 9. Shipping Labels

A Shipping Label contains:

- carrier information;
- shipment reference;
- shipping address;
- barcode or QR code where applicable.

Labels may be regenerated if permitted by carrier rules.

Historical labels remain auditable.

---

# 10. Tracking

Tracking information consists of chronological events.

Examples:

- Label Created
- Accepted by Carrier
- In Transit
- Customs Clearance
- Out for Delivery
- Delivered
- Returned

Tracking events are append-only.

---

# 11. Delivery Confirmation

Delivery may be confirmed by:

- carrier confirmation;
- buyer confirmation;
- administrative resolution.

Confirmation records include:

- timestamp;
- confirmation source;
- optional proof of delivery.

Delivery confirmation is immutable.

---

# 12. Shipping Addresses

A Shipment references shipping information captured at the time of fulfillment.

Subsequent changes to a User's profile address must not affect historical Shipments.

Address data should be retained in accordance with applicable legal and privacy requirements.

---

# 13. Order Interaction

The Shipping domain communicates Order progress through domain events.

Shipment status changes never update Order state directly.

The Orders domain decides how shipment events affect the Order lifecycle.

---

# 14. Permissions

Buyer

May:

- view shipment status;
- track deliveries.

Seller

May:

- prepare shipments;
- generate shipping labels;
- submit tracking information where applicable.

Administrator

May:

- inspect shipment history;
- resolve logistics issues.

Carrier interactions remain provider-controlled.

---

# 15. Domain Events

Examples:

- ShipmentCreated
- ShippingLabelGenerated
- ShipmentDispatched
- ShipmentInTransit
- ShipmentOutForDelivery
- ShipmentDelivered
- ShipmentReturned
- ShipmentLost
- DeliveryConfirmed

Events represent completed logistics facts.

---

# 16. Validation

API

- shipping address format;
- carrier selection;
- tracking number format.

Application

- Order eligibility;
- shipment ownership;
- carrier availability.

Domain

- lifecycle transitions;
- shipment invariants;
- delivery rules.

---

# 17. Error Scenarios

Examples:

- ShipmentNotFound
- InvalidShipmentState
- InvalidTrackingNumber
- CarrierUnavailable
- LabelGenerationFailed
- DeliveryConfirmationFailed
- ShipmentAlreadyDelivered
- ShipmentCanceled

Errors must be deterministic.

---

# 18. Background Jobs

Background processing includes:

- carrier status synchronization;
- tracking updates;
- delivery reminders;
- lost shipment monitoring;
- shipment analytics aggregation.

---

# 19. Audit Requirements

The following actions are audited:

- shipment creation;
- label generation;
- carrier assignment;
- tracking updates;
- delivery confirmation;
- administrative interventions.

Shipment history is immutable.

---

# 20. Concurrency Requirements

Shipment operations must be idempotent where applicable.

Duplicate carrier callbacks and repeated tracking events must not corrupt shipment state.

Concurrent delivery confirmations must result in a single authoritative outcome.

---

# 21. Security Requirements

Shipment information is visible only to authorized participants and administrators.

Tracking information must not expose confidential internal logistics data.

Carrier callbacks must be authenticated and verified.

---

# 22. Compliance Requirements

The Shipping domain must support applicable shipping, customs, consumer protection, and privacy regulations.

Retention of shipment records must comply with applicable legal requirements.

---

# 23. Non-Goals

The Shipping domain does not implement:

- payment processing;
- order creation;
- inventory management;
- recommendation logic;
- AI decision making.

---

# 24. Extension Points

Future enhancements include:

- split shipments;
- multiple packages per Order;
- international customs documentation;
- pickup point delivery;
- local courier delivery;
- scheduled delivery windows;
- digital proof of delivery;
- shipment insurance.

Extensions must preserve shipment history and lifecycle integrity.

---

# 25. Acceptance Criteria

The Shipping domain is complete when:

- shipment lifecycle is enforced;
- carrier integrations are provider-independent;
- tracking events are append-only;
- delivery confirmation is immutable;
- shipment history is fully auditable;
- domain events are emitted correctly;
- duplicate callbacks are handled safely;
- automated tests validate successful, failed, returned, lost, and concurrent shipping scenarios.