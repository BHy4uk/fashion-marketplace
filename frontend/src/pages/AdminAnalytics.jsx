import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { CurrencyCircleDollar, ShoppingBag, Users, Package, ShieldWarning } from "@phosphor-icons/react";
import api from "../lib/api";

const money = (minor) =>
  `₴${((minor || 0) / 100).toLocaleString("en-US", { maximumFractionDigits: 0 })}`;

function Stat({ icon, label, value, sub, testid }) {
  return (
    <div className="panel" data-testid={testid} style={{ flex: "1 1 180px", minWidth: 180 }}>
      <div className="row" style={{ gap: 8, color: "var(--text-2)", marginBottom: 10 }}>
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
          <div style={{ flex: 1, background: "var(--subtle)", height: 10, borderRadius: 4 }}>
            <div style={{ width: `${(v / max) * 100}%`, height: "100%",
              background: "var(--text)", borderRadius: 4 }} />
          </div>
          <span style={{ fontWeight: 600, width: 40, textAlign: "right" }}>{v}</span>
        </div>
      ))}
    </div>
  );
}

export default function AdminAnalytics() {
  const { t } = useTranslation("analytics");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(false);

  useEffect(() => {
    api.get("/analytics/marketplace").then((r) => setData(r.data))
      .catch(() => setErr(true)).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="container" style={{ padding: 80 }}><div className="spin" /></div>;
  if (err) return <div className="container empty" style={{ marginTop: 40 }} data-testid="admin-analytics-forbidden">{t("admin.error.forbidden")}</div>;
  if (!data) return null;

  const g = data.gmv, o = data.orders, ts = data.trust_safety;

  return (
    <div className="container" style={{ paddingTop: 28, paddingBottom: 80 }}>

      {/* Header */}
      <div className="row" style={{ justifyContent: "space-between", alignItems: "flex-start", marginBottom: 32 }}>
        <div>
          <span className="overline" style={{ color: "var(--muted)" }}>{t("admin.overline")}</span>
          <h1 style={{ fontSize: 26, fontWeight: 700, letterSpacing: "-0.02em", margin: "6px 0 0" }}>
            {t("admin.heading")}
          </h1>
        </div>
        <Link to="/admin/moderation" className="btn btn-sm" data-testid="analytics-to-moderation">{t("admin.moderationButton")}</Link>
      </div>

      {/* KPI grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, marginBottom: 16 }}
        data-testid="admin-analytics-cards">
        <Stat testid="stat-gmv" icon={<CurrencyCircleDollar size={18} weight="bold" />}
          label={t("admin.stat.gmv")} value={money(g.total)} sub={`${money(g.completed_value)} ${t("admin.stat.completed")}`} />
        <Stat testid="stat-fees" icon={<CurrencyCircleDollar size={18} weight="bold" />}
          label={t("admin.stat.platformFees")} value={money(g.platform_fees)} sub={t("admin.stat.fromCompleted")} />
        <Stat testid="stat-total-orders" icon={<ShoppingBag size={18} weight="bold" />}
          label={t("admin.stat.orders")} value={o.total} sub={`${o.by_status.Completed || 0} ${t("admin.stat.completed")}`} />
        <Stat testid="stat-users" icon={<Users size={18} weight="bold" />}
          label={t("admin.stat.users")} value={data.users.total} />
        <Stat testid="stat-listings" icon={<Package size={18} weight="bold" />}
          label={t("admin.stat.listings")} value={data.listings.total} />
        <Stat testid="stat-fraud" icon={<ShieldWarning size={18} weight="bold" />}
          label={t("admin.stat.fraudSignals")} value={ts.ai_fraud_signals} sub={`${ts.open_cases} ${t("admin.stat.openCases")}`} />
      </div>

      {/* Charts row */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
        <div className="panel" data-testid="orders-by-status">
          <span className="overline" style={{ color: "var(--muted)" }}>{t("admin.section.ordersByStatus")}</span>
          <Bars data={o.by_status} testid="orders-status-bars" />
        </div>
        <div className="panel" data-testid="listings-by-state">
          <span className="overline" style={{ color: "var(--muted)" }}>{t("admin.section.listingsByState")}</span>
          <Bars data={data.listings.by_state} testid="listings-state-bars" />
        </div>
      </div>

      {/* Top lists */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        <div className="panel" data-testid="top-brands">
          <span className="overline" style={{ color: "var(--muted)" }}>{t("admin.section.topBrands")}</span>
          <div style={{ marginTop: 12 }}>
            {data.top_brands.map((b) => (
              <div key={b.value} className="row" style={{ justifyContent: "space-between", padding: "8px 0", borderBottom: "1px solid var(--border)" }}>
                <span style={{ fontSize: 13 }}>{b.value}</span>
                <span style={{ fontWeight: 600, fontSize: 13 }}>{b.count}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="panel" data-testid="top-categories">
          <span className="overline" style={{ color: "var(--muted)" }}>{t("admin.section.topCategories")}</span>
          <div style={{ marginTop: 12 }}>
            {data.top_categories.map((c) => (
              <div key={c.value} className="row" style={{ justifyContent: "space-between", padding: "8px 0", borderBottom: "1px solid var(--border)" }}>
                <span style={{ fontSize: 13 }}>{c.value}</span>
                <span style={{ fontWeight: 600, fontSize: 13 }}>{c.count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
