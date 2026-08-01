import React, { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { useTranslation } from "react-i18next";
import api, { apiError } from "../lib/api";
import { useAuth } from "../context/AuthContext";

const STATUSES = ["", "Created", "UnderReview", "Investigation", "DecisionMade", "Closed", "Dismissed"];
const ACTIONS = [
  "NoAction", "Warning", "ListingHidden", "ListingRemoved",
  "MessageHidden", "ReviewHidden", "ReviewRemoved",
  "TemporarySuspension", "PermanentSuspension",
];
const fmt = (t) => { try { return new Date(t).toLocaleString(); } catch { return ""; } };

export default function AdminModeration() {
  const { user } = useAuth();
  const { t } = useTranslation("admin");
  const [stats, setStats] = useState(null);
  const [filter, setFilter] = useState("");
  const [cases, setCases] = useState([]);
  const [active, setActive] = useState(null);
  const [detail, setDetail] = useState(null);
  const [action, setAction] = useState("Warning");
  const [reason, setReason] = useState("");
  const [comment, setComment] = useState("");

  const loadList = useCallback(async () => {
    try {
      const [s, l] = await Promise.all([
        api.get("/moderation/stats"),
        api.get("/moderation/cases", { params: filter ? { status: filter } : {} }),
      ]);
      setStats(s.data);
      setCases(l.data.items);
    } catch (e) { toast.error(apiError(e)); }
  }, [filter]);

  const loadDetail = useCallback(async (id) => {
    try { setDetail((await api.get(`/moderation/cases/${id}`)).data); }
    catch (e) { toast.error(apiError(e)); }
  }, []);

  useEffect(() => { loadList(); }, [loadList]);
  useEffect(() => { if (active) loadDetail(active); }, [active, loadDetail]);

  const act = async (fn) => { try { await fn(); toast.success("Done"); loadList(); if (active) loadDetail(active); } catch (e) { toast.error(apiError(e)); } };

  if (!user || !["admin", "moderator"].includes(user.role)) {
    return <div className="container" style={{ padding: 40 }}><div className="empty" data-testid="admin-forbidden">{t("moderation.error.forbidden")}</div></div>;
  }

  return (
    <div className="container" style={{ paddingTop: 28, paddingBottom: 80 }}>
      <div style={{ marginBottom: 24 }}>
        <span className="overline" style={{ color: "var(--muted)" }}>{t("moderation.overline")}</span>
        <h1 style={{ fontSize: 26, fontWeight: 700, letterSpacing: "-0.02em", margin: "6px 0 0" }}
          data-testid="admin-moderation-heading">{t("moderation.heading")}</h1>
      </div>

      {stats && (
        <div className="row" style={{ gap: 12, flexWrap: "wrap", marginBottom: 16 }} data-testid="mod-stats">
          {["open", "Created", "Investigation", "DecisionMade", "Closed", "Dismissed"].map((k) => (
            <div key={k} className="panel" style={{ padding: "8px 14px" }}>
              <div className="overline">{k}</div>
              <div style={{ fontWeight: 700, fontSize: 20 }}>{stats[k] ?? 0}</div>
            </div>
          ))}
        </div>
      )}

      <div className="row" style={{ gap: 8, marginBottom: 12 }}>
        {STATUSES.map((s) => (
          <button key={s || "all"} className={`btn btn-sm ${filter === s ? "btn-primary" : ""}`}
            onClick={() => setFilter(s)} data-testid={`mod-filter-${s || "all"}`}>{s ? t(`moderation.filter.${s}`) : t("moderation.filter.all")}</button>
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "360px 1fr", gap: 12 }}>
        <div className="stack" style={{ gap: 8 }} data-testid="mod-case-list">
          {cases.length === 0 && <div className="empty">{t("moderation.empty.cases")}</div>}
          {cases.map((c) => (
            <button key={c.id} className="panel" onClick={() => setActive(c.id)}
              data-testid={`mod-case-${c.id}`}
              style={{ textAlign: "left", padding: 12, cursor: "pointer",
                border: c.id === active ? "2px solid var(--text)" : "1px solid var(--border)" }}>
              <div className="row" style={{ justifyContent: "space-between" }}>
                <span style={{ fontWeight: 600, fontSize: 13 }}>{c.target_type} · {c.target_id.slice(0, 8)}</span>
                <span className="badge">{c.status}</span>
              </div>
              <div className="hint" style={{ marginTop: 4 }}>{c.reports} report(s) · {c.decisions} decision(s)</div>
            </button>
          ))}
        </div>

        <div className="panel" style={{ padding: 16, minHeight: 400 }} data-testid="mod-case-detail">
          {!detail ? <div className="empty" style={{ margin: "auto" }}>{t("moderation.empty.select")}</div> : (
            <>
              <div className="row" style={{ justifyContent: "space-between", marginBottom: 12 }}>
                <div><strong>{detail.target_type}</strong> · <span className="hint">{detail.target_id}</span></div>
                <span className="badge badge-primary" data-testid="mod-detail-status">{detail.status}</span>
              </div>

              <div className="overline">{t("moderation.section.reports")}</div>
              {detail.reports.map((r) => (
                <div key={r.report_id} className="hint" style={{ marginBottom: 4 }}>
                  {r.reporter_name || r.reporter_id.slice(0, 8)}: <strong>{r.reason}</strong>{r.note ? ` — ${r.note}` : ""}
                </div>
              ))}

              {detail.decisions.length > 0 && (
                <>
                  <div className="overline" style={{ marginTop: 12 }}>{t("moderation.section.decisions")}</div>
                  {detail.decisions.map((d) => (
                    <div key={d.decision_id} className="hint" data-testid={`mod-decision-${d.decision_id}`}>
                      <strong>{d.action}</strong> — {d.reason} <span style={{ opacity: 0.6 }}>({fmt(d.created_at)})</span>
                    </div>
                  ))}
                </>
              )}

              {detail.comments.length > 0 && (
                <>
                  <div className="overline" style={{ marginTop: 12 }}>{t("moderation.section.notes")}</div>
                  {detail.comments.map((x) => (
                    <div key={x.comment_id} className="hint">{x.author_name || "mod"}: {x.text}</div>
                  ))}
                </>
              )}

              {["Closed", "Dismissed"].includes(detail.status) ? (
                <div className="hint" style={{ marginTop: 16 }}>{t("moderation.message.closedCase")}</div>
              ) : (
                <div className="stack" style={{ gap: 10, marginTop: 16, borderTop: "1px solid var(--border)", paddingTop: 16 }}>
                  <div className="row" style={{ gap: 8 }}>
                    <button className="btn btn-sm" data-testid="mod-investigate"
                      onClick={() => act(() => api.post(`/moderation/cases/${active}/investigate`))}>{t("moderation.button.investigate")}</button>
                    <button className="btn btn-sm" data-testid="mod-close"
                      onClick={() => act(() => api.post(`/moderation/cases/${active}/close`))}>{t("moderation.button.close")}</button>
                    <button className="btn btn-sm" data-testid="mod-dismiss"
                      onClick={() => act(() => api.post(`/moderation/cases/${active}/dismiss`, { reason: "no violation" }))}>{t("moderation.button.dismiss")}</button>
                  </div>
                  <div className="row" style={{ gap: 8 }}>
                    <input placeholder={t("moderation.input.addNote")} value={comment} onChange={(e) => setComment(e.target.value)}
                      data-testid="mod-comment-input" style={{ flex: 1 }} />
                    <button className="btn btn-sm" data-testid="mod-comment-submit"
                      onClick={() => act(async () => { await api.post(`/moderation/cases/${active}/comment`, { text: comment }); setComment(""); })}>{t("moderation.button.addNote")}</button>
                  </div>
                  <div className="row" style={{ gap: 8, alignItems: "center" }}>
                    <select value={action} onChange={(e) => setAction(e.target.value)} data-testid="mod-action-select">
                      {ACTIONS.map((a) => <option key={a} value={a}>{a}</option>)}
                    </select>
                    <input placeholder={t("moderation.input.decisionReason")} value={reason} onChange={(e) => setReason(e.target.value)}
                      data-testid="mod-decision-reason" style={{ flex: 1 }} />
                    <button className="btn btn-primary btn-sm" data-testid="mod-decision-submit"
                      onClick={() => {
                        if (!reason.trim()) { toast.error(t("moderation.error.reasonRequired")); return; }
                        act(async () => {
                          await api.post(`/moderation/cases/${active}/decision`, { action, reason });
                          setReason("");
                        });
                      }}>{t("moderation.button.recordDecision")}</button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
