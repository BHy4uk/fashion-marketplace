import React from "react";
import { useTranslation } from "react-i18next";
import { Check } from "@phosphor-icons/react";

const STEP_KEYS = ["photos", "details", "condition", "pricing", "shipping", "review"];

export default function WizardProgress({ current, completed, onStepClick }) {
  const { t } = useTranslation("sell");
  const STEPS = STEP_KEYS.map(k => t(`wizard.step.${k}`));
  const progress = ((current + 1) / STEPS.length) * 100;

  return (
    <nav aria-label={t("wizard.stepsAria")} style={{ marginBottom: 40 }}>

      {/* Current step label */}
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
        <span style={{
          fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase",
          fontWeight: 600, color: "var(--muted)",
        }}>
          {t("wizard.stepLabel", { current: current + 1, total: STEPS.length })}
        </span>
        <span style={{ color: "var(--border-strong)", fontSize: 11 }}>·</span>
        <span style={{ fontSize: 13, fontWeight: 700, color: "var(--text)" }}>
          {STEPS[current]}
        </span>
      </div>

      {/* Animated progress bar */}
      <div style={{ height: 2, background: "var(--border)", borderRadius: 1, marginBottom: 20 }}>
        <div style={{
          height: "100%",
          width: `${progress}%`,
          background: "var(--text)",
          borderRadius: 1,
          transition: "width 0.24s cubic-bezier(0,0,0.2,1)",
        }} />
      </div>

      {/* Step circles with labels */}
      <div style={{ display: "flex", alignItems: "flex-start" }}>
        {STEPS.map((label, i) => {
          const isDone = completed.has(i);
          const isActive = current === i;
          const isClickable = isDone && !isActive;

          return (
            <React.Fragment key={i}>
              <button
                type="button"
                onClick={() => isClickable && onStepClick(i)}
                disabled={!isClickable && !isActive}
                aria-current={isActive ? "step" : undefined}
                aria-label={isDone ? t("wizard.completedAria", { label }) : label}
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  gap: 6,
                  background: "none",
                  border: "none",
                  padding: 0,
                  cursor: isClickable ? "pointer" : "default",
                  opacity: !isDone && !isActive ? 0.3 : 1,
                  transition: "opacity 0.15s",
                  flexShrink: 0,
                }}
              >
                <div style={{
                  width: 26,
                  height: 26,
                  borderRadius: "50%",
                  background: isActive || isDone ? "var(--text)" : "transparent",
                  border: `1.5px solid ${isActive || isDone ? "var(--text)" : "var(--border-strong)"}`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  transition: "all 0.18s",
                }}>
                  {isDone && !isActive
                    ? <Check size={12} weight="bold" color="#fff" />
                    : <span style={{
                        fontSize: 10,
                        fontWeight: 700,
                        color: isActive ? "#fff" : "var(--text-2)",
                        lineHeight: 1,
                      }}>{i + 1}</span>
                  }
                </div>
                <span style={{
                  fontSize: 10,
                  letterSpacing: "0.07em",
                  textTransform: "uppercase",
                  fontWeight: isActive ? 700 : 500,
                  color: isActive ? "var(--text)" : isDone ? "var(--text-2)" : "var(--muted)",
                  whiteSpace: "nowrap",
                }}>
                  {label}
                </span>
              </button>

              {i < STEPS.length - 1 && (
                <div style={{
                  flex: 1,
                  height: 1,
                  background: i < current ? "var(--text)" : "var(--border)",
                  marginTop: 13,
                  transition: "background 0.24s",
                  minWidth: 8,
                }} />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </nav>
  );
}
