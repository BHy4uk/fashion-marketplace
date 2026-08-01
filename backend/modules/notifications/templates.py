"""Notification templates (DOMAIN-010 §11) — map a business event to zero or more
recipient-specific notification specs. Pure functions of the event payload; business
data is injected here at render time. Adding/adjusting a message never touches the
aggregate or the emitting domains.
"""
from __future__ import annotations


def _money(payload: dict) -> str:
    amt = payload.get("amount")
    cur = payload.get("currency", "")
    if amt is None:
        return ""
    return f"{cur} {amt / 100:,.0f}".strip()


def specs_for(event_type: str, payload: dict) -> list[dict]:
    """Return list of {recipient_id, notif_type, title, body}. Empty => no notification."""
    p = payload

    if event_type == "OfferCreated":
        return [{
            "recipient_id": p["seller_id"], "notif_type": "OfferReceived",
            "title": "New offer received",
            "body": f"A buyer has made an offer of {_money(p)}. Tap to review and respond.",
        }]

    if event_type == "CounterOfferCreated":
        awaiting = p.get("awaiting")
        recipient = p["buyer_id"] if awaiting == "buyer" else p["seller_id"]
        return [{
            "recipient_id": recipient, "notif_type": "CounterOfferReceived",
            "title": "Counter offer received",
            "body": f"A counter offer of {_money(p)} has been made. Tap to accept, reject, or counter.",
        }]

    if event_type == "OfferRejected":
        return [{
            "recipient_id": p["buyer_id"], "notif_type": "OfferRejected",
            "title": "Offer declined",
            "body": "The seller has declined your offer. You can make a new offer at a different price.",
        }]

    if event_type == "OfferAccepted":
        # notify the party who did NOT accept
        accepted_by = p.get("accepted_by")
        recipient = p["buyer_id"] if accepted_by == "seller" else p["seller_id"]
        return [{
            "recipient_id": recipient, "notif_type": "OfferAccepted",
            "title": "Your offer was accepted" if accepted_by == "seller" else "Offer accepted",
            "body": f"An offer of {_money({'amount': p.get('accepted_amount'), 'currency': p.get('currency')})} was accepted. An order has been created.",
        }]

    if event_type == "OrderCreated":
        if p.get("offer_id"):  # offer flow: OfferAccepted already notified both parties
            return []
        return [{
            "recipient_id": p["seller_id"], "notif_type": "OrderReceived",
            "title": "New order received",
            "body": f"Order {p.get('order_number')} was placed via Buy Now. Awaiting buyer payment.",
        }]

    if event_type == "PaymentCaptured":
        return [{
            "recipient_id": p["seller_id"], "notif_type": "PaymentReceived",
            "title": "Payment received",
            "body": f"Payment of {_money(p)} was captured for order {p.get('order_id')}. Prepare the item for shipment.",
        }]

    if event_type == "ShipmentDispatched":
        return [{
            "recipient_id": p["buyer_id"], "notif_type": "ShipmentDispatched",
            "title": "Your order has shipped",
            "body": f"Tracking number: {p.get('tracking_number')} ({p.get('carrier')}).",
        }]

    if event_type == "ShipmentDelivered":
        return [{
            "recipient_id": p["seller_id"], "notif_type": "OrderDelivered",
            "title": "Your item was delivered",
            "body": "The buyer has received the item. The order will complete shortly.",
        }]

    if event_type == "OrderCompleted":
        return [
            {"recipient_id": p["seller_id"], "notif_type": "OrderCompleted",
             "title": "Order completed — payout scheduled",
             "body": f"Order {p.get('order_number') or p.get('order_id')} is complete. Your escrow payout is scheduled."},
            {"recipient_id": p["buyer_id"], "notif_type": "OrderCompleted",
             "title": "Order completed",
             "body": f"Your order {p.get('order_number') or p.get('order_id')} is complete. Don't forget to leave a review!"},
        ]

    if event_type == "ReviewPublished":
        return [{
            "recipient_id": p["recipient_id"], "notif_type": "ReviewReceived",
            "title": f"You received a {p.get('rating')}★ review",
            "body": "Tap to read the review on your profile.",
        }]

    if event_type == "MessageSent":
        author = p.get("author_id")
        return [{
            "recipient_id": uid, "notif_type": "NewMessage",
            "title": "New message",
            "body": "You have a new message. Open your inbox to reply.",
        } for uid in p.get("participants", []) if uid != author]

    return []
