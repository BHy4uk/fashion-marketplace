import React, { useState, useEffect, useRef, useCallback } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { MagnifyingGlass, Clock, X, Tag, Folder, ArrowRight } from "@phosphor-icons/react";
import { AnimatePresence, motion } from "framer-motion";
import api, { formatPrice } from "../lib/api";

// ─── constants ───────────────────────────────────────────────────────────────

const POPULAR_BRANDS = [
  "Stone Island", "Maison Margiela", "Rick Owens", "Acne Studios",
  "Carhartt WIP", "Nike", "New Balance", "Prada",
];
const RECENT_KEY = "archive_recent_searches";
const MAX_RECENT = 8;
const DEBOUNCE_MS = 200;

const COND_SHORT = {
  BRAND_NEW: "New", LIKE_NEW: "Like New", GENTLY_USED: "Gently",
  USED: "Used", WELL_WORN: "Worn",
};

// ─── helpers ─────────────────────────────────────────────────────────────────

function useDebounce(val, ms) {
  const [dv, setDv] = useState(val);
  useEffect(() => {
    const t = setTimeout(() => setDv(val), ms);
    return () => clearTimeout(t);
  }, [val, ms]);
  return dv;
}

function getRecent() {
  try { return JSON.parse(localStorage.getItem(RECENT_KEY) || "[]"); } catch { return []; }
}
function pushRecent(q) {
  if (!q.trim()) return;
  const next = [q, ...getRecent().filter(s => s !== q)].slice(0, MAX_RECENT);
  localStorage.setItem(RECENT_KEY, JSON.stringify(next));
}
function dropRecent(q) {
  localStorage.setItem(RECENT_KEY, JSON.stringify(getRecent().filter(s => s !== q)));
}

// Simple in-memory query cache so re-opening dropdown is instant
const cache = new Map();

function ThumbImg({ src, alt }) {
  const [err, setErr] = useState(false);
  if (!src || err) {
    return (
      <div style={{
        width: 48, height: 48, background: "var(--subtle)", borderRadius: 6,
        display: "grid", placeItems: "center",
        fontSize: 8, fontWeight: 700, color: "var(--muted)", letterSpacing: "0.05em",
        flexShrink: 0,
      }}>
        ARC
      </div>
    );
  }
  return (
    <img
      src={src} alt={alt}
      onError={() => setErr(true)}
      style={{ width: 48, height: 48, objectFit: "cover", borderRadius: 6, flexShrink: 0 }}
    />
  );
}

// ─── main component ───────────────────────────────────────────────────────────

