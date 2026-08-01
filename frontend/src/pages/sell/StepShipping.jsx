import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { MapPin, Buildings, Globe } from "@phosphor-icons/react";

const SHIPS_TO_KEYS = [
  { value: "domestic", Icon: MapPin },
  { value: "europe", Icon: Buildings },
  { value: "worldwide", Icon: Globe },
];

const COUNTRIES = [
  "Ukraine", "Germany", "France", "Italy", "Spain",
  "United Kingdom", "Netherlands", "Belgium", "Poland", "Austria",
  "Switzerland", "Sweden", "Denmark", "Norway", "Finland",
  "Portugal", "Greece", "Czechia", "Hungary", "Romania",
  "Serbia", "Croatia", "Bulgaria", "Slovakia", "Slovenia",
  "Estonia", "Latvia", "Lithuania", "Georgia", "Armenia",
  "USA", "Canada", "Australia", "Japan", "South Korea",
  "Turkey", "UAE", "Israel", "Brazil", "Other",
];

function parseLocation(str) {
  if (!str) return { city: "", country: "Ukraine" };
  const idx = str.lastIndexOf(", ");
  if (idx === -1) return { city: "", country: str };
  return { city: str.slice(0, idx), country: str.slice(idx + 2) };
}

export default function StepShipping({ form, onChange }) {
  const { t } = useTranslation("sell");
  const SHIPS_TO = SHIPS_TO_KEYS.map(({ value, Icon }) => ({
    value, Icon, label: t(`shipping.option.${value}`), desc: t(`shipping.desc.${value}`),
  }));
  const set = (k, v) => onChange({ ...form, [k]: v });

  const initial = parseLocation(form.ships_from_region);
  const [country, setCountry] = useState(initial.country || "Ukraine");
  const [city, setCity] = useState(initial.city);

  const updateLocation = (newCountry, newCity) => {
    const combined = newCity.trim() ? `${newCity.trim()}, ${newCountry}` : newCountry;
    set("ships_from_region", combined);
  };

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: 22, fontWeight: 700, letterSpacing: "-0.02em", marginBottom: 8 }}>
          {t("shipping.heading")}
        </h2>
        <p style={{ fontSize: 14, color: "var(--text-2)", lineHeight: 1.6 }}>
          {t("shipping.description")}
        </p>
      </div>

      {/* Ships from */}
      <div style={{ marginBottom: 24 }}>
        <p style={{ fontSize: 12, fontWeight: 600, color: "var(--text-2)", marginBottom: 10 }}>
          {t("shipping.section.shipsFrom")}
        </p>
        <div className="grid-form" style={{ maxWidth: 580 }}>
          <div>
            <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--text-2)", marginBottom: 6 }}>{t("shipping.field.country")}</label>
            <select
              value={country}
              onChange={(e) => {
                setCountry(e.target.value);
                updateLocation(e.target.value, city);
              }}
            >
              {COUNTRIES.map(c => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
          <div>
            <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--text-2)", marginBottom: 6 }}>{t("shipping.field.city")}</label>
            <input
              type="text"
              value={city}
              onChange={(e) => {
                setCity(e.target.value);
                updateLocation(country, e.target.value);
              }}
              placeholder={t("shipping.placeholder.city")}
            />
          </div>
        </div>
      </div>

      {/* Ships to */}
      <div style={{ marginBottom: 24 }}>
        <p style={{ fontSize: 12, fontWeight: 600, color: "var(--text-2)", marginBottom: 10 }}>
          {t("shipping.section.shipsTo")}
        </p>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {SHIPS_TO.map(({ value, Icon, label, desc }) => {
            const selected = form.ships_to === value;
            return (
              <label
                key={value}
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
                  name="ships_to"
                  value={value}
                  checked={selected}
                  onChange={() => set("ships_to", value)}
                  style={{ width: "auto", marginTop: 2, accentColor: "var(--text)" }}
                />
                <Icon size={18} color={selected ? "var(--text)" : "var(--muted)"} weight={selected ? "bold" : "regular"} />
                <div>
                  <div style={{ fontSize: 14, fontWeight: 600 }}>{label}</div>
                  <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 2 }}>{desc}</div>
                </div>
              </label>
            );
          })}
        </div>
      </div>

      {/* Shipping notes */}
      <div>
        <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--text-2)", marginBottom: 6 }}>{t("shipping.field.notes")}</label>
        <textarea
          rows={2}
          value={form.shipping_notes || ""}
          onChange={(e) => set("shipping_notes", e.target.value)}
          placeholder={t("shipping.placeholder.notes")}
        />
      </div>
    </div>
  );
}
