import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ChartLineUp, Package, CurrencyCircleDollar, Handshake, Star, Vault } from "@phosphor-icons/react";
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

export default function SellerAnalytics() {
  const { t } = useTranslation("analytics");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/analytics/seller").then((r) => setData(r.data)).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="container" style={{ padding: 80 }}><div className="spin" /></div>;
  if (!data) return <div className="container empty" style={{ marginTop: 40 }}>{t("seller.error.noData")}</div>;

  const s = data.sales, l = data.listings, o = data.offers, r = data.reputation;
  const acceptRate = o.received ? Math.round((o.accepted / o.received) * 100) : 0;

  return (
    <div className="container" style={{ paddingTop: 28, paddingBottom: 80 }}>

      {/* Header */}
      <div className="row" style={{ justifyContent: "space-between", alignItems: "flex-start", marginBottom: 32 }}>
        <div>
          <span className="overline" style={{ color: "var(--muted)" }}>{t("seller.overline")}</span>
          <h1 style={{ fontSize: 26, fontWeight: 700, letterSpacing: "-0.02em", margin: "6px 0 0" }}>
            {t("seller.heading")}
          </h1>
        </div>
        <Link to="/dashboard" className="btn btn-sm" data-testid="analytics-to-dashboard">{t("seller.backButton")}</Link>
      </div>

      {/* KPI grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, marginBottom: 16 }}
        data-testid="seller-analytics-cards">
        <Stat testid="stat-net-revenue" icon={<CurrencyCircleDollar size={18} weight="bold" />}
          label={t("seller.stat.netRevenue")} value={money(s.net_revenue)} sub={`${s.completed} ${t("seller.stat.completedOrders")}`} />
        <Stat testid="stat-pending-payout" icon={<Vault size={18} weight="bold" />}
          label={t("seller.stat.pendingPayout")} value={money(data.escrow.pending_payout)} sub={t("seller.stat.heldInEscrow")} />
        <Stat testid="stat-active-listings" icon={<Package size={18} weight="bold" />}
          label={t("seller.stat.activeListings")} value={l.active} sub={`${l.total} ${t("seller.stat.total")}`} />
        <Stat testid="stat-orders" icon={<ChartLineUp size={18} weight="bold" />}
          label={t("seller.stat.sales")} value={s.orders} sub={`${money(s.platform_fees)} ${t("seller.stat.platformFees")}`} />
        <Stat testid="stat-offers" icon={<Handshake size={18} weight="bold" />}
          label="Offers received" value={o.received} sub={`${acceptRate}% accepted`} />
        <Stat testid="stat-rating" icon={<Star size={18} weight="fill" />}
          label="Rating" value={r.average_rating || "—"} sub={`${r.reviews} reviews`} />
      </div>

      {/* Listings breakdown */}
      <div className="panel" data-testid="listings-breakdown">
        <span className="overline" style={{ color: "var(--muted)" }}>Listings by state</span>
        <div style={{ display: "flex", gap: 32, flexWrap: "wrap", marginTop: 16 }}>
          {Object.keys(l.by_state).length === 0 ? (
            <span className="hint">No listings yet.</span>
          ) : Object.entries(l.by_state).map(([state, n]) => (
            <div key={state}>
              <div style={{ fontSize: 28, fontWeight: 700, letterSpacing: "-0.03em", lineHeight: 1 }}>{n}</div>
              <span className="overline" style={{ display: "block", marginTop: 6, color: "var(--muted)" }}>{state}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
