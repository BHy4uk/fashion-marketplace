import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
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
  const [box, setBox] = useState("buyer");
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [counterFor, setCounterFor] = useState(null);
  const [counterVal, setCounterVal] = useState("");

  const load = useCallback(() => {
    setLoading(true);
    api.get(`/offers?box=${box}`).then((r) => setItems(r.data.items)).finally(() => setLoading(false));
  }, [box]);

  useEffect(load, [load]);

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
    <div className="container" style={{ paddingTop: 24, paddingBottom: 60 }}>
      <div className="section-head">
        <h2 data-testid="offers-heading">Offers</h2>
      </div>
      <div className="toolbar">
        <button className={`chip ${box === "buyer" ? "chip-active" : ""}`}
          onClick={() => setBox("buyer")} data-testid="offers-tab-buyer">My offers (sent)</button>
        <button className={`chip ${box === "seller" ? "chip-active" : ""}`}
          onClick={() => setBox("seller")} data-testid="offers-tab-seller">Received</button>
      </div>

      {loading ? (
        <div style={{ padding: 40 }}><div className="spin" /></div>
      ) : items.length === 0 ? (
        <div className="empty" data-testid="offers-empty">No offers here yet.</div>
      ) : (
        <div className="stack" style={{ gap: 12 }} data-testid="offers-list">
          {items.map((o) => {
            const myRole = roleFor(o);
            const myTurn = o.status === "Active" && o.awaiting === myRole;
            return (
              <div key={o.id} className="panel" data-testid={`offer-row-${o.id}`}
                style={{ padding: 18 }}>
                <div className="row" style={{ justifyContent: "space-between", flexWrap: "wrap", gap: 8 }}>
                  <div>
                    <div className="row" style={{ gap: 10 }}>
                      <span className={`badge ${STATUS_BADGE[o.status]}`} data-testid={`offer-status-${o.id}`}>
                        {o.status}
                      </span>
                      {o.status === "Active" && (
                        <span className="overline">Awaiting {o.awaiting}</span>
                      )}
                      {box === "seller" && <span className="hint">from {o.buyer_name}</span>}
                    </div>
                    <div className="heading" style={{ fontSize: 22, marginTop: 6 }}>
                      <Money amount={o.current_amount} currency={o.currency} />
                    </div>
                    <Link to={`/listing/${o.listing_id}`} className="overline"
                      data-testid={`offer-listing-${o.id}`}>View listing →</Link>
                  </div>

                  <div className="row" style={{ gap: 8 }}>
                    {myTurn && (
                      <>
                        <button className="btn btn-primary btn-sm" onClick={() => act(o.id, "accept")}
                          data-testid={`offer-accept-${o.id}`}>Accept</button>
                        <button className="btn btn-sm" onClick={() => act(o.id, "reject")}
                          data-testid={`offer-reject-${o.id}`}>Reject</button>
                        <button className="btn btn-sm"
                          onClick={() => { setCounterFor(o.id); setCounterVal(String(Math.round(o.current_amount / 100))); }}
                          data-testid={`offer-counter-${o.id}`}>Counter</button>
                      </>
                    )}
                    {myRole === "buyer" && o.status === "Active" && (
                      <button className="btn btn-sm" onClick={() => act(o.id, "cancel")}
                        data-testid={`offer-cancel-${o.id}`}>Cancel</button>
                    )}
                  </div>
                </div>

                {counterFor === o.id && (
                  <form className="row mt-16" style={{ gap: 8 }}
                    onSubmit={(e) => { e.preventDefault(); act(o.id, "counter", { amount: Math.round(parseFloat(counterVal) * 100) }); }}>
                    <input type="number" min="1" step="0.01" value={counterVal}
                      onChange={(e) => setCounterVal(e.target.value)}
                      data-testid={`offer-counter-input-${o.id}`} style={{ maxWidth: 200 }} />
                    <button className="btn btn-primary btn-sm" data-testid={`offer-counter-submit-${o.id}`}>
                      Send counter ({o.currency})
                    </button>
                  </form>
                )}

                {o.revisions?.length > 1 && (
                  <div className="hint mt-16" data-testid={`offer-history-${o.id}`}>
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