export default function SearchBar() {
  const navigate = useNavigate();
  const { t } = useTranslation("marketplace");
  const containerRef = useRef(null);
  const inputRef = useRef(null);

  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [products, setProducts] = useState([]);
  const [brandMatches, setBrandMatches] = useState([]);
  const [catMatches, setCatMatches] = useState([]);
  const [allCats, setAllCats] = useState([]);
  const [recent, setRecent] = useState([]);
  const [activeIdx, setActiveIdx] = useState(-1);

  const dq = useDebounce(query, DEBOUNCE_MS);

  // Load categories once
  useEffect(() => {
    api.get("/taxonomy/categories")
      .then(r => setAllCats(r.data.categories || []))
      .catch(() => {});
  }, []);

  // Click outside closes
  useEffect(() => {
    const handler = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  // Fetch suggestions when debounced query changes
  useEffect(() => {
    if (!dq.trim() || dq.length < 2) {
      setProducts([]);
      setBrandMatches([]);
      setCatMatches([]);
      setLoading(false);
      return;
    }

    const cacheKey = dq.toLowerCase();
    if (cache.has(cacheKey)) {
      const hit = cache.get(cacheKey);
      setProducts(hit.products);
      setBrandMatches(hit.brands);
      setCatMatches(hit.cats);
      return;
    }

    setLoading(true);
    const controller = new AbortController();

    Promise.all([
      api.get(`/listings?q=${encodeURIComponent(dq)}&page_size=5`, { signal: controller.signal }),
      api.get(`/taxonomy/brands?q=${encodeURIComponent(dq)}`, { signal: controller.signal }),
    ])
      .then(([listRes, brandRes]) => {
        const prods = listRes.data.items || [];
        const brands = (brandRes.data.brands || []).slice(0, 4);
        const ql = dq.toLowerCase();
        const cats = allCats
          .filter(c => c.name.toLowerCase().includes(ql) || c.slug.includes(ql))
          .slice(0, 3);

        setProducts(prods);
        setBrandMatches(brands);
        setCatMatches(cats);
        cache.set(cacheKey, { products: prods, brands, cats });
      })
      .catch(() => {})
      .finally(() => setLoading(false));

    return () => controller.abort();
  }, [dq, allCats]);

  // Refresh recent whenever dropdown opens
  useEffect(() => {
    if (open) setRecent(getRecent());
  }, [open]);

  // Build flat navigable item list for keyboard nav
  const hasQuery = dq.trim().length >= 2;
  const items = hasQuery
    ? [
        ...products.map(p => ({ kind: "product", p })),
        ...brandMatches.map(b => ({ kind: "brand", b })),
        ...catMatches.map(c => ({ kind: "cat", c })),
      ]
    : [
        ...recent.map(r => ({ kind: "recent", r })),
        ...POPULAR_BRANDS.map(b => ({ kind: "popular", b })),
      ];

  const resetActiveIdx = useCallback(() => setActiveIdx(-1), []);

  const handleKeyDown = (e) => {
    if (!open) { if (e.key !== "Escape") setOpen(true); return; }

    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIdx(i => Math.min(i + 1, items.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIdx(i => Math.max(i - 1, -1));
    } else if (e.key === "Escape") {
      setOpen(false);
      setActiveIdx(-1);
      inputRef.current?.blur();
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (activeIdx >= 0 && items[activeIdx]) {
        selectItem(items[activeIdx]);
      } else {
        submitSearch(query);
      }
    } else if (e.key === "Tab") {
      setOpen(false);
    }
  };

  const selectItem = (item) => {
    setOpen(false);
    setActiveIdx(-1);
    if (item.kind === "product") {
      pushRecent(query);
      navigate(`/listing/${item.p.slug || item.p.id}`);
    } else if (item.kind === "brand") {
      pushRecent(item.b);
      setQuery(item.b);
      navigate(`/shop?brand=${encodeURIComponent(item.b)}`);
    } else if (item.kind === "cat") {
      navigate(`/shop?category=${encodeURIComponent(item.c.slug)}`);
    } else if (item.kind === "recent") {
      setQuery(item.r);
      submitSearch(item.r);
    } else if (item.kind === "popular") {
      setQuery(item.b);
      navigate(`/shop?brand=${encodeURIComponent(item.b)}`);
    }
  };

  const submitSearch = (q) => {
    if (!q.trim()) return;
    pushRecent(q.trim());
    setOpen(false);
    navigate(`/shop?q=${encodeURIComponent(q.trim())}`);
    setQuery(q.trim());
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    submitSearch(query);
  };

  const showEmpty = open && !hasQuery;
  const showResults = open && hasQuery;
  const showDropdown = open && (showEmpty ? (recent.length > 0 || true) : true);

  let flatIdx = 0;

  return (
    <div className="search-wrap" ref={containerRef}>
      <form className="search-form" onSubmit={handleSubmit} role="search">
        <MagnifyingGlass
          size={16}
          className="search-icon"
          style={{ color: open ? "var(--text)" : "var(--text-2)" }}
        />
        <input
          ref={inputRef}
          type="text"
          className="search-input"
          data-testid="nav-search-input"
          placeholder={t("search.placeholder")}
          value={query}
          autoComplete="off"
          onChange={(e) => { setQuery(e.target.value); setActiveIdx(-1); }}
          onFocus={() => setOpen(true)}
          onKeyDown={handleKeyDown}
          aria-expanded={open}
          aria-autocomplete="list"
          aria-controls="search-listbox"
        />
        {query && (
          <button
            type="button"
            className="search-clear"
            onClick={() => { setQuery(""); resetActiveIdx(); inputRef.current?.focus(); }}
            aria-label="Clear search"
          >
            <X size={13} weight="bold" />
          </button>
        )}
      </form>

      <AnimatePresence>
        {showDropdown && (
          <motion.div
            id="search-listbox"
            className="search-dropdown"
            role="listbox"
            initial={{ opacity: 0, y: -6, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -6, scale: 0.98 }}
            transition={{ duration: 0.15, ease: [0.2, 0, 0, 1] }}
          >
            {/* ── Empty state ── */}
            {showEmpty && (
              <>
                {recent.length > 0 && (
                  <div className="search-section">
                    <div className="search-group-label">{t("search.recentSearches")}</div>
                    {recent.map((r, i) => {
                      const idx = flatIdx++;
                      return (
                        <div
                          key={r}
                          className={`search-item ${activeIdx === idx ? "search-item--active" : ""}`}
                          role="option"
                          aria-selected={activeIdx === idx}
                          onMouseEnter={() => setActiveIdx(idx)}
                          onClick={() => { setQuery(r); submitSearch(r); }}
                        >
                          <Clock size={14} style={{ color: "var(--muted)", flexShrink: 0 }} />
                          <span style={{ flex: 1, fontSize: 14 }}>{r}</span>
                          <button
                            className="search-remove-recent"
                            onClick={(e) => {
                              e.stopPropagation();
                              dropRecent(r);
                              setRecent(getRecent());
                            }}
                            aria-label={`Remove ${r}`}
                          >
                            <X size={11} weight="bold" />
                          </button>
                        </div>
                      );
                    })}
                  </div>
                )}

                <div className="search-section">
                  <div className="search-group-label">{t("search.popular")}</div>
                  <div className="search-brand-chips">
                    {POPULAR_BRANDS.map((b, i) => {
                      const idx = flatIdx++;
                      return (
                        <button
                          key={b}
                          className={`search-brand-chip ${activeIdx === idx ? "search-item--active" : ""}`}
                          onMouseEnter={() => setActiveIdx(idx)}
                          onClick={() => { setQuery(b); navigate(`/shop?brand=${encodeURIComponent(b)}`); setOpen(false); }}
                        >
                          {b}
                        </button>
                      );
                    })}
                  </div>
                </div>
              </>
            )}

            {/* ── Query results ── */}
            {showResults && loading && (
              <div className="search-section">
                {[1, 2, 3].map(i => (
                  <div key={i} className="search-skeleton">
                    <div className="search-skeleton-thumb" />
                    <div style={{ flex: 1 }}>
                      <div className="search-skeleton-line" style={{ width: "60%", marginBottom: 6 }} />
                      <div className="search-skeleton-line" style={{ width: "40%" }} />
                    </div>
                  </div>
                ))}
              </div>
            )}

            {showResults && !loading && products.length === 0 && brandMatches.length === 0 && catMatches.length === 0 && (
              <div className="search-empty">
                <MagnifyingGlass size={24} style={{ color: "var(--muted)", marginBottom: 8 }} />
                <p style={{ fontSize: 14, color: "var(--text-2)", margin: 0 }}>{t("search.noResults", { query: dq })}</p>
                <p style={{ fontSize: 12, color: "var(--muted)", margin: "4px 0 0" }}>Try a different spelling or brand name</p>
              </div>
            )}

            {showResults && !loading && products.length > 0 && (
              <div className="search-section">
                <div className="search-group-label">{t("search.items")}</div>
                {products.map((p) => {
                  const idx = flatIdx++;
                  const a = p.attributes || {};
                  const thumb = p.images?.[0]?.url;
                  const condLabel = COND_SHORT[a.condition];
                  return (
                    <Link
                      key={p.id}
                      to={`/listing/${p.slug || p.id}`}
                      className={`search-item search-item--product ${activeIdx === idx ? "search-item--active" : ""}`}
                      role="option"
                      aria-selected={activeIdx === idx}
                      onMouseEnter={() => setActiveIdx(idx)}
                      onClick={() => { pushRecent(query); setOpen(false); }}
                    >
                      <ThumbImg src={thumb} alt={p.title} />
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontSize: 14, fontWeight: 500, color: "var(--text)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                          {p.title}
                        </div>
                        <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 2 }}>
                          {a.brand && <span>{a.brand}</span>}
                          {a.size && <span> · {a.size}</span>}
                          {condLabel && <span> · {condLabel}</span>}
                        </div>
                      </div>
                      {p.price && (
                        <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text)", flexShrink: 0 }}>
                          {formatPrice(p.price)}
                        </div>
                      )}
                    </Link>
                  );
                })}
                <button
                  className="search-view-all"
                  onClick={() => submitSearch(query)}
                >
                  View all results for "{dq}"
                  <ArrowRight size={13} weight="bold" />
                </button>
              </div>
            )}

            {showResults && !loading && brandMatches.length > 0 && (
              <div className="search-section">
                <div className="search-group-label">{t("search.brands")}</div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6, padding: "4px 12px 8px" }}>
                  {brandMatches.map((b) => {
                    const idx = flatIdx++;
                    return (
                      <button
                        key={b}
                        className={`search-brand-chip ${activeIdx === idx ? "search-item--active" : ""}`}
                        onMouseEnter={() => setActiveIdx(idx)}
                        onClick={() => { navigate(`/shop?brand=${encodeURIComponent(b)}`); setOpen(false); }}
                      >
                        <Tag size={11} /> {b}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {showResults && !loading && catMatches.length > 0 && (
              <div className="search-section">
                <div className="search-group-label">{t("search.categories")}</div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6, padding: "4px 12px 8px" }}>
                  {catMatches.map((c) => {
                    const idx = flatIdx++;
                    return (
                      <button
                        key={c.slug}
                        className={`search-brand-chip ${activeIdx === idx ? "search-item--active" : ""}`}
                        onMouseEnter={() => setActiveIdx(idx)}
                        onClick={() => { navigate(`/shop?category=${encodeURIComponent(c.slug)}`); setOpen(false); }}
                      >
                        <Folder size={11} /> {c.name}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
