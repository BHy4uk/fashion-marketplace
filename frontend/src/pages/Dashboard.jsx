import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { useTranslation } from "react-i18next";
import api, { formatPrice, apiError } from "../lib/api";
import { useAuth } from "../context/AuthContext";

const STATE_BADGE = {
  Published: "badge-solid", Draft: "badge", Reserved: "badge-primary",
  Sold: "badge", Archived: "badge",
};

const STATE_FILTERS = ["All", "Published", "Draft", "Sold", "Archived"];

export default function Dashboard() {
  const { user } = useAuth();
  const { t } = useTranslation("dashboard");
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stateFilter, setStateFilter] = useState("All");

  const load = () => {
    setLoading(true);
    api.get("/listings/mine").then((r) => setItems(r.data.items)).finally(() => setLoading(false));
  };
  useEffect(load, []);

  const remove = async (id) => {
    try {
      await api.delete(`/listings/${id}`);
      toast.success(t("toast.removed"));
      load();
    } catch (e) {
      toast.error(apiError(e));
    }
  };

  const rep = user?.reputation || {};
  const filtered = stateFilter === "All" ? items : items.filter((l) => l.state === stateFilter);

  return (
    <div className="container" style={{ paddingTop: 28, paddingBottom: 80 }}>

      {/* ── Header ──────────────────────────────────────────────── */}
      <div data-testid="dashboard-header" style={{ marginBottom: 40 }}>
        <div className="row" style={{ justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 16 }}>
          <div>
            <h1 style={{ fontSize: 28, fontWeight: 700, letterSpacing: "-0.02em" }}>
              {t("heading")}
            </h1>
          </div>
          <Link to="/sell" className="btn btn-primary" data-testid="dashboard-new-listing">
            {t("button.newListing")}
          </Link>
        </div>

        {/* KPI row */}
        <div style={{
          display: "grid", gridTemplateColumns: "repeat(3, auto) 1fr",
          gap: "24px 40px", marginTop: 28,
          borderTop: "1px solid var(--border)", paddingTop: 24,
        }}>
          {[
            [items.length, t("stat.listings")],
            [rep.average_rating ? `${rep.average_rating}★` : "—", t("stat.rating")],
            [rep.completed_reviews || 0, t("stat.reviews")],
          ].map(([val, label]) => (
            <div key={label}>
              <div style={{ fontSize: 28, fontWeight: 700, letterSpacing: "-0.03em", lineHeight: 1 }}>
                {val}
              </div>
              <span className="overline" style={{ display: "block", marginTop: 6 }}>{label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* State filter tabs */}
      <div className="toolbar">
        {["All", "Published", "Draft", "Sold", "Archived"].map((s) => (
          <button
            key={s}
            className={`chip ${stateFilter === s ? "chip-active" : ""}`}
            onClick={() => setStateFilter(s)}
          >
            {t(`filter.${s.toLowerCase()}`)}
            {s !== "All" && items.filter((l) => l.state === s).length > 0 && (
              <span style={{ opacity: 0.6, marginLeft: 2 }}>
                {items.filter((l) => l.state === s).length}
              </span>
            )}
          </button>
        ))}
      </div>

      {loading ? (
        <div style={{ padding: "40px 0", display: "flex", justifyContent: "center" }}>
          <div className="spin" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="empty" data-testid="dashboard-empty">
          {stateFilter === "All"
            ? <><div style={{ fontWeight: 600, marginBottom: 8 }}>{t("empty.title")}</div>
                <Link to="/sell" className="btn btn-primary btn-sm">{t("empty.action")}</Link></>
            : <div>{t("empty.byState", { state: stateFilter.toLowerCase() })}</div>
          }
        </div>
      ) : (
        <div className="grid grid-products" data-testid="dashboard-grid">
          {filtered.map((l) => (
            <div key={l.id} data-testid={`dashboard-item-${l.id}`}>
              <Link to={`/listing/${l.slug || l.id}`} className="product-img" style={{ display: "block" }}>
                {l.images?.[0]
                  ? <img src={l.images[0].url} alt={l.title} />
                  : <div className="img-fallback">{l.attributes?.brand || "ARCHIVE"}</div>
                }
              </Link>
              <div className="product-info">
                <div className="row" style={{ justifyContent: "space-between", alignItems: "flex-start" }}>
                  <span className="product-brand">{l.attributes?.brand || "—"}</span>
                  <span className={`badge ${STATE_BADGE[l.state] || "badge"}`}>{l.state}</span>
                </div>
                <div className="product-title">{l.title}</div>
                <div className="row" style={{ justifyContent: "space-between", alignItems: "center" }}>
                  <span className="product-price">{formatPrice(l.price)}</span>
                  <div className="row" style={{ gap: 6 }}>
                    <Link
                      to={`/edit/${l.id}`}
                      className="btn btn-sm"
                      style={{ fontSize: 11, padding: "4px 10px" }}
                    >
                      {t("button.edit")}
                    </Link>
                    {["Published", "Draft", "Ready", "Archived"].includes(l.state) && (
                      <button
                        className="btn btn-sm"
                        style={{ fontSize: 11, padding: "4px 10px", color: "var(--error)", border: "1px solid var(--border)" }}
                        onClick={() => remove(l.id)}
                        data-testid={`dashboard-archive-${l.id}`}
                      >
                        {t("button.remove")}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

