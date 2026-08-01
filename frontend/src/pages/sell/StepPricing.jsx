import React from "react";
import { useTranslation } from "react-i18next";
import { formatPrice } from "../../lib/api";

const PLATFORM_FEE_PCT = 10;

function fmtUAH(minor) {
  if (!minor || minor <= 0) return "—";
  return formatPrice({ amount: Math.round(minor), currency: "UAH" });
}

export default function StepPricing({ form, onChange, errors }) {
  const { t } = useTranslation("sell");
  const set = (k, v) => onChange({ ...form, [k]: v });

  const priceMinor = Math.round(parseFloat(form.price_amount || 0) * 100);
  const feeMinor = Math.round(priceMinor * PLATFORM_FEE_PCT / 100);
  const payoutMinor = priceMinor - feeMinor;
  const minOfferMinor = form.min_offer ? Math.round(parseFloat(form.min_offer) * 100) : 0;

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: 22, fontWeight: 700, letterSpacing: "-0.02em", marginBottom: 8 }}>
          {t("pricing.heading")}
        </h2>
        <p style={{ fontSize: 14, color: "var(--text-2)", lineHeight: 1.6 }}>
          {t("pricing.description")}
        </p>
      </div>

      {/* Price input */}
      <div style={{ marginBottom: 24 }}>
        <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--text-2)", marginBottom: 6 }}>{t("pricing.field.price", { currency: "UAH" })} *</label>
        <div style={{ position: "relative", maxWidth: 280 }}>
          <span style={{
            position: "absolute", left: 14, top: "50%", transform: "translateY(-50%)",
            fontSize: 16, fontWeight: 600, color: "var(--muted)", pointerEvents: "none",
          }}>
            ₴
          </span>
          <input
            data-testid="sell-price"
            type="number"
            min="1"
            step="1"
            value={form.price_amount}
            onChange={(e) => set("price_amount", e.target.value)}
            placeholder="0"
            style={{
              paddingLeft: 32,
              fontSize: 20,
              fontWeight: 700,
              letterSpacing: "-0.02em",
              borderColor: errors?.price_amount ? "var(--error)" : undefined,
            }}
          />
        </div>
        {errors?.price_amount && (
          <p style={{ fontSize: 12, color: "var(--error)", marginTop: 4 }}>{errors.price_amount}</p>
        )}
      </div>

      {/* Fee breakdown — appears as soon as price is entered */}
      {priceMinor > 0 && (
        <div style={{
          background: "var(--subtle)",
          borderRadius: 10,
          padding: "16px 20px",
          marginBottom: 24,
          display: "flex",
          flexDirection: "column",
          gap: 10,
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, color: "var(--text-2)" }}>
            <span>{t("pricing.breakdown.listing")}</span>
            <span>{fmtUAH(priceMinor)}</span>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, color: "var(--muted)" }}>
            <span>{t("pricing.breakdown.fee", { pct: PLATFORM_FEE_PCT })}</span>
            <span>−{fmtUAH(feeMinor)}</span>
          </div>
          <div style={{ height: 1, background: "var(--border)" }} />
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 15, fontWeight: 700 }}>
            <span>{t("pricing.breakdown.payout")}</span>
            <span style={{ color: "var(--success)" }}>{fmtUAH(payoutMinor)}</span>
          </div>
        </div>
      )}

      {/* Accept offers toggle */}
      <div style={{ marginBottom: form.allow_offers ? 12 : 0 }}>
        <label
          data-testid="sell-allow-offers-label"
          style={{
            display: "flex",
            alignItems: "flex-start",
            gap: 14,
            padding: "16px",
            border: `1.5px solid ${form.allow_offers ? "var(--text)" : "var(--border)"}`,
            borderRadius: 10,
            cursor: "pointer",
            background: form.allow_offers ? "var(--subtle)" : "var(--surface)",
            transition: "all 0.15s",
          }}
        >
          <input
            type="checkbox"
            data-testid="sell-allow-offers"
            checked={form.allow_offers}
            onChange={(e) => set("allow_offers", e.target.checked)}
            style={{ width: "auto", marginTop: 2, accentColor: "var(--text)" }}
          />
          <div>
            <div style={{ fontSize: 14, fontWeight: 600 }}>{t("pricing.field.allowOffers")}</div>
            <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 2 }}>
              Let buyers negotiate — listings with offers receive significantly more engagement
            </div>
          </div>
        </label>
      </div>

      {/* Minimum offer — only when offers enabled and price set */}
      {form.allow_offers && priceMinor > 0 && (
        <div style={{
          marginTop: 0,
          padding: "14px 16px",
          background: "var(--subtle)",
          borderRadius: 10,
          borderTop: "none",
        }}>
          <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--text-2)", marginBottom: 6 }}>
            Minimum offer (optional)
          </label>
          <div style={{ position: "relative", maxWidth: 200 }}>
            <span style={{
              position: "absolute", left: 14, top: "50%", transform: "translateY(-50%)",
              fontSize: 14, fontWeight: 600, color: "var(--muted)", pointerEvents: "none",
            }}>
              ₴
            </span>
            <input
              type="number"
              min="1"
              step="1"
              value={form.min_offer || ""}
              onChange={(e) => set("min_offer", e.target.value)}
              placeholder={t("pricing.placeholder.minOffer")}
              style={{ paddingLeft: 30 }}
            />
          </div>
          {minOfferMinor > 0 && (
            <p style={{ fontSize: 12, color: "var(--muted)", marginTop: 6 }}>
              Offers below {fmtUAH(minOfferMinor)} will not be shown to buyers
            </p>
          )}
        </div>
      )}
    </div>
  );
}
