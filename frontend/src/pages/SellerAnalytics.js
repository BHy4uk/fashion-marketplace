import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ChartLineUp, Package, CurrencyCircleDollar, Handshake, Star, Vault } from "@phosphor-icons/react";
import api from "../lib/api";

const money = (minor) =>
  `₴${((minor || 0) / 100).toLocaleString("en-US", { maximumFractionDigits: 0 })}`;

function Stat({ icon, label, value, sub, testid }) {
  return (
    <div className="panel" data-testid={testid} style={{ flex: "1 1 180px", minWidth: 180 }}>
      <div className="row" style={{ gap: 8, color: "var(--primary)", marginBottom: 10 }}>
        {icon}<span className="overline">{label}</span>
      </div>
      <div className="heading" style={{ fontSize: 30 }}>{value}</div>
      {sub && <div className="hint" style={{ marginTop: 4 }}>{sub}</div>}
    </div>
  );
}

export default function SellerAnalytics() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/analytics/seller").then((r) => setData(r.data)).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="container" style={{ padding: 80 }}><div className="spin" /></div>;
  if (!data) return <div className="container empty" style={{ marginTop: 40 }}>No analytics available.</div>;

  const s = data.sales, l = data.listings, o = data.offers, r = data.reputation;
  const acceptRate = o.received ? Math.round((o.accepted / o.received) * 100) : 0;

  return (
    <div className="container" style={{ paddingTop: 24, paddingBottom: 60 }}>
      <div className="row" style={{ justifyContent: "space-between", alignItems: "flex-end", marginBottom: 20 }}>
        <div>
          <span className="overline">Seller analytics</span>
          <h1 style={{ fontSize: 26, margin: "6px 0" }}>Your performance</h1>
        </div>
        <Link to="/dashboard" className="btn btn-sm" data-testid="analytics-to-dashboard">← Dashboard</Link>
      </div>

      <div className="row" style={{ gap: 16, flexWrap: "wrap", marginBottom: 16 }} data-testid="seller-analytics-cards">
        <Stat testid="stat-net-revenue" icon={<CurrencyCircleDollar size={18} weight="bold" />}
          label="Net revenue" value={money(s.net_revenue)} sub={`${s.completed} completed orders`} />
        <Stat testid="stat-pending-payout" icon={<Vault size={18} weight="bold" />}
          label="Pending payout" value={money(data.escrow.pending_payout)} sub="held in escrow" />
        <Stat testid="stat-active-listings" icon={<Package size={18} weight="bold" />}
          label="Active listings" value={l.active} sub={`${l.total} total`} />
        <Stat testid="stat-orders" icon={<ChartLineUp size={18} weight="bold" />}
          label="Sales" value={s.orders} sub={`${money(s.platform_fees)} platform fees`} />
        <Stat testid="stat-offers" icon={<Handshake size={18} weight="bold" />}
          label="Offers received" value={o.received} sub={`${acceptRate}% accepted`} />
        <Stat testid="stat-rating" icon={<Star size={18} weight="fill" />}
          label="Rating" value={r.average_rating || "—"} sub={`${r.reviews} reviews`} />
      </div>

      <div className="panel" data-testid="listings-breakdown">
        <span className="overline">Listings by state</span>
        <div className="row" style={{ gap: 20, flexWrap: "wrap", marginTop: 12 }}>
          {Object.keys(l.by_state).length === 0 ? (
            <span className="hint">No listings yet.</span>
          ) : Object.entries(l.by_state).map(([state, n]) => (
            <div key={state}>
              <div className="heading" style={{ fontSize: 22 }}>{n}</div>
              <span className="overline">{state}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
