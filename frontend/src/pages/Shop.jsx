import React, { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { X } from "@phosphor-icons/react";
import { motion } from "framer-motion";
import { useTranslation } from "react-i18next";
import api from "../lib/api";
import ProductCard from "../components/ProductCard";
import { CONDITION_LABEL } from "../components/ProductCard";
import { ProductCardSkeleton } from "../components/Skeleton";
import { listVariants, listItemVariants } from "../lib/motion";

function formatFacetValue(field, value) {
  if (field === "condition") return CONDITION_LABEL[value] || value;
  return value;
}

export default function Shop() {
  const { t } = useTranslation("marketplace");
  const [params, setParams] = useSearchParams();
  const [data, setData] = useState({ items: [], total: 0, facets: {} });
  const [loading, setLoading] = useState(true);

  const q = params.get("q") || "";
  const sort = params.get("sort") || "newest";

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await api.get(`/listings?${params.toString()}`);
      setData(r.data);
    } finally {
      setLoading(false);
    }
  }, [params]);

  useEffect(() => { load(); }, [load]);

  const setParam = (k, v) => {
    const next = new URLSearchParams(params);
    if (v == null || next.get(k) === v) next.delete(k);
    else next.set(k, v);
    next.delete("page");
    setParams(next);
  };

  const activeFilters = ["brand", "category", "condition", "size"].filter((k) => params.get(k));

  return (
    <div className="container" style={{ paddingTop: 28, paddingBottom: 80 }}>
      <div className="section-head">
        <h2 data-testid="shop-heading">{q ? `"${q}"` : t("shop.heading")}</h2>
        <div className="row" style={{ gap: 10 }}>
          <span className="overline" data-testid="shop-count">{t("shop.resultCount", { count: data.total })}</span>
          <select value={sort} onChange={(e) => setParam("sort", e.target.value)}
            data-testid="shop-sort" style={{ width: "auto" }}>
            <option value="newest">{t("sort.newest")}</option>
            <option value="price_asc">{t("sort.priceAsc")}</option>
            <option value="price_desc">{t("sort.priceDesc")}</option>
          </select>
        </div>
      </div>

      {activeFilters.length > 0 && (
        <div className="toolbar" data-testid="shop-active-filters">
          {activeFilters.map((k) => (
            <span key={k} className="chip chip-active">
              {params.get(k)}
              <button onClick={() => setParam(k, null)} data-testid={`remove-filter-${k}`} aria-label={t("filter.removeAria", { key: k })}>
                <X size={11} weight="bold" />
              </button>
            </span>
          ))}
        </div>
      )}

      <div className="layout-2col">
        <aside data-testid="shop-facets">
          {["brand", "category", "condition", "size"].map((field) => {
            const opts = data.facets?.[field] || [];
            if (!opts.length) return null;
            return (
              <div className="facet" key={field}>
                <h4>{t(`facet.${field}`)}</h4>
                {opts.map((o) => (
                  <div key={o.value}
                    className={`facet-item ${params.get(field) === String(o.value) ? "active" : ""}`}
                    onClick={() => setParam(field, String(o.value))}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => e.key === "Enter" && setParam(field, String(o.value))}
                    data-testid={`facet-${field}-${o.value}`}>
                    <span>{formatFacetValue(field, o.value)}</span>
                    <span style={{ opacity: 0.4, fontSize: 11 }}>{o.count}</span>
                  </div>
                ))}
              </div>
            );
          })}
        </aside>

        <div>
          {loading ? (
            <div className="grid grid-products">
              {Array.from({ length: 12 }).map((_, i) => <ProductCardSkeleton key={i} />)}
            </div>
          ) : data.items.length === 0 ? (
            <div className="empty" data-testid="shop-empty">
              <span className="overline" style={{ display: "block", marginBottom: 8 }}>{t("empty.title")}</span>
              {t("empty.message")}
            </div>
          ) : (
            <motion.div
              className="grid grid-products"
              variants={listVariants}
              initial="hidden"
              animate="visible"
              key={params.toString()}
              data-testid="shop-grid"
            >
              {data.items.map((l) => (
                <motion.div key={l.id} variants={listItemVariants}>
                  <ProductCard listing={l} />
                </motion.div>
              ))}
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}
