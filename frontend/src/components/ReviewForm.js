import React, { useState } from "react";
import { toast } from "sonner";
import api, { apiError } from "../lib/api";

function Stars({ value, onChange, testidPrefix }) {
  const [hover, setHover] = useState(0);
  return (
    <div className="row" style={{ gap: 4 }} role="radiogroup" aria-label="Rating">
      {[1, 2, 3, 4, 5].map((n) => (
        <button
          key={n}
          type="button"
          onMouseEnter={() => setHover(n)}
          onMouseLeave={() => setHover(0)}
          onClick={() => onChange(n)}
          data-testid={`${testidPrefix}-star-${n}`}
          aria-label={`${n} star${n > 1 ? "s" : ""}`}
          style={{
            background: "none", border: "none", cursor: "pointer", padding: 0,
            fontSize: 26, lineHeight: 1,
            color: (hover || value) >= n ? "var(--primary)" : "var(--line, #d8d8d8)",
            transition: "color 120ms ease, transform 120ms ease",
            transform: (hover || value) >= n ? "scale(1.08)" : "scale(1)",
          }}
        >
          ★
        </button>
      ))}
    </div>
  );
}

export default function ReviewForm({ orderId, recipientName, onDone }) {
  const [open, setOpen] = useState(false);
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    if (rating < 1) {
      toast.error("Please pick a star rating");
      return;
    }
    setBusy(true);
    try {
      await api.post("/reviews", { order_id: orderId, rating, comment: comment || null });
      toast.success("Review published — thanks for building trust");
      setOpen(false);
      onDone && onDone();
    } catch (e) {
      toast.error(apiError(e));
    } finally {
      setBusy(false);
    }
  };

  if (!open) {
    return (
      <button className="btn btn-sm" onClick={() => setOpen(true)}
        data-testid={`order-review-open-${orderId}`}>
        Leave a review{recipientName ? ` for ${recipientName}` : ""}
      </button>
    );
  }

  return (
    <div className="panel mt-16" style={{ padding: 14, background: "var(--bg-soft, #fafafa)" }}
      data-testid={`order-review-form-${orderId}`}>
      <div className="overline" style={{ marginBottom: 8 }}>
        Rate {recipientName || "this participant"}
      </div>
      <Stars value={rating} onChange={setRating} testidPrefix={`order-review-${orderId}`} />
      <textarea
        className="mt-16"
        style={{ width: "100%", minHeight: 70 }}
        placeholder="Share how the transaction went (optional)"
        value={comment}
        maxLength={2000}
        onChange={(e) => setComment(e.target.value)}
        data-testid={`order-review-comment-${orderId}`}
      />
      <div className="row mt-16" style={{ gap: 8 }}>
        <button className="btn btn-primary btn-sm" disabled={busy} onClick={submit}
          data-testid={`order-review-submit-${orderId}`}>
          {busy ? "…" : "Publish review"}
        </button>
        <button className="btn btn-sm" onClick={() => setOpen(false)}
          data-testid={`order-review-cancel-${orderId}`}>Cancel</button>
      </div>
    </div>
  );
}
