import React, { useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { UploadSimple, X, FrameCorners } from "@phosphor-icons/react";

function fileToDataUrl(file) {
  return new Promise((res, rej) => {
    const r = new FileReader();
    r.onload = (e) => res(e.target.result);
    r.onerror = rej;
    r.readAsDataURL(file);
  });
}

export default function StepPhotos({ photos, onChange, error }) {
  const { t } = useTranslation("sell");
  const ANGLE_TIPS = [
    t("photos.tip.front"), t("photos.tip.back"), t("photos.tip.label"),
    t("photos.tip.flaws"), t("photos.tip.detail"),
  ];
  const [dropActive, setDropActive] = useState(false);
  const [dragIdx, setDragIdx] = useState(null);
  const [overIdx, setOverIdx] = useState(null);
  const fileRef = useRef();

  const addFiles = async (files) => {
    const accepted = Array.from(files)
      .filter(f => f.type.startsWith("image/"))
      .slice(0, 10 - photos.length);
    if (!accepted.length) return;
    const entries = await Promise.all(
      accepted.map(async f => ({
        preview: URL.createObjectURL(f),
        dataUrl: await fileToDataUrl(f),
      }))
    );
    onChange([...photos, ...entries]);
  };

  const remove = (i) => onChange(photos.filter((_, j) => j !== i));

  const onZoneDrop = (e) => {
    e.preventDefault();
    setDropActive(false);
    addFiles(e.dataTransfer.files);
  };

  const onPhotoDragStart = (i) => setDragIdx(i);
  const onPhotoDragEnd = () => { setDragIdx(null); setOverIdx(null); };
  const onPhotoDragOver = (e, i) => { e.preventDefault(); setOverIdx(i); };
  const onPhotoDrop = (i) => {
    if (dragIdx === null || dragIdx === i) return;
    const next = [...photos];
    const [item] = next.splice(dragIdx, 1);
    next.splice(i, 0, item);
    onChange(next);
    setDragIdx(null);
    setOverIdx(null);
  };

  const remaining = 10 - photos.length;

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: 22, fontWeight: 700, letterSpacing: "-0.02em", marginBottom: 8 }}>
          {t("photos.heading")}
        </h2>
        <p style={{ fontSize: 14, color: "var(--text-2)", lineHeight: 1.6 }}>
          {t("photos.description")}
        </p>
      </div>

      {/* Drop zone */}
      <div
        data-testid="sell-dropzone"
        onClick={() => fileRef.current?.click()}
        onDrop={onZoneDrop}
        onDragOver={(e) => { e.preventDefault(); setDropActive(true); }}
        onDragLeave={() => setDropActive(false)}
        role="button"
        aria-label={t("photos.aria.upload")}
        style={{
          border: `1.5px dashed ${dropActive ? "var(--text)" : error ? "var(--error)" : "var(--border-strong)"}`,
          borderRadius: 12,
          background: dropActive ? "var(--subtle)" : "var(--surface)",
          padding: photos.length > 0 ? "18px 24px" : "52px 24px",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 8,
          cursor: "pointer",
          transition: "all 0.15s",
          userSelect: "none",
        }}
      >
        <UploadSimple size={24} weight="light" color="var(--muted)" />
        <span style={{ fontSize: 14, fontWeight: 500, color: "var(--text-2)" }}>
          {t("photos.action.dragOrChoose")}
        </span>
        <span style={{ fontSize: 12, color: "var(--muted)" }}>
          {t("photos.format.supported")}{remaining < 10 ? t("photos.format.remaining", { count: remaining }) : t("photos.format.max")}
        </span>
      </div>
      <input ref={fileRef} type="file" accept="image/*" multiple style={{ display: "none" }}
        data-testid="sell-image-input"
        onChange={(e) => { addFiles(e.target.files); e.target.value = ""; }} />

      {/* Guidance tips — shown only when empty */}
      {photos.length === 0 && (
        <div style={{ marginTop: 20 }}>
          <p style={{ fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--muted)", fontWeight: 600, marginBottom: 10 }}>
            {t("photos.section.angles")}
          </p>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            {ANGLE_TIPS.map((tip, i) => (
              <span key={i} style={{
                display: "flex", alignItems: "center", gap: 5,
                fontSize: 12, color: "var(--text-2)",
                background: "var(--subtle)", borderRadius: 999, padding: "4px 10px",
              }}>
                <FrameCorners size={11} color="var(--muted)" />
                {tip}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Photo grid with reorder */}
      {photos.length > 0 && (
        <div style={{ marginTop: 14 }}>
          <div style={{
            display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10,
          }}>
            <span style={{ fontSize: 12, color: "var(--muted)" }}>
              {t("photos.hint.reorder", { count: photos.length })}
            </span>
            {photos.length < 3 && (
              <span style={{ fontSize: 12, color: "var(--warning)", fontWeight: 500 }}>
                  {t("photos.warning.addMore", { count: 3 - photos.length })}
              </span>
            )}
          </div>
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(100px, 1fr))",
            gap: 8,
          }}>
            {photos.map((p, i) => (
              <div
                key={i}
                draggable
                onDragStart={() => onPhotoDragStart(i)}
                onDragEnd={onPhotoDragEnd}
                onDragOver={(e) => onPhotoDragOver(e, i)}
                onDrop={() => onPhotoDrop(i)}
                style={{
                  position: "relative",
                  aspectRatio: "1",
                  borderRadius: 8,
                  overflow: "hidden",
                  background: "var(--subtle)",
                  cursor: "grab",
                  outline: overIdx === i && dragIdx !== i ? "2px solid var(--text)" : "none",
                  opacity: dragIdx === i ? 0.45 : 1,
                  transition: "opacity 0.12s",
                }}
              >
                <img src={p.preview} alt="" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                {i === 0 && (
                  <div style={{
                    position: "absolute", bottom: 4, left: 4,
                    background: "rgba(0,0,0,0.62)", borderRadius: 4,
                    padding: "2px 6px", fontSize: 9, fontWeight: 700,
                    color: "#fff", letterSpacing: "0.08em", textTransform: "uppercase",
                  }}>
                    {t("photos.badge.cover")}
                  </div>
                )}
                <button
                  type="button"
                  onClick={() => remove(i)}
                  aria-label={t("photos.aria.remove")}
                  style={{
                    position: "absolute", top: 4, right: 4,
                    width: 22, height: 22, borderRadius: "50%",
                    background: "rgba(0,0,0,0.55)", border: "none",
                    cursor: "pointer", display: "grid", placeItems: "center", padding: 0,
                  }}
                >
                  <X size={11} color="#fff" weight="bold" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {error && (
        <p style={{ marginTop: 12, fontSize: 12, color: "var(--error)" }}>{error}</p>
      )}
    </div>
  );
}
