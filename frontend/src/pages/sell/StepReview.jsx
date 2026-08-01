import React from "react";
import { useTranslation } from "react-i18next";
import { PencilSimple } from "@phosphor-icons/react";
import { computeQualityScore } from "./useQualityScore.js";
import { formatPrice } from "../../lib/api";

function fmtUAH(minor) {
  if (!minor || minor <= 0) return "—";
  return formatPrice({ amount: Math.round(minor), currency: "UAH" });
}

function ReviewSection({ title, step, onEdit, t, children }) {
  return (
    <div style={{ paddingBottom: 24 }}>
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        marginBottom: 14, paddingBottom: 10, borderBottom: "1px solid var(--border)",
      }}>
        <span style={{
          fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase",
          fontWeight: 600, color: "var(--muted)",
        }}>
          {title}
        </span>
        <button
          type="button"
          onClick={() => onEdit(step)}
          style={{
            display: "flex", alignItems: "center", gap: 5,
            fontSize: 12, fontWeight: 600, color: "var(--text-2)",
            background: "none", border: "none", cursor: "pointer",
            padding: "4px 8px", borderRadius: 6,
            transition: "color 0.12s",
          }}
        >
          <PencilSimple size={12} />
          {t("review.button.edit")}
        </button>
      </div>
      {children}
    </div>
  );
}

function ScoreGauge({ score, t }) {
  const radius = 22;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - score / 100);
  const color = score >= 80 ? "var(--success)" : score >= 55 ? "var(--warning)" : "var(--error)";
  const label = score >= 80 ? t("review.score.excellent") : score >= 55 ? t("review.score.good") : score >= 35 ? t("review.score.fair") : t("review.score.needsWork");

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
      <div style={{ position: "relative", width: 60, height: 60, flexShrink: 0 }}>
        <svg viewBox="0 0 60 60" style={{ transform: "rotate(-90deg)", width: "100%", height: "100%" }}>
          <circle cx="30" cy="30" r={radius} fill="none" stroke="var(--border)" strokeWidth="4" />
          <circle
            cx="30" cy="30" r={radius}
            fill="none" stroke={color} strokeWidth="4"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            style={{ transition: "stroke-dashoffset 0.4s cubic-bezier(0,0,0.2,1)" }}
          />
        </svg>
        <span style={{
          position: "absolute", inset: 0, display: "flex", alignItems: "center",
          justifyContent: "center", fontSize: 12, fontWeight: 800, color,
        }}>
          {score}
        </span>
      </div>
      <div>
        <div style={{ fontSize: 16, fontWeight: 700, color }}>{label}</div>
        <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 2 }}>{t("review.score.label")}</div>
      </div>
    </div>
  );
}

