import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { CurrencyCircleDollar, ShoppingBag, Users, Package, ShieldWarning } from "@phosphor-icons/react";
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

function Bars({ data, testid }) {
  const max = Math.max(1, ...Object.values(data));
  return (
    <div data-testid={testid} style={{ marginTop: 12 }}>
      {Object.entries(data).map(([k, v]) => (
        <div key={k} className="row" style={{ gap: 12, marginBottom: 8, alignItems: "center" }}>
          <span className="overline" style={{ width: 140 }}>{k}</span>
          <div style={{ flex: 1, background: "#f0f0f0", height: 10, borderRadius: 6 }}>
            <div style={{ width: `${(v / max) * 100}%`, height: "100%",
              background: "var(--primary)", borderRadius: 6 }} />
          </div>
          <span style={{ fontWeight: 600, width: 40, textAlign: "right" }}>{v}</span>
        </div>
      ))}
    </div>
  );
}

export default function AdminAnalytics() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(false);

  useEffect(() => {
    api.get("/analytics/marketplace").then((r) => setData(r.data))
      .catch(() => setErr(true)).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="container" style={{ padding: 80 }}><div className="spin" /></div>;
  if (err) return <div className="container empty" style={{ marginTop: 40 }} data-testid="admin-analytics-forbidden">Staff access only.</div>;
  if (!data) return null;

  const g = data.gmv, o = data.orders, ts = data.trust_safety;

  return (
    <div className="container" style={{ paddingTop: 24, paddingBottom: 60 }}>
      <div className="row" style={{ justifyContent: "space-between", alignItems: "flex-end", marginBottom: 20 }}>
        <div>
          <span className="overline">Marketplace analytics</span>
          <h1 style={{ fontSize: 26, margin: "6px 0" }}>Platform overview</h1>
        </div>
        <Link to="/admin/moderation" className="btn btn-sm" data-testid="analytics-to-moderation">Moderation →</Link>
      </div>

      <div className="row" style={{ gap: 16, flexWrap: "wrap", marginBottom: 16 }} data-testid="admin-analytics-cards">
        <Stat testid="stat-gmv" icon={<CurrencyCircleDollar size={18} weight="bold" />}
          label="GMV" value={money(g.total)} sub={`${money(g.completed_value)} completed`} />
        <Stat testid="stat-fees" icon={<CurrencyCircleDollar size={18} weight="bold" />}
          label="Platform fees" value={money(g.platform_fees)} sub="from completed orders" />
        <Stat testid="stat-total-orders" icon={<ShoppingBag size={18} weight="bold" />}
          label="Orders" value={o.total} sub={`${o.by_status.Completed || 0} completed`} />
        <Stat testid="stat-users" icon={<Users size={18} weight="bold" />}
          label="Users" value={data.users.total} />
        <Stat testid="stat-listings" icon={<Package size={18} weight="bold" />}
          label="Listings" value={data.listings.total} />
        <Stat testid="stat-fraud" icon={<ShieldWarning size={18} weight="bold" />}
          label="AI fraud signals" value={ts.ai_fraud_signals} sub={`${ts.open_cases} open cases`} />
      </div>

      <div className="row" style={{ gap: 16, flexWrap: "wrap" }}>
        <div className="panel" style={{ flex: "1 1 320px" }} data-testid="orders-by-status">
          <span className="overline">Orders by status</span>
          <Bars data={o.by_status} testid="orders-status-bars" />
        </div>
        <div className="panel" style={{ flex: "1 1 320px" }} data-testid="listings-by-state">
          <span className="overline">Listings by state</span>
          <Bars data={data.listings.by_state} testid="listings-state-bars" />
        </div>
      </div>

      <div className="row" style={{ gap: 16, flexWrap: "wrap", marginTop: 16 }}>
        <div className="panel" style={{ flex: "1 1 320px" }} data-testid="top-brands">
          <span className="overline">Top brands</span>
          <div style={{ marginTop: 10 }}>
            {data.top_brands.map((b) => (
              <div key={b.value} className="row" style={{ justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid #f0f0f0" }}>
                <span>{b.value}</span><span style={{ fontWeight: 600 }}>{b.count}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="panel" style={{ flex: "1 1 320px" }} data-testid="top-categories">
          <span className="overline">Top categories</span>
          <div style={{ marginTop: 10 }}>
            {data.top_categories.map((c) => (
              <div key={c.value} className="row" style={{ justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid #f0f0f0" }}>
                <span>{c.value}</span><span style={{ fontWeight: 600 }}>{c.count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
