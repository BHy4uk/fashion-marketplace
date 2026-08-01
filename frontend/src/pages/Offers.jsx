import React, { useCallback, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { useTranslation } from "react-i18next";
import api, { formatPrice, apiError } from "../lib/api";
import { useAuth } from "../context/AuthContext";

const STATUS_BADGE = {
  Active: "badge-primary", Accepted: "badge-solid", Rejected: "badge",
  Canceled: "badge", Expired: "badge",
};

function Money({ amount, currency }) {
  return <>{formatPrice({ amount, currency })}</>;
}

export default function Offers() {
  const { user } = useAuth();
  const { t } = useTranslation("offers");
  const [searchParams, setSearchParams] = useSearchParams();
  const [box, setBox] = useState(() => {
    const v = searchParams.get("box");
    return v === "seller" ? "seller" : "buyer";
  });
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [counterFor, setCounterFor] = useState(null);
  const [counterVal, setCounterVal] = useState("");
  const [counts, setCounts] = useState({ buyer: 0, seller: 0 });

  const load = useCallback(() => {
    setLoading(true);
    api.get(`/offers?box=${box}`).then((r) => setItems(r.data.items)).finally(() => setLoading(false));
  }, [box]);

  useEffect(load, [load]);

  useEffect(() => {
    api.get("/offers/counts").then((r) => setCounts(r.data)).catch(() => {});
  }, [items]);

  if (!user) return null;

  const act = async (id, verb, body) => {
    try {
      await api.post(`/offers/${id}/${verb}`, body || {});
      toast.success(`Offer ${verb}ed`);
      setCounterFor(null);
      load();
    } catch (e) {
      toast.error(apiError(e));
    }
  };

  const roleFor = (o) => (o.buyer_id === user.id ? "buyer" : "seller");

  return (
    <div className="container" style={{ paddingTop: 28, paddingBottom: 80 }}>

      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 26, fontWeight: 700, letterSpacing: "-0.02em", marginBottom: 16 }}
          data-testid="offers-heading">{t("heading")}</h1>
        <div className="toolbar">
          <button className={`chip ${box === "buyer" ? "chip-active" : ""}`}
            onClick={() => { setBox("buyer"); setSearchParams({ box: "buyer" }); }} data-testid="offers-tab-buyer">
            {t("tab.buyer")}
            {counts.buyer > 0 && box !== "buyer" && (
              <span style={{ display: "inline-flex", alignItems: "center", justifyContent: "center", background: "var(--text)", color: "#fff", borderRadius: 999, fontSize: 10, fontWeight: 700, minWidth: 16, height: 16, padding: "0 4px", marginLeft: 5 }}>
                {counts.buyer}
              </span>
            )}
          </button>
          <button className={`chip ${box === "seller" ? "chip-active" : ""}`}
            onClick={() => { setBox("seller"); setSearchParams({ box: "seller" }); }} data-testid="offers-tab-seller">
            {t("tab.seller")}
            {counts.seller > 0 && box !== "seller" && (
              <span style={{ display: "inline-flex", alignItems: "center", justifyContent: "center", background: "var(--text)", color: "#fff", borderRadius: 999, fontSize: 10, fontWeight: 700, minWidth: 16, height: 16, padding: "0 4px", marginLeft: 5 }}>
                {counts.seller}
              </span>
            )}
          </button>
        </div>
      </div>

      {loading ? (
        <div style={{ padding: "40px 0", display: "flex", justifyContent: "center" }}>
          <div className="spin" />
        </div>
      ) : items.length === 0 ? (
        <div className="empty" data-testid="offers-empty">{t("empty")}</div>
      ) : (
        <div className="stack" style={{ gap: 12 }} data-testid="offers-list">
          {items.map((o) => {
            const myRole = roleFor(o);
            const myTurn = o.status === "Active" && o.awaiting === myRole;
            return (
              <div key={o.id} className="panel" data-testid={`offer-row-${o.id}`}>

                {/* Header: status + context */}
                <div className="row" style={{ justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 10, marginBottom: 14 }}>
                  <div className="row" style={{ gap: 10 }}>
                    <span className={`badge ${STATUS_BADGE[o.status]}`} data-testid={`offer-status-${o.id}`}>
                      {o.status}
                    </span>
                    {o.status === "Active" && (
                      <span className="overline" style={{ color: "var(--muted)" }}>
                        Waiting on {o.awaiting}
                      </span>
                    )}
                    {box === "seller" && o.buyer_name && (
                      <span className="hint">from {o.buyer_name}</span>
                    )}
                  </div>
                  <Link to={`/listing/${o.listing_id}`} className="overline" style={{ color: "var(--muted)" }}
                    data-testid={`offer-listing-${o.id}`}>View listing →</Link>
                </div>

                {/* Offer amount */}
                <div style={{ fontSize: 28, fontWeight: 700, letterSpacing: "-0.03em", marginBottom: 16 }}>
                  <Money amount={o.current_amount} currency={o.currency} />
                </div>

                {/* Actions */}
                {(myTurn || (myRole === "buyer" && o.status === "Active")) && (
                  <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
                    {myTurn && (
                      <>
                        <button className="btn btn-primary btn-sm" onClick={() => act(o.id, "accept")}
                          data-testid={`offer-accept-${o.id}`}>Accept</button>
                        <button className="btn btn-sm" onClick={() => act(o.id, "reject")}
                          data-testid={`offer-reject-${o.id}`}>Reject</button>
                        <button className="btn btn-sm"
                          onClick={() => { setCounterFor(o.id); setCounterVal(String(Math.round(o.current_amount / 100))); }}
                          data-testid={`offer-counter-${o.id}`}>Counter offer</button>
                      </>
                    )}
                    {myRole === "buyer" && o.status === "Active" && (
                      <button className="btn btn-sm" onClick={() => act(o.id, "cancel")}
                        data-testid={`offer-cancel-${o.id}`}>Withdraw</button>
                    )}
                  </div>
                )}

                {/* Counter input */}
                {counterFor === o.id && (
                  <form className="row" style={{ gap: 8, marginTop: 16, paddingTop: 16, borderTop: "1px solid var(--border)" }}
                    onSubmit={(e) => {
                      e.preventDefault();
                      act(o.id, "counter", { amount: Math.round(parseFloat(counterVal) * 100) });
                    }}>
                    <input type="number" min="1" step="0.01" value={counterVal}
                      onChange={(e) => setCounterVal(e.target.value)}
                      placeholder={`Your counter (${o.currency})`}
                      data-testid={`offer-counter-input-${o.id}`} style={{ maxWidth: 200 }} />
                    <button className="btn btn-primary btn-sm" data-testid={`offer-counter-submit-${o.id}`}>
                      Send
                    </button>
                    <button type="button" className="btn btn-sm" onClick={() => setCounterFor(null)}>
                      Cancel
                    </button>
                  </form>
                )}

                {/* Negotiation history */}
                {o.revisions?.length > 1 && (
                  <div className="hint" style={{ marginTop: 16, paddingTop: 16, borderTop: "1px solid var(--border)" }}
                    data-testid={`offer-history-${o.id}`}>
                    History:{" "}
                    {o.revisions.map((r, i) => (
                      <span key={i}>
                        {i > 0 && " → "}
                        {r.actor} <Money amount={r.amount} currency={r.currency} />
                      </span>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
