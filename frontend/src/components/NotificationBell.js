import React, { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Bell } from "@phosphor-icons/react";
import api, { wsUrl } from "../lib/api";
import { useAuth } from "../context/AuthContext";

const fmt = (t) => {
  if (!t) return "";
  try { return new Date(t).toLocaleString("en-GB", { hour: "2-digit", minute: "2-digit", day: "2-digit", month: "short" }); }
  catch { return ""; }
};

const ROUTE_FOR = {
  NewMessage: "/messages",
  OfferAccepted: "/orders",
  PaymentReceived: "/orders",
  ShipmentDispatched: "/orders",
  OrderDelivered: "/orders",
  OrderCompleted: "/orders",
  ReviewReceived: "/dashboard",
};

export default function NotificationBell() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [count, setCount] = useState(0);
  const [items, setItems] = useState([]);
  const wrapRef = useRef(null);

  const refresh = useCallback(async () => {
    try {
      const [c, l] = await Promise.all([
        api.get("/notifications/unread-count"),
        api.get("/notifications"),
      ]);
      setCount(c.data.count);
      setItems(l.data.items);
    } catch (_) { /* ignore */ }
  }, []);

  useEffect(() => { if (user) refresh(); }, [user, refresh]);

  // live notifications over the shared WebSocket
  useEffect(() => {
    if (!user) return;
    const ws = new WebSocket(wsUrl("/api/ws/messages"));
    ws.onmessage = (ev) => {
      let msg;
      try { msg = JSON.parse(ev.data); } catch { return; }
      if (msg.type === "notification") {
        setCount((c) => c + 1);
        setItems((prev) => [{ id: msg.id, notif_type: msg.notif_type, title: msg.title,
          body: msg.body, read: false, created_at: msg.created_at }, ...prev].slice(0, 50));
      }
    };
    return () => ws.close();
  }, [user]);

  // close on outside click
  useEffect(() => {
    const onDoc = (e) => { if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false); };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  const openNotif = async (n) => {
    setOpen(false);
    if (!n.read) {
      try { await api.post(`/notifications/${n.id}/read`); } catch (_) {}
      setItems((prev) => prev.map((x) => (x.id === n.id ? { ...x, read: true } : x)));
      setCount((c) => Math.max(0, c - 1));
    }
    navigate(ROUTE_FOR[n.notif_type] || "/dashboard");
  };

  const markAll = async () => {
    try { await api.post("/notifications/read-all"); } catch (_) {}
    setItems((prev) => prev.map((x) => ({ ...x, read: true })));
    setCount(0);
  };

  if (!user) return null;

  return (
    <div ref={wrapRef} style={{ position: "relative" }}>
      <button className="nav-link" onClick={() => { setOpen((o) => !o); if (!open) refresh(); }}
        data-testid="notification-bell"
        style={{ background: "none", border: "none", position: "relative", cursor: "pointer", padding: 4 }}>
        <Bell size={20} weight={count > 0 ? "fill" : "regular"} />
        {count > 0 && (
          <span data-testid="notification-badge"
            style={{ position: "absolute", top: -2, right: -4, background: "var(--primary)",
              color: "#fff", borderRadius: 999, fontSize: 10, minWidth: 16, height: 16,
              lineHeight: "16px", textAlign: "center", padding: "0 3px", fontWeight: 700 }}>
            {count > 99 ? "99+" : count}
          </span>
        )}
      </button>

      {open && (
        <div data-testid="notification-dropdown"
          style={{ position: "absolute", right: 0, top: 34, width: 340, maxHeight: 440,
            overflowY: "auto", background: "#fff", border: "1px solid var(--line, #e5e5e5)",
            borderRadius: 12, boxShadow: "0 12px 32px rgba(0,0,0,0.14)", zIndex: 50 }}>
          <div className="row" style={{ justifyContent: "space-between", padding: "12px 14px",
            borderBottom: "1px solid var(--line, #eee)", position: "sticky", top: 0, background: "#fff" }}>
            <span style={{ fontWeight: 700 }}>Notifications</span>
            {count > 0 && (
              <button className="nav-link" onClick={markAll} data-testid="notification-mark-all"
                style={{ background: "none", border: "none", cursor: "pointer", fontSize: 12, color: "var(--primary)" }}>
                Mark all read
              </button>
            )}
          </div>
          {items.length === 0 ? (
            <div className="hint" style={{ padding: 20 }} data-testid="notification-empty">You're all caught up.</div>
          ) : (
            items.map((n) => (
              <button key={n.id} onClick={() => openNotif(n)}
                data-testid={`notification-item-${n.id}`}
                style={{ display: "block", width: "100%", textAlign: "left", padding: "10px 14px",
                  border: "none", borderBottom: "1px solid var(--line, #f2f2f2)", cursor: "pointer",
                  background: n.read ? "#fff" : "var(--bg-soft, #f7f7f7)" }}>
                <div style={{ fontWeight: n.read ? 500 : 700, fontSize: 13 }}>{n.title}</div>
                <div className="hint" style={{ fontSize: 12, marginTop: 2 }}>{n.body}</div>
                <div className="hint" style={{ fontSize: 10, marginTop: 3 }}>{fmt(n.created_at)}</div>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
}
