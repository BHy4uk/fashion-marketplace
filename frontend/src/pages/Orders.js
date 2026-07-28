import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import api, { formatPrice, apiError } from "../lib/api";
import { useAuth } from "../context/AuthContext";

const STATUS_BADGE = {
  AwaitingPayment: "badge-primary", Paid: "badge-solid", PreparingShipment: "badge-solid",
  Shipped: "badge-solid", Delivered: "badge-solid", Completed: "badge-solid",
  Canceled: "badge", Refunded: "badge", Closed: "badge",
};

export default function Orders() {
  const { user } = useAuth();
  const [box, setBox] = useState("buyer");
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    api.get(`/orders?box=${box}`).then((r) => setItems(r.data.items)).finally(() => setLoading(false));
  }, [box]);

  useEffect(load, [load]);

  if (!user) return null;

  const cancel = async (id) => {
    try {
      await api.post(`/orders/${id}/cancel`);
      toast.success("Order canceled");
      load();
    } catch (e) {
      toast.error(apiError(e));
    }
  };

  return (
    <div className="container" style={{ paddingTop: 24, paddingBottom: 60 }}>
      <div className="section-head"><h2 data-testid="orders-heading">Orders</h2></div>
      <div className="toolbar">
        <button className={`chip ${box === "buyer" ? "chip-active" : ""}`}
          onClick={() => setBox("buyer")} data-testid="orders-tab-buyer">Purchases</button>
        <button className={`chip ${box === "seller" ? "chip-active" : ""}`}
          onClick={() => setBox("seller")} data-testid="orders-tab-seller">Sales</button>
      </div>

      {loading ? (
        <div style={{ padding: 40 }}><div className="spin" /></div>
      ) : items.length === 0 ? (
        <div className="empty" data-testid="orders-empty">No orders here yet.</div>
      ) : (
        <div className="stack" style={{ gap: 12 }} data-testid="orders-list">
          {items.map((o) => (
            <div key={o.id} className="panel" data-testid={`order-row-${o.id}`} style={{ padding: 18 }}>
              <div className="row" style={{ justifyContent: "space-between", flexWrap: "wrap", gap: 8 }}>
                <div>
                  <div className="row" style={{ gap: 10 }}>
                    <span className="overline">{o.order_number}</span>
                    <span className={`badge ${STATUS_BADGE[o.status] || "badge"}`}
                      data-testid={`order-status-${o.id}`}>{o.status}</span>
                  </div>
                  <div className="heading" style={{ fontSize: 22, marginTop: 6 }}>
                    {formatPrice({ amount: o.total, currency: o.currency })}
                  </div>
                  {box === "seller" && (
                    <div className="hint">Platform fee: {formatPrice({ amount: o.platform_fee, currency: o.currency })} ·
                      {" "}You receive {formatPrice({ amount: o.total - o.platform_fee, currency: o.currency })}</div>
                  )}
                  <Link to={`/listing/${o.listing_id}`} className="overline"
                    data-testid={`order-listing-${o.id}`}>View item →</Link>
                </div>
                <div className="row" style={{ gap: 8 }}>
                  {box === "buyer" && o.status === "AwaitingPayment" && (
                    <>
                      <button className="btn btn-primary btn-sm"
                        onClick={() => toast.success("Checkout (LiqPay escrow) ships in Phase 6")}
                        data-testid={`order-pay-${o.id}`}>Pay now</button>
                      <button className="btn btn-sm" onClick={() => cancel(o.id)}
                        data-testid={`order-cancel-${o.id}`}>Cancel</button>
                    </>
                  )}
                </div>
              </div>
              {o.status_history?.length > 0 && (
                <div className="hint mt-16" data-testid={`order-history-${o.id}`}>
                  {o.status_history.map((h, i) => (
                    <span key={i}>{i > 0 && " → "}{h.to_status}</span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
