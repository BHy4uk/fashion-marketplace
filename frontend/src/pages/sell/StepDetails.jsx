import React from "react";
import { useTranslation } from "react-i18next";
import { getCategoryGroup, getExtraFields } from "./categorySchema.js";

const SEASONS = ["", "Spring / Summer", "Autumn / Winter", "Year-round"];
const COLORS = [
  "", "Black", "White", "Grey", "Navy", "Blue", "Green", "Brown",
  "Beige", "Cream", "Tan", "Red", "Pink", "Yellow", "Orange", "Purple", "Multi", "Other",
];

export default function StepDetails({ form, onChange, meta, cats, brands, errors }) {
  const { t } = useTranslation("sell");
  const set = (k, v) => onChange({ ...form, [k]: v });
  const setExtra = (k, v) => onChange({ ...form, extra: { ...(form.extra || {}), [k]: v } });
  const extra = form.extra || {};

  const group = getCategoryGroup(form.category);
  const extraFields = getExtraFields(group);
  const selectedCat = cats.find(c => c.slug === form.category);

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: 22, fontWeight: 700, letterSpacing: "-0.02em", marginBottom: 8 }}>
          {t("details.heading")}
        </h2>
        <p style={{ fontSize: 14, color: "var(--text-2)", lineHeight: 1.6 }}>
          {t("details.description")}
        </p>
      </div>

      {/* Title */}
      <div style={{ marginBottom: 20 }}>
        <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--text-2)", marginBottom: 6 }}>{t("details.field.title")} *</label>
        <input
          type="text"
          data-testid="sell-title"
          value={form.title}
          onChange={(e) => set("title", e.target.value)}
          placeholder={t("details.placeholder.title")}
          style={{ borderColor: errors?.title ? "var(--error)" : undefined }}
        />
        <div style={{ display: "flex", justifyContent: "space-between", marginTop: 6 }}>
          <span style={{ fontSize: 12, color: errors?.title ? "var(--error)" : "var(--muted)" }}>
            {errors?.title || t("details.hint.title")}
          </span>
          <span style={{ fontSize: 12, color: form.title.length > 100 ? "var(--warning)" : "var(--muted)" }}>
            {form.title.length}/120
          </span>
        </div>
      </div>

      {/* Core fields grid */}
      <div className="grid-form" style={{ marginBottom: 20 }}>
        <div>
          <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--text-2)", marginBottom: 6 }}>{t("details.field.brand")}</label>
          <select data-testid="sell-brand" value={form.brand} onChange={(e) => set("brand", e.target.value)}>
            <option value="">{t("details.option.selectBrand")}</option>
            {brands.map(b => <option key={b} value={b}>{b}</option>)}
          </select>
        </div>
        <div>
          <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--text-2)", marginBottom: 6 }}>{t("details.field.category")} *</label>
          <select
            data-testid="sell-category"
            value={form.category}
            onChange={(e) => set("category", e.target.value)}
            style={{ borderColor: errors?.category ? "var(--error)" : undefined }}
          >
            <option value="">{t("details.option.selectCategory")}</option>
            {cats.map(c => <option key={c.slug} value={c.slug}>{c.name}</option>)}
          </select>
          {errors?.category && <p style={{ fontSize: 12, color: "var(--error)", marginTop: 4 }}>{errors.category}</p>}
        </div>
        <div>
          <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--text-2)", marginBottom: 6 }}>{t("details.field.gender")}</label>
          <select data-testid="sell-gender" value={form.gender} onChange={(e) => set("gender", e.target.value)}>
            <option value="">{t("details.option.none")}</option>
            {(meta.genders || []).map(g => <option key={g} value={g}>{g}</option>)}
          </select>
        </div>
        <div>
          <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--text-2)", marginBottom: 6 }}>{t("details.field.size")}</label>
          <select data-testid="sell-size" value={form.size} onChange={(e) => set("size", e.target.value)}>
            <option value="">{t("details.option.selectSize")}</option>
            {(meta.sizes || []).map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
        <div>
          <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--text-2)", marginBottom: 6 }}>{t("details.field.color")}</label>
          <select value={form.color} onChange={(e) => set("color", e.target.value)}>
            {COLORS.map(c => <option key={c} value={c}>{c || t("details.option.selectColor")}</option>)}
          </select>
        </div>
        <div>
          <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--text-2)", marginBottom: 6 }}>{t("details.field.material")}</label>
          <input
            type="text"
            data-testid="sell-material"
            value={form.material || ""}
            onChange={(e) => set("material", e.target.value)}
            placeholder={t("details.placeholder.material")}
          />
        </div>
        <div>
          <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--text-2)", marginBottom: 6 }}>{t("details.field.season")}</label>
          <select value={form.season || ""} onChange={(e) => set("season", e.target.value)}>
            {SEASONS.map(s => <option key={s} value={s}>{s || t("details.option.none")}</option>)}
          </select>
        </div>
        <div>
          <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--text-2)", marginBottom: 6 }}>{t("details.field.collection")}</label>
          <input
            type="text"
            value={form.collection || ""}
            onChange={(e) => set("collection", e.target.value)}
            placeholder={t("details.placeholder.collection")}
          />
        </div>
      </div>

      {/* Category-specific extra fields */}
      {extraFields.length > 0 && (
        <div style={{ marginBottom: 20, paddingTop: 8 }}>
          <p style={{ fontSize: 12, fontWeight: 600, color: "var(--text-2)", marginBottom: 14 }}>
            {t("details.section.categoryDetails", { category: selectedCat?.name || t("details.field.category") })}
          </p>
          <div className="grid-form">
            {extraFields.map(f => (
              <div key={f.key}>
                <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--text-2)", marginBottom: 6 }}>{f.label}</label>
                {f.type === "toggle" ? (
                  <label style={{
                    display: "flex", alignItems: "center", gap: 10,
                    fontSize: 14, cursor: "pointer", marginTop: 4,
                  }}>
                    <input type="checkbox" style={{ width: "auto", cursor: "pointer" }}
                      checked={!!extra[f.key]}
                      onChange={(e) => setExtra(f.key, e.target.checked)} />
                    Yes
                  </label>
                ) : f.type === "select" ? (
                  <select value={extra[f.key] || ""} onChange={(e) => setExtra(f.key, e.target.value)}>
                    {(f.options || []).map(o => <option key={o} value={o}>{o || "—"}</option>)}
                  </select>
                ) : (
                  <input
                    value={extra[f.key] || ""}
                    onChange={(e) => setExtra(f.key, e.target.value)}
                    placeholder={f.placeholder || ""}
                  />
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Description */}
      <div style={{ paddingTop: 8 }}>
        <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--text-2)", marginBottom: 6 }}>{t("details.field.description")}</label>
        <textarea
          data-testid="sell-description"
          rows={4}
          value={form.description || ""}
          onChange={(e) => set("description", e.target.value)}
          placeholder={t("details.placeholder.description")}
        />
        <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 4 }}>
          <span style={{ fontSize: 12, color: (form.description?.length || 0) >= 80 ? "var(--success)" : "var(--muted)" }}>
            {form.description?.length || 0} characters{(form.description?.length || 0) < 80 ? ` · ${t("details.hint.descriptionLength")}` : ` ${t("details.hint.descriptionComplete")}`}
          </span>
        </div>
      </div>
    </div>
  );
}
