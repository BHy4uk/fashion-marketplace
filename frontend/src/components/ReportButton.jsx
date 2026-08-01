import React, { useState } from "react";
import { toast } from "sonner";
import api, { apiError } from "../lib/api";
import { useAuth } from "../context/AuthContext";

const REASONS = ["Counterfeit / fake", "Prohibited item", "Inappropriate content",
  "Spam or scam", "Misleading listing", "Other"];

export default function ReportButton({ targetType, targetId, targetContext, label = "Report" }) {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState(REASONS[0]);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);

  if (!user) return null;

  const submit = async () => {
    setBusy(true);
    try {
      await api.post("/moderation/reports", {
        target_type: targetType, target_id: targetId,
        target_context: targetContext || null, reason, note: note || null,
      });
      toast.success("Report submitted — our team will review it");
      setOpen(false); setNote("");
    } catch (e) {
      toast.error(apiError(e));
    } finally { setBusy(false); }
  };

  if (!open) {
    return (
      <button className="nav-link" onClick={() => setOpen(true)} data-testid="report-open-button"
        style={{ background: "none", border: "none", cursor: "pointer", fontSize: 12, color: "var(--muted,#888)", padding: 0 }}>
        ⚑ {label}
      </button>
    );
  }
  return (
    <div className="panel" style={{ padding: 12, marginTop: 10 }} data-testid="report-form">
      <div className="overline" style={{ marginBottom: 6 }}>Report this {targetType}</div>
      <select value={reason} onChange={(e) => setReason(e.target.value)} data-testid="report-reason"
        style={{ width: "100%", marginBottom: 8 }}>
        {REASONS.map((r) => <option key={r} value={r}>{r}</option>)}
      </select>
      <textarea placeholder="Add details (optional)" value={note} maxLength={2000}
        onChange={(e) => setNote(e.target.value)} data-testid="report-note"
        style={{ width: "100%", minHeight: 56 }} />
      <div className="row" style={{ gap: 8, marginTop: 8 }}>
        <button className="btn btn-primary btn-sm" disabled={busy} onClick={submit} data-testid="report-submit">Submit report</button>
        <button className="btn btn-sm" onClick={() => setOpen(false)} data-testid="report-cancel">Cancel</button>
      </div>
    </div>
  );
}
