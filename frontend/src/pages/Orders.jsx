import React, { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { useTranslation } from "react-i18next";
import api, { formatPrice, apiError } from "../lib/api";
import { useAuth } from "../context/AuthContext";
import ReviewForm from "../components/ReviewForm";

const STATUS_BADGE = {
  AwaitingPayment: "badge-primary", Paid: "badge-solid", PreparingShipment: "badge-solid",
  Shipped: "badge-solid", Delivered: "badge-solid", Completed: "badge-solid",
  Canceled: "badge", Refunded: "badge", Closed: "badge",
};

const humanize = (s) => (s || "").replace(/([a-z])([A-Z])/g, "$1 $2");

export default function Orders() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { t } = useTranslation("orders");
  const [box, setBox] = useState("buyer");
  const [items, setItems] = useState([]);
  const [shipments, setShipments] = useState({});
  const [reviews, setReviews] = useState({});
  const [loading, setLoading] = useState(true);
  const [counts, setCounts] = useState({ buyer: 0, seller: 0 });

  const SHIPPED_STATES = ["Paid", "PreparingShipment", "Shipped", "Delivered", "Completed"];

  const load = useCallback(() => {
    setLoading(true);
    api.get(`/orders?box=${box}`).then(async (r) => {
      setItems(r.data.items);
      const relevant = r.data.items.filter((o) => SHIPPED_STATES.includes(o.status));
      const map = {};
      await Promise.all(relevant.map(async (o) => {
        try {
          const res = await api.get(`/shipments/order/${o.id}`);
          if (res.data.shipment) map[o.id] = res.data.shipment;
        } catch (_) { /* no shipment yet */ }
      }));
      setShipments(map);
      const completed = r.data.items.filter((o) => o.status === "Completed");
      const rmap = {};
      await Promise.all(completed.map(async (o) => {
        try {
          const res = await api.get(`/reviews/eligibility/${o.id}`);
          rmap[o.id] = res.data;
        } catch (_) { /* ignore */ }
      }));
      setReviews(rmap);
    }).finally(() => setLoading(false));
  }, [box]);

  useEffect(load, [load]);

  useEffect(() => {
    api.get("/orders/counts").then((r) => setCounts(r.data)).catch(() => {});
  }, [items]);

  if (!user) return null;

  const pay = async (id) => {
    try {
      const { data } = await api.post("/payments/checkout", { order_id: id });
      if (data.checkout_url && data.data) {
        // LiqPay hosted checkout: POST the signed form to the provider
        const form = document.createElement("form");
        form.method = "POST";
        form.action = data.checkout_url;
        [["data", data.data], ["signature", data.signature]].forEach(([n, v]) => {
          const i = document.createElement("input");
          i.type = "hidden"; i.name = n; i.value = v; form.appendChild(i);
        });
        document.body.appendChild(form);
        form.submit();
        return;
      }
      toast.success(t("toast.paymentCaptured"));
      load();
    } catch (e) {
      toast.error(apiError(e));
    }
  };

  const cancel = async (id) => {
    try {
      await api.post(`/orders/${id}/cancel`);
      toast.success(t("toast.canceled"));
      load();
    } catch (e) {
      toast.error(apiError(e));
    }
  };

  const dispatchShipment = async (shipmentId) => {
    try {
      await api.post(`/shipments/${shipmentId}/dispatch`, {});
      toast.success(t("toast.dispatched"));
      load();
    } catch (e) {
      toast.error(apiError(e));
    }
  };

  const confirmDelivery = async (shipmentId) => {
    try {
      await api.post(`/shipments/${shipmentId}/confirm-delivery`);
      toast.success(t("toast.delivered"));
      load();
    } catch (e) {
      toast.error(apiError(e));
    }
  };

  const messageCounterparty = async (orderId) => {
    try {
      const { data } = await api.post("/conversations", {
        context_type: "order", context_id: orderId,
      });
      navigate(`/messages?c=${data.conversation_id}`);
    } catch (e) {
      toast.error(apiError(e));
    }
  };

  return (
    <div className="container" style={{ paddingTop: 28, paddingBottom: 80 }}>

      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 26, fontWeight: 700, letterSpacing: "-0.02em", marginBottom: 16 }}
          data-testid="orders-heading">{t("heading")}</h1>
        <div className="toolbar">
          <button className={`chip ${box === "buyer" ? "chip-active" : ""}`}
            onClick={() => setBox("buyer")} data-testid="orders-tab-buyer">
            {t("tab.buyer")}
            {counts.buyer > 0 && box !== "buyer" && (
              <span style={{ display: "inline-flex", alignItems: "center", justifyContent: "center", background: "var(--text)", color: "#fff", borderRadius: 999, fontSize: 10, fontWeight: 700, minWidth: 16, height: 16, padding: "0 4px", marginLeft: 5 }}>
                {counts.buyer}
              </span>
            )}
          </button>
          <button className={`chip ${box === "seller" ? "chip-active" : ""}`}
            onClick={() => setBox("seller")} data-testid="orders-tab-seller">
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
        <div className="empty" data-testid="orders-empty">{t("empty")}</div>
      ) : (
        <div className="stack" style={{ gap: 12 }} data-testid="orders-list">
          {items.map((o) => (
            <div key={o.id} className="panel" data-testid={`order-row-${o.id}`}>

              {/* Top row: order# + status + item link */}
              <div className="row" style={{ justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 10, marginBottom: 14 }}>
                <div className="row" style={{ gap: 10 }}>
                  <span className="overline" style={{ color: "var(--muted)" }}>{o.order_number}</span>
                  <span className={`badge ${STATUS_BADGE[o.status] || "badge"}`}
                    data-testid={`order-status-${o.id}`}>{humanize(o.status)}</span>
                </div>
                <Link to={`/listing/${o.listing_id}`} className="overline" style={{ color: "var(--muted)" }}
                  data-testid={`order-listing-${o.id}`}>{t("link.viewItem")}</Link>
              </div>

              {/* Price */}
              <div style={{ fontSize: 28, fontWeight: 700, letterSpacing: "-0.03em", marginBottom: 4 }}>
                {formatPrice({ amount: o.total, currency: o.currency })}
              </div>
              {box === "seller" && (
                <div className="hint" style={{ marginBottom: 16 }}>
                  Fee: {formatPrice({ amount: o.platform_fee, currency: o.currency })} · You receive{" "}
                  {formatPrice({ amount: o.total - o.platform_fee, currency: o.currency })}
                </div>
              )}

              {/* Actions */}
              <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 14 }}>
                {box === "buyer" && o.status === "AwaitingPayment" && (
                  <>
                    <button className="btn btn-primary btn-sm" onClick={() => pay(o.id)}
                      data-testid={`order-pay-${o.id}`}>Pay now</button>
                    <button className="btn btn-sm" onClick={() => cancel(o.id)}
                      data-testid={`order-cancel-${o.id}`}>Cancel</button>
                  </>
                )}
                {box === "seller" && o.status === "PreparingShipment" && shipments[o.id] && (
                  <button className="btn btn-primary btn-sm"
                    onClick={() => dispatchShipment(shipments[o.id].id)}
                    data-testid={`order-dispatch-${o.id}`}>Dispatch shipment</button>
                )}
                {box === "buyer" && o.status === "Shipped" && shipments[o.id] && (
                  <button className="btn btn-primary btn-sm"
                    onClick={() => confirmDelivery(shipments[o.id].id)}
                    data-testid={`order-confirm-delivery-${o.id}`}>Confirm delivery</button>
                )}
                <button className="btn btn-sm" onClick={() => messageCounterparty(o.id)}
                  data-testid={`order-message-${o.id}`}>
                  Message {box === "buyer" ? "seller" : "buyer"}
                </button>
              </div>

              {/* Tracking */}
              {shipments[o.id]?.tracking_number && (
                <div className="hint" style={{ marginTop: 16, paddingTop: 16, borderTop: "1px solid var(--border)" }}
                  data-testid={`order-tracking-${o.id}`}>
                  {shipments[o.id].carrier} · {shipments[o.id].tracking_number} · {humanize(shipments[o.id].status)}
                </div>
              )}

              {/* Status history */}
              {o.status_history?.length > 0 && (
                <div className="hint" style={{ marginTop: 10 }} data-testid={`order-history-${o.id}`}>
                  {o.status_history.map((h, i) => (
                    <span key={i}>{i > 0 && " → "}{humanize(h.to_status)}</span>
                  ))}
                </div>
              )}

              {/* Review */}
              {o.status === "Completed" && reviews[o.id]?.is_participant && (
                <div style={{ marginTop: 16, paddingTop: 16, borderTop: "1px solid var(--border)" }}
                  data-testid={`order-review-block-${o.id}`}>
                  {reviews[o.id].already_reviewed ? (
                    <div className="hint" data-testid={`order-reviewed-${o.id}`}>★ You reviewed this transaction</div>
                  ) : (
                    <ReviewForm orderId={o.id}
                      recipientName={box === "buyer" ? "the seller" : "the buyer"}
                      onDone={load} />
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
