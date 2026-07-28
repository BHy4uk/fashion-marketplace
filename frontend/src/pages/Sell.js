import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import api, { apiError } from "../lib/api";

const empty = {
  title: "", description: "", brand: "", category: "", gender: "", size: "",
  color: "", material: "", condition: "", season: "", price_amount: "", currency: "UAH",
  allow_offers: true,
};

export default function Sell() {
  const navigate = useNavigate();
  const [form, setForm] = useState(empty);
  const [images, setImages] = useState([""]);
  const [meta, setMeta] = useState({ conditions: [], genders: [], sizes: [], currencies: ["UAH"] });
  const [cats, setCats] = useState([]);
  const [brands, setBrands] = useState([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get("/taxonomy/meta").then((r) => setMeta(r.data)).catch(() => {});
    api.get("/taxonomy/categories").then((r) => setCats(r.data.categories)).catch(() => {});
    api.get("/taxonomy/brands").then((r) => setBrands(r.data.brands)).catch(() => {});
  }, []);

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const payload = {
        ...form,
        price_amount: Math.round(parseFloat(form.price_amount) * 100),
        images: images.filter((u) => u.trim()).map((u) => ({ url: u.trim() })),
      };
      const { data } = await api.post("/listings", payload);
      await api.post(`/listings/${data.listing_id}/publish`);
      toast.success("Listing published");
      navigate(`/listing/${data.slug}`);
    } catch (err) {
      setError(apiError(err));
      toast.error(apiError(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="container" style={{ maxWidth: 820, paddingTop: 24, paddingBottom: 60 }}>
      <span className="overline">Sell in under a minute</span>
      <h1 style={{ fontSize: 28, margin: "6px 0 20px" }}>Create a listing</h1>
      <form onSubmit={submit} className="panel stack" style={{ gap: 16 }}>
        <div>
          <label className="field overline">Title *</label>
          <input data-testid="sell-title" value={form.title}
            onChange={(e) => set("title", e.target.value)} required
            placeholder="e.g. Stone Island Shadow Jacket" />
        </div>

        <div>
          <label className="field overline">Photos (image URLs) *</label>
          {images.map((url, i) => (
            <input key={i} data-testid={`sell-image-${i}`} value={url} className="mb-12"
              placeholder="https://…"
              onChange={(e) => setImages((im) => im.map((x, j) => (j === i ? e.target.value : x)))} />
          ))}
          <button type="button" className="btn btn-sm" data-testid="sell-add-image"
            onClick={() => setImages((im) => [...im, ""])}>+ Add another photo</button>
        </div>

        <div className="grid-form">
          <div>
            <label className="field overline">Brand</label>
            <select data-testid="sell-brand" value={form.brand} onChange={(e) => set("brand", e.target.value)}>
              <option value="">Select brand</option>
              {brands.map((b) => <option key={b} value={b}>{b}</option>)}
            </select>
          </div>
          <div>
            <label className="field overline">Category *</label>
            <select data-testid="sell-category" value={form.category}
              onChange={(e) => set("category", e.target.value)} required>
              <option value="">Select category</option>
              {cats.map((c) => <option key={c.slug} value={c.slug}>{c.name}</option>)}
            </select>
          </div>
          <div>
            <label className="field overline">Condition *</label>
            <select data-testid="sell-condition" value={form.condition}
              onChange={(e) => set("condition", e.target.value)} required>
              <option value="">Select condition</option>
              {meta.conditions.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
            </select>
          </div>
          <div>
            <label className="field overline">Size</label>
            <select data-testid="sell-size" value={form.size} onChange={(e) => set("size", e.target.value)}>
              <option value="">Select size</option>
              {meta.sizes.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div>
            <label className="field overline">Gender</label>
            <select data-testid="sell-gender" value={form.gender} onChange={(e) => set("gender", e.target.value)}>
              <option value="">—</option>
              {meta.genders.map((g) => <option key={g} value={g}>{g}</option>)}
            </select>
          </div>
          <div>
            <label className="field overline">Color</label>
            <input data-testid="sell-color" value={form.color} onChange={(e) => set("color", e.target.value)} />
          </div>
          <div>
            <label className="field overline">Material</label>
            <input data-testid="sell-material" value={form.material} onChange={(e) => set("material", e.target.value)} />
          </div>
          <div>
            <label className="field overline">Price ({form.currency}) *</label>
            <input data-testid="sell-price" type="number" min="1" step="0.01" value={form.price_amount}
              onChange={(e) => set("price_amount", e.target.value)} required placeholder="e.g. 4200" />
          </div>
        </div>

        <div>
          <label className="field overline">Description</label>
          <textarea data-testid="sell-description" rows={4} value={form.description}
            onChange={(e) => set("description", e.target.value)}
            placeholder="Condition details, measurements, flaws…" />
        </div>

        <label className="row" style={{ gap: 8, fontSize: 14 }}>
          <input type="checkbox" style={{ width: "auto" }} checked={form.allow_offers}
            data-testid="sell-allow-offers"
            onChange={(e) => set("allow_offers", e.target.checked)} />
          Allow buyers to make offers
        </label>

        {error && <div className="error-text" data-testid="sell-error">{error}</div>}
        <button className="btn btn-primary btn-block" disabled={busy} data-testid="sell-submit">
          {busy ? "Publishing…" : "Publish listing"}
        </button>
      </form>
    </div>
  );
}
