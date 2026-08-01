import React, { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";
import { X, UploadSimple } from "@phosphor-icons/react";
import api, { apiError } from "../lib/api";

function fileToDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => resolve(e.target.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

export default function EditListing() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { t } = useTranslation("sell");
  const [form, setForm] = useState(null);
  const [photos, setPhotos] = useState([]); // {type:'existing'|'new', url, preview?, dataUrl?}
  const [meta, setMeta] = useState({ conditions: [], genders: [], sizes: [] });
  const [cats, setCats] = useState([]);
  const [brands, setBrands] = useState([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(true);
  const fileInputRef = useRef();

  useEffect(() => {
    Promise.all([
      api.get(`/listings/${id}`),
      api.get("/taxonomy/meta").catch(() => ({ data: { conditions: [], genders: [], sizes: [] } })),
      api.get("/taxonomy/categories").catch(() => ({ data: { categories: [] } })),
      api.get("/taxonomy/brands").catch(() => ({ data: { brands: [] } })),
    ]).then(([listingRes, metaRes, catsRes, brandsRes]) => {
      const l = listingRes.data.listing;
      const a = l.attributes || {};
      setForm({
        title: l.title || "",
        description: l.description || "",
        brand: a.brand || "",
        category: a.category || "",
        gender: a.gender || "",
        size: a.size || "",
        color: a.color || "",
        material: a.material || "",
        condition: a.condition || "",
        season: a.season || "",
        price_amount: l.price ? String(l.price.amount / 100) : "",
        currency: l.price?.currency || "UAH",
        allow_offers: l.allow_offers !== false,
      });
      setPhotos((l.images || []).map((img) => ({ type: "existing", url: img.url })));
      setMeta(metaRes.data);
      setCats(catsRes.data.categories || []);
      setBrands(brandsRes.data.brands || []);
      setLoading(false);
    }).catch(() => {
      toast.error(t("edit.toastError"));
      navigate("/dashboard");
    });
  }, [id, navigate]);

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const addFiles = async (files) => {
    const accepted = Array.from(files).filter((f) => f.type.startsWith("image/")).slice(0, 10 - photos.length);
    if (!accepted.length) return;
    const entries = await Promise.all(
      accepted.map(async (f) => {
        const dataUrl = await fileToDataUrl(f);
        return { type: "new", preview: URL.createObjectURL(f), dataUrl };
      })
    );
    setPhotos((prev) => [...prev, ...entries]);
  };

  const removePhoto = (i) => setPhotos((prev) => prev.filter((_, j) => j !== i));
  const onFileChange = (e) => { addFiles(e.target.files); e.target.value = ""; };
  const onDrop = (e) => { e.preventDefault(); setDragging(false); addFiles(e.dataTransfer.files); };
  const onDragOver = (e) => { e.preventDefault(); setDragging(true); };
  const onDragLeave = () => setDragging(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    if (photos.length === 0) {
      setError("Add at least one photo.");
      return;
    }
    setBusy(true);
    try {
      const payload = {
        ...form,
        price_amount: Math.round(parseFloat(form.price_amount) * 100),
        images: photos.map((p) => ({ url: p.type === "existing" ? p.url : p.dataUrl })),
      };
      await api.patch(`/listings/${id}`, payload);
      toast.success(t("edit.toastUpdated"));
      navigate("/dashboard");
    } catch (err) {
      setError(apiError(err));
      toast.error(apiError(err));
    } finally {
      setBusy(false);
    }
  };

  if (loading) return (
    <div style={{ display: "flex", justifyContent: "center", padding: "80px 0" }}>
      <div className="spin" />
    </div>
  );

  return (
    <div className="container" style={{ maxWidth: 760, paddingTop: 28, paddingBottom: 80 }}>
      <div className="row" style={{ justifyContent: "space-between", alignItems: "center", marginBottom: 32 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, letterSpacing: "-0.02em", margin: 0 }}>
          {t("edit.heading")}
        </h1>
        <button className="btn btn-sm" onClick={() => navigate("/dashboard")}>{t("edit.cancel")}</button>
      </div>

      <form onSubmit={submit} className="stack" style={{ gap: 32 }}>

        {/* Photos */}
        <div>
          <label className="field overline" style={{ marginBottom: 12, display: "block" }}>{t("photos.heading")} *</label>
          {photos.length > 0 && (
            <div style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(100px, 1fr))",
              gap: 8,
              marginBottom: 12,
            }}>
              {photos.map((p, i) => (
                <div key={i} style={{ position: "relative", aspectRatio: "1", borderRadius: 8, overflow: "hidden", background: "var(--subtle)" }}>
                  <img
                    src={p.type === "existing" ? p.url : p.preview}
                    alt=""
                    style={{ width: "100%", height: "100%", objectFit: "cover" }}
                    onError={(e) => { e.currentTarget.style.display = "none"; }}
                  />
                  <button
                    type="button"
                    onClick={() => removePhoto(i)}
                    style={{
                      position: "absolute", top: 4, right: 4,
                      width: 22, height: 22, borderRadius: "50%",
                      background: "rgba(0,0,0,0.55)", border: "none", cursor: "pointer",
                      display: "grid", placeItems: "center", padding: 0,
                    }}>
                    <X size={12} color="#fff" weight="bold" />
                  </button>
                </div>
              ))}
            </div>
          )}
          <div
            onClick={() => fileInputRef.current?.click()}
            onDrop={onDrop}
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            style={{
              border: `2px dashed ${dragging ? "var(--text)" : "var(--border-strong)"}`,
              borderRadius: 12,
              padding: "20px",
              display: "flex", alignItems: "center", gap: 10,
              cursor: "pointer",
              transition: "border-color 0.15s",
            }}>
            <UploadSimple size={20} weight="light" color="var(--muted)" />
            <div style={{ fontSize: 13, color: "var(--text-2)" }}>
              {t("edit.addMorePhotos")}
            </div>
          </div>
          <input ref={fileInputRef} type="file" accept="image/*" multiple style={{ display: "none" }} onChange={onFileChange} />
        </div>

        {/* Title */}
        <div>
          <label className="field overline">{t("details.field.title")} *</label>
          <input value={form.title} onChange={(e) => set("title", e.target.value)} required
            placeholder={t("details.placeholder.title")} />
        </div>

        {/* Details */}
        <div>
          <div className="overline" style={{ marginBottom: 16, color: "var(--muted)", fontSize: 11 }}>Item details</div>
          <div className="grid-form">
            <div>
              <label className="field overline">{t("details.field.brand")}</label>
              <select value={form.brand} onChange={(e) => set("brand", e.target.value)}>
                <option value="">{t("details.option.selectBrand")}</option>
                {brands.map((b) => <option key={b} value={b}>{b}</option>)}
              </select>
            </div>
            <div>
              <label className="field overline">{t("details.field.category")} *</label>
              <select value={form.category} onChange={(e) => set("category", e.target.value)} required>
                <option value="">{t("details.option.selectCategory")}</option>
                {cats.map((c) => <option key={c.slug} value={c.slug}>{c.name}</option>)}
              </select>
            </div>
            <div>
              <label className="field overline">{t("condition.field.condition")} *</label>
              <select value={form.condition} onChange={(e) => set("condition", e.target.value)} required>
                <option value="">{t("condition.field.condition")}</option>
                {meta.conditions.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
              </select>
            </div>
            <div>
              <label className="field overline">{t("details.field.size")}</label>
              <select value={form.size} onChange={(e) => set("size", e.target.value)}>
                <option value="">{t("details.option.selectSize")}</option>
                {meta.sizes.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label className="field overline">{t("details.field.gender")}</label>
              <select value={form.gender} onChange={(e) => set("gender", e.target.value)}>
                <option value="">{t("details.option.none")}</option>
                {meta.genders.map((g) => <option key={g} value={g}>{g}</option>)}
              </select>
            </div>
            <div>
              <label className="field overline">{t("details.field.color")}</label>
              <input value={form.color} onChange={(e) => set("color", e.target.value)} />
            </div>
            <div>
              <label className="field overline">{t("details.field.material")}</label>
              <input value={form.material} onChange={(e) => set("material", e.target.value)} />
            </div>
          </div>
        </div>

        {/* Description */}
        <div>
          <label className="field overline">{t("details.field.description")}</label>
          <textarea rows={4} value={form.description}
            onChange={(e) => set("description", e.target.value)}
            placeholder={t("details.placeholder.description")} />
        </div>

        {/* Pricing */}
        <div>
          <div className="overline" style={{ marginBottom: 16, color: "var(--muted)", fontSize: 11 }}>Pricing</div>
          <label className="field overline">{t("pricing.field.price", { currency: form.currency })} *</label>
          <input type="number" min="1" step="0.01" value={form.price_amount}
            onChange={(e) => set("price_amount", e.target.value)} required
            placeholder="e.g. 4200" style={{ maxWidth: 240 }} />
          <label className="row" style={{ gap: 10, fontSize: 14, marginTop: 14 }}>
            <input type="checkbox" style={{ width: "auto" }} checked={form.allow_offers}
              onChange={(e) => set("allow_offers", e.target.checked)} />
            {t("pricing.field.allowOffers")}
          </label>
        </div>

        {error && <div className="error-text">{error}</div>}

        <div className="row" style={{ gap: 12 }}>
          <button className="btn btn-primary" disabled={busy} style={{ height: 48, flex: 1 }}>
            {busy ? t("edit.saving") : t("edit.saveChanges")}
          </button>
        </div>
      </form>
    </div>
  );
}
