import React, { useEffect, useRef, useState } from "react";
import { useSearchParams, useNavigate, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle, Package, CreditCard, MapPin, ArrowLeft, CaretDown } from "@phosphor-icons/react";
import { toast } from "sonner";
import api, { formatPrice, apiError } from "../lib/api";
import { useAuth } from "../context/AuthContext";
import { slideUpVariants, DURATION, EASE } from "../lib/motion";
import { COUNTRIES } from "../lib/countries";

// Flag image component — uses flagcdn.com for cross-platform rendering (Windows-safe)
const FlagImg = ({ code, size = 20 }) => (
  <img
    src={`https://flagcdn.com/w${size}/${code.toLowerCase()}.png`}
    srcSet={`https://flagcdn.com/w${size * 2}/${code.toLowerCase()}.png 2x`}
    alt=""
    width={size}
    height={Math.round(size * 0.75)}
    loading="lazy"
    style={{ flexShrink: 0, borderRadius: 2 }}
  />
);

// ─── Step indicator ──────────────────────────────────────────────────────────
const STEPS_KEYS = ["step.review", "step.shipping", "step.payment", "step.confirmation"];

function StepBar({ current }) {
  const { t } = useTranslation("checkout");
  const STEPS = STEPS_KEYS.map(k => t(k));
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 0, marginBottom: 36 }}>
      {STEPS.map((label, i) => {
        const done = i < current;
        const active = i === current;
        return (
          <React.Fragment key={label}>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 6 }}>
              <div style={{
                width: 28, height: 28, borderRadius: "50%",
                border: `2px solid ${done || active ? "var(--text)" : "var(--border)"}`,
                background: done ? "var(--text)" : active ? "transparent" : "transparent",
                display: "flex", alignItems: "center", justifyContent: "center",
                transition: `all ${DURATION.normal}s`,
              }}>
                {done
                  ? <CheckCircle size={16} color="#fff" weight="fill" />
                  : <span style={{ fontSize: 11, fontWeight: 600, color: active ? "var(--text)" : "var(--muted)" }}>{i + 1}</span>
                }
              </div>
              <span style={{
                fontSize: 10, letterSpacing: "0.08em", textTransform: "uppercase",
                fontWeight: active ? 600 : 400,
                color: active ? "var(--text)" : done ? "var(--text-2)" : "var(--muted)",
              }}>{label}</span>
            </div>
            {i < STEPS.length - 1 && (
              <div style={{
                flex: 1, height: 1, margin: "0 8px", marginBottom: 22,
                background: done ? "var(--text)" : "var(--border)",
                transition: `background ${DURATION.normal}s`,
              }} />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}

// ─── Order summary sidebar ───────────────────────────────────────────────────
function OrderSummary({ listing, shippingCost = 0 }) {
  const { t } = useTranslation("checkout");
  if (!listing) return null;
  const price = listing.price || {};
  const itemTotal = price.amount || 0;
  const total = itemTotal + shippingCost;
  const currency = price.currency || "UAH";

  return (
    <div className="panel" style={{ padding: 24, position: "sticky", top: 88 }}>
      <div className="overline" style={{ color: "var(--muted)", marginBottom: 16 }}>{t("sidebar.orderSummary")}</div>

      {/* Item */}
      <div style={{ display: "flex", gap: 14, marginBottom: 20, paddingBottom: 20, borderBottom: "1px solid var(--border)" }}>
        <div style={{
          width: 64, height: 80, borderRadius: 8, background: "var(--canvas-2, #F0EFE9)",
          flexShrink: 0, overflow: "hidden", display: "flex", alignItems: "center", justifyContent: "center",
        }}>
          {listing.images?.[0]?.url
            ? <img src={listing.images[0].url} alt={listing.title} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            : <span style={{ fontSize: 9, color: "var(--muted)", letterSpacing: "0.05em" }}>{listing.attributes?.brand || "ARCHIVE"}</span>
          }
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          {listing.attributes?.brand && (
            <div className="overline" style={{ color: "var(--muted)", marginBottom: 2 }}>{listing.attributes.brand}</div>
          )}
          <div style={{ fontSize: 13, fontWeight: 600, lineHeight: 1.4, marginBottom: 4 }}
            title={listing.title}>
            {listing.title}
          </div>
          {listing.attributes?.size && (
            <div className="overline" style={{ color: "var(--muted)" }}>Size {listing.attributes.size}</div>
          )}
        </div>
      </div>

      {/* Totals */}
      <div className="stack" style={{ gap: 10 }}>
        <div className="row" style={{ justifyContent: "space-between" }}>
          <span style={{ fontSize: 13, color: "var(--text-2)" }}>{t("sidebar.item")}</span>
          <span style={{ fontSize: 13 }}>{formatPrice(price)}</span>
        </div>
        <div className="row" style={{ justifyContent: "space-between" }}>
          <span style={{ fontSize: 13, color: "var(--text-2)" }}>{t("sidebar.shipping")}</span>
          <span style={{ fontSize: 13, color: "var(--muted)" }}>{t("sidebar.shippingNote")}</span>
        </div>
        <div style={{ borderTop: "1px solid var(--border)", paddingTop: 10, marginTop: 2 }}>
          <div className="row" style={{ justifyContent: "space-between" }}>
            <span style={{ fontSize: 14, fontWeight: 700 }}>{t("sidebar.total")}</span>
            <span style={{ fontSize: 16, fontWeight: 700, letterSpacing: "-0.02em" }}>{formatPrice({ amount: total, currency })}</span>
          </div>
        </div>
      </div>

      {/* Trust signals */}
      <div className="stack" style={{ gap: 8, marginTop: 20, paddingTop: 20, borderTop: "1px solid var(--border)" }}>
        <div className="row" style={{ gap: 8 }}>
          <Package size={14} color="var(--muted)" />
          <span style={{ fontSize: 12, color: "var(--text-2)" }}>{t("trust.escrow")}</span>
        </div>
        <div className="row" style={{ gap: 8 }}>
          <CreditCard size={14} color="var(--muted)" />
          <span style={{ fontSize: 12, color: "var(--text-2)" }}>{t("trust.payment")}</span>
        </div>
      </div>
    </div>
  );
}

// ─── Step 0: Review ──────────────────────────────────────────────────────────
function ReviewStep({ listing, onNext }) {
  const { t } = useTranslation("checkout");
  return (
    <div className="panel" style={{ padding: 32 }}>
      <h2 style={{ fontSize: 18, fontWeight: 700, letterSpacing: "-0.02em", marginBottom: 6 }}>{t("review.heading")}</h2>
      <p style={{ fontSize: 13, color: "var(--text-2)", marginBottom: 24 }}>
        {t("review.description")}
      </p>

      <div style={{ display: "flex", gap: 20, marginBottom: 24, padding: "16px 0", borderTop: "1px solid var(--border)", borderBottom: "1px solid var(--border)" }}>
        <div style={{
          width: 96, height: 120, borderRadius: 8, background: "var(--canvas-2, #F0EFE9)",
          flexShrink: 0, overflow: "hidden", display: "flex", alignItems: "center", justifyContent: "center",
        }}>
          {listing?.images?.[0]?.url
            ? <img src={listing.images[0].url} alt={listing.title} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            : <span style={{ fontSize: 10, color: "var(--muted)" }}>{listing?.attributes?.brand || "ARCHIVE"}</span>
          }
        </div>
        <div>
          {listing?.attributes?.brand && (
            <div className="overline" style={{ color: "var(--muted)", marginBottom: 4 }}>{listing.attributes.brand}</div>
          )}
          <div style={{ fontSize: 15, fontWeight: 600, lineHeight: 1.4, marginBottom: 8 }}>{listing?.title}</div>
          <div className="row" style={{ gap: 6, flexWrap: "wrap", marginBottom: 10 }}>
            {listing?.attributes?.condition && <span className="badge badge-solid">{listing.attributes.condition}</span>}
            {listing?.attributes?.size && <span className="badge">Size {listing.attributes.size}</span>}
          </div>
          <div style={{ fontSize: 22, fontWeight: 700, letterSpacing: "-0.03em" }}>{formatPrice(listing?.price)}</div>
        </div>
      </div>

      <div style={{ background: "var(--canvas-2, #F5F4F0)", borderRadius: 8, padding: "12px 16px", marginBottom: 24 }}>
        <p style={{ fontSize: 12, color: "var(--text-2)", lineHeight: 1.7, margin: 0 }}>
          {t("review.terms")}
        </p>
      </div>

      <button className="btn btn-primary btn-block" onClick={onNext} style={{ height: 48 }}>
        {t("review.continueButton")}
      </button>
    </div>
  );
}

// ─── Country Select ──────────────────────────────────────────────────────────
function CountrySelect({ value, onChange, error }) {
  const { t } = useTranslation("checkout");
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [highlighted, setHighlighted] = useState(-1);
  const containerRef = useRef(null);
  const listRef = useRef(null);
  const searchRef = useRef(null);

  const filtered = search.trim()
    ? COUNTRIES.filter(c =>
        c.name.toLowerCase().includes(search.toLowerCase()) ||
        c.code.toLowerCase().startsWith(search.toLowerCase())
      )
    : COUNTRIES;

  const selected = COUNTRIES.find(c => c.code === value);

  useEffect(() => {
    const handler = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  useEffect(() => {
    if (highlighted >= 0 && listRef.current) {
      listRef.current.children[highlighted]?.scrollIntoView({ block: "nearest" });
    }
  }, [highlighted]);

  const openDropdown = () => {
    setOpen(true);
    setSearch("");
    setHighlighted(-1);
    setTimeout(() => searchRef.current?.focus(), 30);
  };

  const selectCountry = (c) => {
    onChange(c);
    setOpen(false);
    setSearch("");
    setHighlighted(-1);
  };

  const handleSearchKeyDown = (e) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlighted(i => Math.min(i + 1, filtered.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlighted(i => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (highlighted >= 0 && filtered[highlighted]) selectCountry(filtered[highlighted]);
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  };

  return (
    <div ref={containerRef} style={{ position: "relative" }}>
      <button
        type="button"
        onClick={openDropdown}
        aria-haspopup="listbox"
        aria-expanded={open}
        style={{
          width: "100%", height: 44, padding: "0 12px",
          border: `1px solid ${error ? "var(--error, #C0392B)" : "var(--border)"}`,
          borderRadius: "var(--radius-sm, 8px)",
          background: "var(--surface, #fff)", cursor: "pointer",
          display: "flex", alignItems: "center", justifyContent: "space-between",
          fontSize: 14, fontFamily: "inherit",
        }}
      >
        <span style={{ display: "flex", alignItems: "center", gap: 8, minWidth: 0, overflow: "hidden" }}>
          {selected ? (
            <>
              <FlagImg code={selected.code} />
              <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {selected.name}
              </span>
            </>
          ) : (
            <span style={{ color: "var(--muted)" }}>{t("address.selectCountry")}</span>
          )}
        </span>
        <CaretDown size={14} color="var(--muted)" style={{ flexShrink: 0, marginLeft: 8 }} />
      </button>

      {open && (
        <div style={{
          position: "absolute", top: "calc(100% + 4px)", left: 0, right: 0,
          background: "var(--surface, #fff)", border: "1px solid var(--border)",
          borderRadius: "var(--radius-sm, 8px)",
          boxShadow: "0 8px 24px rgba(0,0,0,0.1)", zIndex: 100,
          display: "flex", flexDirection: "column", maxHeight: 300,
        }}>
          <div style={{ padding: "8px 8px 4px", borderBottom: "1px solid var(--border)" }}>
            <input
              ref={searchRef}
              type="text"
              placeholder={t("address.searchCountries")}
              value={search}
              onChange={(e) => { setSearch(e.target.value); setHighlighted(0); }}
              onKeyDown={handleSearchKeyDown}
              style={{ margin: 0, fontSize: 13 }}
              aria-label={t("address.searchCountries")}
            />
          </div>
          <ul
            ref={listRef}
            role="listbox"
            style={{ overflowY: "auto", flex: 1, padding: "4px 0", margin: 0, listStyle: "none" }}
          >
            {filtered.length === 0 ? (
              <li style={{ padding: "10px 14px", fontSize: 13, color: "var(--muted)" }}>{t("address.noCountriesFound")}</li>
            ) : filtered.map((c, i) => (
              <li
                key={c.code}
                role="option"
                aria-selected={c.code === value}
                onClick={() => selectCountry(c)}
                onMouseEnter={() => setHighlighted(i)}
                style={{
                  padding: "8px 14px", fontSize: 13, cursor: "pointer",
                  display: "flex", alignItems: "center", gap: 10,
                  background: i === highlighted || c.code === value
                    ? "var(--canvas-2, #F5F4F0)" : "transparent",
                }}
              >
                <FlagImg code={c.code} />
                <span style={{ flex: 1 }}>{c.name}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

// ─── Phone Input ─────────────────────────────────────────────────────────────
function PhoneInput({ dialCode, dialCountry, onDialChange, number, onNumberChange, error }) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [highlighted, setHighlighted] = useState(-1);
  const containerRef = useRef(null);
  const listRef = useRef(null);
  const searchRef = useRef(null);

  const filtered = search.trim()
    ? COUNTRIES.filter(c =>
        c.name.toLowerCase().includes(search.toLowerCase()) ||
        c.dial.includes(search)
      )
    : COUNTRIES;

  useEffect(() => {
    const handler = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  useEffect(() => {
    if (highlighted >= 0 && listRef.current) {
      listRef.current.children[highlighted]?.scrollIntoView({ block: "nearest" });
    }
  }, [highlighted]);

  const openDropdown = () => {
    setOpen(true);
    setSearch("");
    setHighlighted(-1);
    setTimeout(() => searchRef.current?.focus(), 30);
  };

  const selectDial = (c) => {
    onDialChange(c);
    setOpen(false);
    setSearch("");
    setHighlighted(-1);
  };

  const handleSearchKeyDown = (e) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlighted(i => Math.min(i + 1, filtered.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlighted(i => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (highlighted >= 0 && filtered[highlighted]) selectDial(filtered[highlighted]);
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  };

  const [focused, setFocused] = useState(false);
  const borderColor = error ? "var(--error, #C0392B)" : focused ? "var(--text)" : "var(--border)";
  const sepColor = focused ? "var(--text-2, #4F4F4F)" : "var(--border)";

  return (
    <div ref={containerRef} style={{ position: "relative" }}>
      <div
        style={{
          display: "flex", alignItems: "stretch",
          border: `1px solid ${borderColor}`,
          borderRadius: "var(--radius-sm, 8px)",
          overflow: "hidden",
          background: "var(--surface, #fff)",
          transition: "border-color 0.12s",
        }}
      >
        <button
          type="button"
          onClick={openDropdown}
          aria-haspopup="listbox"
          aria-expanded={open}
          aria-label="Select dialing code"
          style={{
            height: 44, padding: "0 10px 0 12px",
            border: "none",
            borderRight: `1px solid ${sepColor}`,
            background: "transparent", cursor: "pointer",
            display: "flex", alignItems: "center", gap: 7,
            fontSize: 13, fontFamily: "inherit", whiteSpace: "nowrap", flexShrink: 0,
            transition: "border-color 0.12s",
          }}
        >
          {dialCountry
            ? <FlagImg code={dialCountry} />
            : <span style={{ display: "inline-block", width: 20, height: 15, borderRadius: 2, background: "var(--border, #E7E7E3)", flexShrink: 0 }} />
          }
          <span style={{ color: dialCode ? "var(--text)" : "var(--muted)", fontVariantNumeric: "tabular-nums", minWidth: 34 }}>
            {dialCode || "Code"}
          </span>
          <CaretDown size={11} color="var(--muted)" />
        </button>
        <input
          type="tel"
          name="phone_number"
          autoComplete="tel-national"
          placeholder="Phone number"
          value={number}
          onChange={(e) => onNumberChange(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          aria-invalid={!!error}
          style={{
            flex: 1, margin: 0, padding: "0 12px", height: 44,
            border: "none", outline: "none", boxShadow: "none",
            background: "transparent", borderRadius: 0,
            fontSize: 14, fontFamily: "inherit",
          }}
        />
      </div>

      {open && (
        <div style={{
          position: "absolute", top: "calc(100% + 4px)", left: 0,
          width: 300,
          background: "var(--surface, #fff)", border: "1px solid var(--border)",
          borderRadius: "var(--radius-sm, 8px)",
          boxShadow: "0 8px 24px rgba(0,0,0,0.1)", zIndex: 100,
          display: "flex", flexDirection: "column", maxHeight: 280,
        }}>
          <div style={{ padding: "8px 8px 4px", borderBottom: "1px solid var(--border)" }}>
            <input
              ref={searchRef}
              type="text"
              placeholder="Search countries…"
              value={search}
              onChange={(e) => { setSearch(e.target.value); setHighlighted(0); }}
              onKeyDown={handleSearchKeyDown}
              style={{ margin: 0, fontSize: 13 }}
              aria-label="Search dialing codes"
            />
          </div>
          <ul
            ref={listRef}
            role="listbox"
            style={{ overflowY: "auto", flex: 1, padding: "4px 0", margin: 0, listStyle: "none" }}
          >
            {filtered.map((c, i) => (
              <li
                key={c.code}
                role="option"
                aria-selected={c.code === dialCountry}
                onClick={() => selectDial(c)}
                onMouseEnter={() => setHighlighted(i)}
                style={{
                  padding: "7px 14px", fontSize: 13, cursor: "pointer",
                  display: "flex", alignItems: "center", gap: 10,
                  background: i === highlighted || c.code === dialCountry
                    ? "var(--canvas-2, #F5F4F0)" : "transparent",
                }}
              >
                <FlagImg code={c.code} />
                <span style={{ flex: 1 }}>{c.name}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

// ─── Step 1: Shipping ────────────────────────────────────────────────────────
const INITIAL_SHIPPING = {
  full_name: "", email: "",
  phone_dial: "", phone_country: "", phone_number: "",
  address_line1: "", address_line2: "",
  city: "", region: "", postal_code: "",
  country_code: "", country_name: "",
};

function validate(form, t) {
  const errs = {};
  if (!form.full_name.trim()) errs.full_name = t("validation.fullNameRequired");
  if (!form.email.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email))
    errs.email = t("validation.emailRequired");
  if (!form.phone_number.trim()) errs.phone = t("validation.phoneRequired");
  if (!form.address_line1.trim()) errs.address_line1 = t("validation.addressRequired");
  if (!form.city.trim()) errs.city = t("validation.cityRequired");
  if (!form.country_code) errs.country_code = t("validation.countryRequired");
  return errs;
}

function ShippingStep({ shipping, setShipping, onBack, onNext }) {
  const { t } = useTranslation("checkout");
  const [errors, setErrors] = useState({});

  const selectedCountry = COUNTRIES.find(c => c.code === shipping.country_code);
  const regionLabel = selectedCountry?.region || "Region / State";

  const update = (updates) => setShipping(prev => ({ ...prev, ...updates }));
  const clearErr = (...keys) => setErrors(prev => {
    const next = { ...prev };
    keys.forEach(k => delete next[k]);
    return next;
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    const errs = validate(shipping, t);
    if (Object.keys(errs).length) { setErrors(errs); return; }
    onNext();
  };

  const labelStyle = {
    display: "block", fontSize: 11, fontWeight: 600,
    letterSpacing: "0.06em", textTransform: "uppercase",
    color: "var(--text-2)", marginBottom: 6,
  };
  const errStyle = {
    fontSize: 11, color: "var(--error, #C0392B)", marginTop: 4, display: "block",
  };

  return (
    <div className="panel" style={{ padding: 32 }}>
      <h2 style={{ fontSize: 18, fontWeight: 700, letterSpacing: "-0.02em", marginBottom: 6 }}>
        {t("shipping.heading")}
      </h2>
      <p style={{ fontSize: 13, color: "var(--text-2)", marginBottom: 28 }}>
        {t("shipping.description")}
      </p>

      <form onSubmit={handleSubmit} noValidate>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 24 }}>

          {/* Full Name */}
          <div style={{ gridColumn: "span 2" }}>
            <label htmlFor="sh-name" style={labelStyle}>{t("address.fullName")} *</label>
            <input
              id="sh-name" name="full_name" type="text" autoComplete="name"
              placeholder={t("address.fullNamePlaceholder")}
              value={shipping.full_name}
              onChange={(e) => { update({ full_name: e.target.value }); clearErr("full_name"); }}
              aria-invalid={!!errors.full_name}
              aria-describedby={errors.full_name ? "err-full_name" : undefined}
              style={{ borderColor: errors.full_name ? "var(--error, #C0392B)" : undefined }}
            />
            {errors.full_name && <span id="err-full_name" role="alert" style={errStyle}>{errors.full_name}</span>}
          </div>

          {/* Email */}
          <div style={{ gridColumn: "span 2" }}>
            <label htmlFor="sh-email" style={labelStyle}>{t("address.email")} *</label>
            <input
              id="sh-email" name="email" type="email" autoComplete="email"
              placeholder={t("address.emailPlaceholder")}
              value={shipping.email}
              onChange={(e) => { update({ email: e.target.value }); clearErr("email"); }}
              aria-invalid={!!errors.email}
              aria-describedby={errors.email ? "err-email" : undefined}
              style={{ borderColor: errors.email ? "var(--error, #C0392B)" : undefined }}
            />
            {errors.email && <span id="err-email" role="alert" style={errStyle}>{errors.email}</span>}
          </div>

          {/* Phone */}
          <div style={{ gridColumn: "span 2" }}>
            <label style={labelStyle}>{t("address.phone")} *</label>
            <PhoneInput
              dialCode={shipping.phone_dial}
              dialCountry={shipping.phone_country}
              onDialChange={(c) => update({ phone_dial: c.dial, phone_country: c.code })}
              number={shipping.phone_number}
              onNumberChange={(v) => { update({ phone_number: v }); clearErr("phone"); }}
              error={errors.phone}
            />
            {errors.phone && <span role="alert" style={errStyle}>{errors.phone}</span>}
          </div>

          {/* Address Line 1 */}
          <div style={{ gridColumn: "span 2" }}>
            <label htmlFor="sh-addr1" style={labelStyle}>{t("address.addressLine1")} *</label>
            <input
              id="sh-addr1" name="address_line1" type="text" autoComplete="address-line1"
              placeholder={t("address.addressLine1Placeholder")}
              value={shipping.address_line1}
              onChange={(e) => { update({ address_line1: e.target.value }); clearErr("address_line1"); }}
              aria-invalid={!!errors.address_line1}
              style={{ borderColor: errors.address_line1 ? "var(--error, #C0392B)" : undefined }}
            />
            {errors.address_line1 && <span role="alert" style={errStyle}>{errors.address_line1}</span>}
          </div>

          {/* Address Line 2 */}
          <div style={{ gridColumn: "span 2" }}>
            <label htmlFor="sh-addr2" style={labelStyle}>{t("address.addressLine2")}</label>
            <input
              id="sh-addr2" name="address_line2" type="text" autoComplete="address-line2"
              placeholder={t("address.addressLine2Placeholder")}
              value={shipping.address_line2}
              onChange={(e) => update({ address_line2: e.target.value })}
            />
          </div>

          {/* City */}
          <div style={{ gridColumn: "span 1" }}>
            <label htmlFor="sh-city" style={labelStyle}>{t("address.city")} *</label>
            <input
              id="sh-city" name="city" type="text" autoComplete="address-level2"
              placeholder={t("address.cityPlaceholder")}
              value={shipping.city}
              onChange={(e) => { update({ city: e.target.value }); clearErr("city"); }}
              aria-invalid={!!errors.city}
              style={{ borderColor: errors.city ? "var(--error, #C0392B)" : undefined }}
            />
            {errors.city && <span role="alert" style={errStyle}>{errors.city}</span>}
          </div>

          {/* Region / State — label adapts to selected country */}
          <div style={{ gridColumn: "span 1" }}>
            <label htmlFor="sh-region" style={labelStyle}>{regionLabel}</label>
            <input
              id="sh-region" name="region" type="text" autoComplete="address-level1"
              placeholder={regionLabel}
              value={shipping.region}
              onChange={(e) => update({ region: e.target.value })}
            />
          </div>

          {/* Postal Code */}
          <div style={{ gridColumn: "span 1" }}>
            <label htmlFor="sh-postal" style={labelStyle}>{t("address.postalCode")}</label>
            <input
              id="sh-postal" name="postal_code" type="text" autoComplete="postal-code"
              placeholder={t("address.postalCodePlaceholder")}
              value={shipping.postal_code}
              onChange={(e) => update({ postal_code: e.target.value })}
            />
          </div>

          {/* Country — searchable dropdown */}
          <div style={{ gridColumn: "span 1" }}>
            <label style={labelStyle}>{t("address.country")} *</label>
            <CountrySelect
              value={shipping.country_code}
              onChange={(c) => { update({ country_code: c.code, country_name: c.name }); clearErr("country_code"); }}
              error={errors.country_code}
            />
            {errors.country_code && <span role="alert" style={errStyle}>{errors.country_code}</span>}
          </div>

        </div>

        <div className="row" style={{ gap: 10 }}>
          <button type="button" className="btn" onClick={onBack} style={{ height: 44 }}>
            <ArrowLeft size={14} style={{ marginRight: 6 }} />{t("button.back")}
          </button>
          <button type="submit" className="btn btn-primary" style={{ height: 44, flex: 1 }}>
            {t("address.continueButton")}
          </button>
        </div>
      </form>
    </div>
  );
}

// ─── Step 2: Payment ─────────────────────────────────────────────────────────
function PaymentStep({ listing, shipping, onBack, onPaid }) {
  const { t } = useTranslation("checkout");
  const [processing, setProcessing] = useState(false);

  const handlePay = async () => {
    setProcessing(true);
    try {
      // 1. Create the order via buy-now
      const { data: orderData } = await api.post("/orders/buy-now", {
        listing_id: listing.id,
      });

      // 2. Initiate payment checkout (provider-agnostic; sandbox auto-settles)
      const { data: payData } = await api.post("/payments/checkout", {
        order_id: orderData.order_id,
      });

      // Provider returned a hosted checkout page (e.g. LiqPay)
      if (payData.checkout_url && payData.data) {
        const form = document.createElement("form");
        form.method = "POST";
        form.action = payData.checkout_url;
        [["data", payData.data], ["signature", payData.signature]].forEach(([n, v]) => {
          const inp = document.createElement("input");
          inp.type = "hidden"; inp.name = n; inp.value = v;
          form.appendChild(inp);
        });
        document.body.appendChild(form);
        form.submit();
        return;
      }

      // Sandbox: payment settled synchronously
      onPaid({ orderNumber: orderData.order_number, orderId: orderData.order_id });
    } catch (err) {
      toast.error(apiError(err));
      setProcessing(false);
    }
  };

  return (
    <div className="panel" style={{ padding: 32 }}>
      <h2 style={{ fontSize: 18, fontWeight: 700, letterSpacing: "-0.02em", marginBottom: 6 }}>{t("payment.heading")}</h2>
      <p style={{ fontSize: 13, color: "var(--text-2)", marginBottom: 28 }}>
        {t("payment.secureNote")}
      </p>

      {/* Shipping recap */}
      <div style={{ background: "var(--canvas-2, #F5F4F0)", borderRadius: 8, padding: "14px 16px", marginBottom: 24 }}>
        <div className="row" style={{ gap: 8, marginBottom: 8 }}>
          <MapPin size={14} color="var(--muted)" />
          <span style={{ fontSize: 12, fontWeight: 600, color: "var(--text-2)" }}>{t("payment.shippingTo")}</span>
        </div>
        <div style={{ fontSize: 13, lineHeight: 1.7 }}>
          {shipping.full_name}<br />
          {shipping.address_line1}{shipping.address_line2 ? `, ${shipping.address_line2}` : ""}<br />
          {[shipping.city, shipping.region].filter(Boolean).join(", ")}
          {shipping.postal_code ? ` ${shipping.postal_code}` : ""}<br />
          {shipping.country_name}
          {(shipping.phone_dial || shipping.phone_number) && (
            <><br />{[shipping.phone_dial, shipping.phone_number].filter(Boolean).join(" ")}</>
          )}
        </div>
      </div>

      {/* Order total */}
      <div className="row" style={{ justifyContent: "space-between", padding: "16px 0", borderTop: "1px solid var(--border)", borderBottom: "1px solid var(--border)", marginBottom: 24 }}>
        <span style={{ fontSize: 14, fontWeight: 600 }}>{t("payment.totalDue")}</span>
        <span style={{ fontSize: 20, fontWeight: 700, letterSpacing: "-0.02em" }}>{formatPrice(listing?.price)}</span>
      </div>

      {/* Payment notice */}
      <div style={{ background: "var(--canvas-2, #F5F4F0)", borderRadius: 8, padding: "12px 16px", marginBottom: 24 }}>
        <p style={{ fontSize: 12, color: "var(--text-2)", lineHeight: 1.7, margin: 0 }}>
          {t("payment.certifiedNote")}
        </p>
      </div>

      <div className="row" style={{ gap: 10 }}>
        <button className="btn" onClick={onBack} disabled={processing} style={{ height: 48 }}>
          <ArrowLeft size={14} style={{ marginRight: 6 }} />{t("button.back")}
        </button>
        <button
          className="btn btn-primary"
          onClick={handlePay}
          disabled={processing}
          style={{ height: 48, flex: 1, fontSize: 15 }}
          data-testid="checkout-pay-button"
        >
          {processing ? (
            <span className="row" style={{ gap: 8, justifyContent: "center" }}>
              <span className="spin" style={{ width: 16, height: 16 }} />
              Processing…
            </span>
          ) : (
            t("payment.placeOrder")
          )}
        </button>
      </div>
    </div>
  );
}

// ─── Step 3: Confirmation ────────────────────────────────────────────────────
function ConfirmationStep({ orderNumber, orderId }) {
  const { t } = useTranslation("checkout");
  return (
    <motion.div
      className="panel"
      style={{ padding: 40, textAlign: "center" }}
      variants={slideUpVariants}
      initial="hidden"
      animate="visible"
    >
      <div style={{
        width: 64, height: 64, borderRadius: "50%",
        background: "var(--success-bg, #EEF2ED)", display: "flex",
        alignItems: "center", justifyContent: "center", margin: "0 auto 24px",
      }}>
        <CheckCircle size={32} color="var(--success, #596B52)" weight="fill" />
      </div>

      <h2 style={{ fontSize: 22, fontWeight: 700, letterSpacing: "-0.02em", marginBottom: 8 }}>
        {t("confirmation.heading")}
      </h2>
      <p style={{ fontSize: 14, color: "var(--text-2)", marginBottom: 8, lineHeight: 1.7 }}>
        Your payment was received and is held securely in escrow.
      </p>
      <div className="overline" style={{ color: "var(--muted)", marginBottom: 32 }}>
        Order {orderNumber}
      </div>

      <div style={{ background: "var(--canvas-2, #F5F4F0)", borderRadius: 8, padding: "14px 16px", marginBottom: 32, textAlign: "left" }}>
        <div className="stack" style={{ gap: 10 }}>
          <div className="row" style={{ gap: 8 }}>
            <CheckCircle size={14} color="var(--success, #596B52)" weight="fill" />
            <span style={{ fontSize: 13 }}>Payment received — funds held in escrow</span>
          </div>
          <div className="row" style={{ gap: 8 }}>
            <Package size={14} color="var(--muted)" />
            <span style={{ fontSize: 13, color: "var(--text-2)" }}>Seller will ship within 5 days</span>
          </div>
          <div className="row" style={{ gap: 8 }}>
            <CreditCard size={14} color="var(--muted)" />
            <span style={{ fontSize: 13, color: "var(--text-2)" }}>Escrow released to seller when you confirm delivery</span>
          </div>
        </div>
      </div>

      <div className="row" style={{ gap: 10, justifyContent: "center" }}>
        <Link to="/orders" className="btn btn-primary" style={{ height: 44, display: "inline-flex", alignItems: "center" }}>
          View My Orders
        </Link>
        <Link to="/shop" className="btn" style={{ height: 44, display: "inline-flex", alignItems: "center" }}>
          Continue Shopping
        </Link>
      </div>
    </motion.div>
  );
}

// ─── Main Checkout page ──────────────────────────────────────────────────────
export default function Checkout() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { t } = useTranslation("checkout");
  const listingId = searchParams.get("listing_id");

  const [step, setStep] = useState(0);
  const [listing, setListing] = useState(null);
  const [notFound, setNotFound] = useState(false);
  const [shipping, setShipping] = useState(INITIAL_SHIPPING);
  const [confirmation, setConfirmation] = useState(null); // { orderNumber, orderId }

  useEffect(() => {
    if (!listingId) { navigate("/shop"); return; }
    api.get(`/listings/${listingId}`)
      .then((r) => {
        const l = r.data.listing;
        if (l.state !== "Published") { setNotFound(true); return; }
        if (user && l.seller_id === user.id) {
          toast.error("You cannot purchase your own listing");
          navigate(`/listing/${listingId}`);
          return;
        }
        setListing(l);
      })
      .catch(() => setNotFound(true));
  }, [listingId, user, navigate]);

  if (!listingId || notFound) return (
    <div className="container" style={{ paddingTop: 80 }}>
      <div className="empty">
        <p className="hint" style={{ marginBottom: 20 }}>{t("notAvailable")}</p>
        <Link to="/shop" className="btn">{t("button.backToShop")}</Link>
      </div>
    </div>
  );

  if (!listing) return (
    <div style={{ display: "flex", justifyContent: "center", padding: "80px 0" }}>
      <div className="spin" />
    </div>
  );

  const goNext = () => setStep((s) => s + 1);
  const goBack = () => setStep((s) => s - 1);

  const handlePaid = (data) => {
    setConfirmation(data);
    setStep(3);
  };

  return (
    <div className="container" style={{ paddingTop: 28, paddingBottom: 80 }}>
      {/* Back link */}
      {step < 3 && (
        <Link
          to={`/listing/${listing.id}`}
          className="row"
          style={{ gap: 6, color: "var(--text-2)", fontSize: 13, marginBottom: 28, width: "fit-content" }}
        >
          <ArrowLeft size={14} />
          <span>{t("button.backToListing")}</span>
        </Link>
      )}

      <h1 style={{ fontSize: 26, fontWeight: 700, letterSpacing: "-0.02em", marginBottom: 28 }}>
        {t("heading")}
      </h1>

      <StepBar current={step} />

      <div style={{
        display: "grid",
        gridTemplateColumns: step === 3 ? "1fr" : "minmax(0,1fr) 320px",
        gap: 24,
        alignItems: "start",
      }}>
        {/* Main content */}
        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            variants={slideUpVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
          >
            {step === 0 && <ReviewStep listing={listing} onNext={goNext} />}
            {step === 1 && <ShippingStep shipping={shipping} setShipping={setShipping} onBack={goBack} onNext={goNext} />}
            {step === 2 && <PaymentStep listing={listing} shipping={shipping} onBack={goBack} onPaid={handlePaid} />}
            {step === 3 && confirmation && (
              <ConfirmationStep orderNumber={confirmation.orderNumber} orderId={confirmation.orderId} />
            )}
          </motion.div>
        </AnimatePresence>

        {/* Sidebar — hidden on confirmation */}
        {step < 3 && <OrderSummary listing={listing} />}
      </div>
    </div>
  );
}
