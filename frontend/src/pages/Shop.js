import React, { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { X } from "@phosphor-icons/react";
import api from "../lib/api";
import ProductCard from "../components/ProductCard";

export default function Shop() {
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
    <div className="container" style={{ paddingTop: 24, paddingBottom: 40 }}>
      <div className="section-head">
        <h2 data-testid="shop-heading">{q ? `“${q}”` : "All items"}</h2>
        <div className="row" style={{ gap: 10 }}>
          <span className="overline" data-testid="shop-count">{data.total} results</span>
          <select value={sort} onChange={(e) => setParam("sort", e.target.value)}
            data-testid="shop-sort" style={{ width: "auto" }}>
            <option value="newest">Newest</option>
            <option value="price_asc">Price: Low → High</option>
            <option value="price_desc">Price: High → Low</option>
          </select>
        </div>
      </div>

      {activeFilters.length > 0 && (
        <div className="toolbar" data-testid="shop-active-filters">
          {activeFilters.map((k) => (
            <span key={k} className="chip">
              {params.get(k)}
              <button onClick={() => setParam(k, null)} data-testid={`remove-filter-${k}`}>
                <X size={12} />
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
                <h4>{field}</h4>
                {opts.map((o) => (
                  <div key={o.value}
                    className={`facet-item ${params.get(field) === String(o.value) ? "active" : ""}`}
                    onClick={() => setParam(field, String(o.value))}
                    data-testid={`facet-${field}-${o.value}`}>
                    <span>{o.value}</span><span>{o.count}</span>
                  </div>
                ))}
              </div>
            );
          })}
        </aside>

        <div>
          {loading ? (
            <div style={{ padding: 60 }}><div className="spin" /></div>
          ) : data.items.length === 0 ? (
            <div className="empty" data-testid="shop-empty">No items match your search.</div>
          ) : (
            <div className="grid grid-products" data-testid="shop-grid">
              {data.items.map((l) => <ProductCard key={l.id} listing={l} />)}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