export default function StepReview({ draft, onGoToStep, onPublish, busy }) {
  const { t } = useTranslation("sell");
  const CONDITION_LABELS = {
    BRAND_NEW: t("condition.value.BRAND_NEW"),
    LIKE_NEW: t("condition.value.LIKE_NEW"),
    GENTLY_USED: t("condition.value.GENTLY_USED"),
    USED: t("condition.value.USED"),
    WELL_WORN: t("condition.value.WELL_WORN"),
  };
  const SHIPS_TO_LABELS = {
    domestic: t("shipping.option.domestic"),
    europe: t("shipping.option.europe"),
    worldwide: t("shipping.option.worldwide"),
  };
  const { score, checks } = computeQualityScore(draft);
  const priceMinor = Math.round(parseFloat(draft.price_amount || 0) * 100);
  const feeMinor = Math.round(priceMinor * 0.1);
  const payoutMinor = priceMinor - feeMinor;
  const hasMeasurements = Object.values(draft.measurements || {}).some(v => v);

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: 22, fontWeight: 700, letterSpacing: "-0.02em", marginBottom: 8 }}>
          {t("review.heading")}
        </h2>
        <p style={{ fontSize: 14, color: "var(--text-2)", lineHeight: 1.6 }}>
          {t("review.description")}
        </p>
      </div>

      {/* Quality score */}
      <div style={{
        background: "var(--subtle)", borderRadius: 12,
        padding: "20px 24px", marginBottom: 32,
      }}>
        <ScoreGauge score={score} t={t} />
        <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 7 }}>
          {checks.map((c, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13 }}>
              <span style={{
                color: c.met ? "var(--success)" : "var(--border-strong)",
                fontWeight: 700, fontSize: 14, lineHeight: 1, flexShrink: 0,
              }}>
                {c.met ? "✓" : "○"}
              </span>
              <span style={{ color: c.met ? "var(--text)" : "var(--muted)" }}>{c.label}</span>
            </div>
          ))}
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>

        {/* Photos */}
        <ReviewSection title={t("review.section.photos")} step={0} onEdit={onGoToStep} t={t}>
          {draft.photos.length > 0 ? (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(64px, 1fr))", gap: 6 }}>
              {draft.photos.map((p, i) => (
                <div key={i} style={{
                  aspectRatio: "1", borderRadius: 6, overflow: "hidden",
                  background: "var(--subtle)", position: "relative",
                }}>
                  <img src={p.preview} alt="" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                  {i === 0 && (
                    <div style={{
                      position: "absolute", bottom: 2, left: 2,
                      background: "rgba(0,0,0,0.6)", borderRadius: 3,
                      padding: "1px 4px", fontSize: 8, color: "#fff", fontWeight: 700,
                    }}>
                      Cover
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <span style={{ fontSize: 13, color: "var(--muted)" }}>{t("review.empty.photos")}</span>
          )}
        </ReviewSection>

        {/* Details */}
        <ReviewSection title={t("review.section.details")} step={1} onEdit={onGoToStep} t={t}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px 32px" }}>
            {[
              ["Title", draft.title],
              ["Brand", draft.brand],
              ["Category", draft.category],
              ["Size", draft.size],
              ["Color", draft.color],
              ["Material", draft.material],
              ["Gender", draft.gender],
              ["Season", draft.season],
            ].filter(([, v]) => v).map(([k, v]) => (
              <div key={k}>
                <div style={{ fontSize: 10, letterSpacing: "0.08em", textTransform: "uppercase", color: "var(--muted)", fontWeight: 600 }}>{k}</div>
                <div style={{ fontSize: 13, color: "var(--text)", marginTop: 2 }}>{v}</div>
              </div>
            ))}
          </div>
          {draft.description && (
            <p style={{ fontSize: 13, color: "var(--text-2)", marginTop: 12, lineHeight: 1.5 }}>
              {draft.description}
            </p>
          )}
        </ReviewSection>

        {/* Condition */}
        <ReviewSection title={t("review.section.condition")} step={2} onEdit={onGoToStep} t={t}>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <span style={{ fontSize: 14, fontWeight: 600 }}>
              {CONDITION_LABELS[draft.condition] || draft.condition || "—"}
            </span>
            {draft.condition_notes && (
              <p style={{ fontSize: 13, color: "var(--text-2)", lineHeight: 1.5 }}>
                {draft.condition_notes}
              </p>
            )}
            {hasMeasurements && (
              <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginTop: 4 }}>
                {Object.entries(draft.measurements).filter(([, v]) => v).map(([k, v]) => (
                  <span key={k} style={{ fontSize: 12, color: "var(--text-2)" }}>
                    <span style={{ textTransform: "capitalize", color: "var(--muted)" }}>
                      {k.replace(/_/g, " ")}
                    </span>: {v} cm
                  </span>
                ))}
              </div>
            )}
          </div>
        </ReviewSection>

        {/* Pricing */}
        <ReviewSection title={t("review.section.pricing")} step={3} onEdit={onGoToStep} t={t}>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <div style={{ fontSize: 26, fontWeight: 800, letterSpacing: "-0.03em" }}>
              {fmtUAH(priceMinor)}
            </div>
            <div style={{ display: "flex", gap: 16, fontSize: 12, color: "var(--muted)" }}>
              <span>Platform fee: {fmtUAH(feeMinor)}</span>
              <span>{t("pricing.breakdown.payout")}: <strong style={{ color: "var(--text)" }}>{fmtUAH(payoutMinor)}</strong></span>
            </div>
            {draft.allow_offers && (
              <span style={{ fontSize: 12, color: "var(--success)", fontWeight: 600, marginTop: 2 }}>
                {t("review.badge.acceptingOffers")}
              </span>
            )}
          </div>
        </ReviewSection>

        {/* Shipping */}
        <ReviewSection title={t("review.section.shipping")} step={4} onEdit={onGoToStep} t={t}>
          <div style={{ fontSize: 13, color: "var(--text-2)" }}>
            {SHIPS_TO_LABELS[draft.ships_to] || t("review.empty.shipping")}
            {draft.ships_from_region && ` · Ships from ${draft.ships_from_region}`}
          </div>
          {draft.shipping_notes && (
            <p style={{ fontSize: 13, color: "var(--muted)", marginTop: 6, lineHeight: 1.5 }}>
              {draft.shipping_notes}
            </p>
          )}
        </ReviewSection>
      </div>

      {/* Publish */}
      <div style={{ marginTop: 32, display: "flex", flexDirection: "column", gap: 10 }}>
        <button
          type="button"
          className="btn btn-primary btn-block"
          disabled={busy}
          onClick={onPublish}
          data-testid="sell-submit"
          style={{ height: 52, fontSize: 15, fontWeight: 700 }}
        >
          {busy ? t("wizard.button.publishing") : t("wizard.button.publish")}
        </button>
        <p style={{ fontSize: 12, color: "var(--muted)", textAlign: "center" }}>
          Your listing will be live and visible to buyers immediately
        </p>
      </div>
    </div>
  );
}
