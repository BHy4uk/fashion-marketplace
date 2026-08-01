import React from "react";
import { useTranslation } from "react-i18next";
import { getCategoryGroup, getMeasurements } from "./categorySchema.js";
import { Info } from "@phosphor-icons/react";

export default function StepCondition({ form, onChange, errors }) {
  const { t } = useTranslation("sell");
  const CONDITIONS = [
    { value: "BRAND_NEW", label: t("condition.value.BRAND_NEW"), desc: t("condition.desc.BRAND_NEW") },
    { value: "LIKE_NEW", label: t("condition.value.LIKE_NEW"), desc: t("condition.desc.LIKE_NEW") },
    { value: "GENTLY_USED", label: t("condition.value.GENTLY_USED"), desc: t("condition.desc.GENTLY_USED") },
    { value: "USED", label: t("condition.value.USED"), desc: t("condition.desc.USED") },
    { value: "WELL_WORN", label: t("condition.value.WELL_WORN"), desc: t("condition.desc.WELL_WORN") },
  ];
  const INCLUDED_OPTIONS = [
    { key: "has_authentication", label: t("condition.option.auth") },
    { key: "has_receipt", label: t("condition.option.receipt") },
    { key: "has_original_packaging", label: t("condition.option.packaging") },
  ];
  const set = (k, v) => onChange({ ...form, [k]: v });
  const setMeasurement = (k, v) =>
    onChange({ ...form, measurements: { ...(form.measurements || {}), [k]: v } });

  const group = getCategoryGroup(form.category);
  const measurementFields = getMeasurements(group);
  const hasMeasurements = Object.values(form.measurements || {}).some(v => v);

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: 22, fontWeight: 700, letterSpacing: "-0.02em", marginBottom: 8 }}>
          {t("condition.heading")}
        </h2>
        <p style={{ fontSize: 14, color: "var(--text-2)", lineHeight: 1.6 }}>
          {t("condition.description")}
        </p>
      </div>

      {/* Condition radio cards */}
      <div style={{ marginBottom: 24 }}>
        <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--text-2)", marginBottom: 10 }}>
          {t("condition.field.condition")} *
        </label>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {CONDITIONS.map(c => {
            const selected = form.condition === c.value;
            return (
              <label
                key={c.value}
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: 14,
                  padding: "14px 16px",
                  border: `1.5px solid ${selected ? "var(--text)" : "var(--border)"}`,
                  borderRadius: 10,
                  cursor: "pointer",
                  background: selected ? "var(--subtle)" : "var(--surface)",
                  transition: "all 0.15s",
                }}
              >
                <input
                  type="radio"
                  name="condition"
                  value={c.value}
                  checked={selected}
                  onChange={() => set("condition", c.value)}
                  style={{ width: "auto", marginTop: 1, accentColor: "var(--text)" }}
                  data-testid={`sell-condition-${c.value}`}
                />
                <div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text)" }}>{c.label}</div>
                  <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 2 }}>{c.desc}</div>
                </div>
              </label>
            );
          })}
        </div>
        {errors?.condition && (
          <p style={{ fontSize: 12, color: "var(--error)", marginTop: 6 }}>{errors.condition}</p>
        )}
      </div>

      {/* Condition notes */}
      <div style={{ marginBottom: 24 }}>
        <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--text-2)", marginBottom: 6 }}>{t("condition.field.notes")}</label>
        <textarea
          rows={3}
          value={form.condition_notes || ""}
          onChange={(e) => set("condition_notes", e.target.value)}
          placeholder={t("condition.placeholder.notes")}
        />
      </div>

      {/* Included accessories */}
      <div style={{ marginBottom: 28 }}>
        <p style={{ fontSize: 12, fontWeight: 600, color: "var(--text-2)", marginBottom: 10 }}>
          {t("condition.section.included")}
        </p>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {INCLUDED_OPTIONS.map(({ key, label }) => (
            <label
              key={key}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 12,
                fontSize: 14,
                cursor: "pointer",
                padding: "10px 14px",
                border: `1px solid ${form[key] ? "var(--text)" : "var(--border)"}`,
                borderRadius: 8,
                background: form[key] ? "var(--subtle)" : "var(--surface)",
                transition: "all 0.15s",
              }}
            >
              <input
                type="checkbox"
                style={{ width: "auto", accentColor: "var(--text)" }}
                checked={!!form[key]}
                onChange={(e) => set(key, e.target.checked)}
              />
              {label}
            </label>
          ))}
        </div>
      </div>

      {/* Measurements */}
      <div>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
          <p style={{ fontSize: 12, fontWeight: 600, color: "var(--text-2)" }}>
            {t("condition.section.measurements")}
          </p>
          <span style={{
            display: "flex", alignItems: "center", gap: 4,
            fontSize: 12, color: "var(--info)",
          }}>
            <Info size={12} />
            {t("condition.hint.measurements")}
          </span>
        </div>
        <div className="grid-form">
          {measurementFields.map(f => (
            <div key={f.key}>
              <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--text-2)", marginBottom: 6 }}>{f.label}</label>
              <input
                type="number"
                min="0"
                step="0.5"
                value={(form.measurements || {})[f.key] || ""}
                onChange={(e) => setMeasurement(f.key, e.target.value)}
                placeholder={t("condition.placeholder.measurement")}
              />
            </div>
          ))}
        </div>
        {!hasMeasurements && (
          <p style={{ fontSize: 12, color: "var(--muted)", marginTop: 8 }}>
            {t("condition.hint.optional")}
          </p>
        )}
      </div>
    </div>
  );
}
