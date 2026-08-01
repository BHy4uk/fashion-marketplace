import React, { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { AnimatePresence, motion } from "framer-motion";
import { toast } from "sonner";
import { ArrowLeft, ArrowRight } from "@phosphor-icons/react";
import api, { apiError } from "../lib/api";
import WizardProgress from "./sell/WizardProgress.jsx";
import StepPhotos from "./sell/StepPhotos.jsx";
import StepDetails from "./sell/StepDetails.jsx";
import StepCondition from "./sell/StepCondition.jsx";
import StepPricing from "./sell/StepPricing.jsx";
import StepShipping from "./sell/StepShipping.jsx";
import StepReview from "./sell/StepReview.jsx";

const DRAFT_KEY = "archive_listing_draft_v2";

const EMPTY = {
  photos: [],
  title: "", brand: "", category: "", gender: "", size: "", color: "",
  material: "", condition: "", season: "", collection: "", description: "",
  extra: {},
  condition_notes: "",
  has_authentication: false, has_receipt: false, has_original_packaging: false,
  measurements: {},
  price_amount: "", currency: "UAH", allow_offers: true, min_offer: "",
  ships_from_region: "", ships_to: "worldwide", shipping_notes: "",
};

function validateStep(step, draft) {
  switch (step) {
    case 0:
      return draft.photos.length >= 1 ? null : "Add at least one photo to continue";
    case 1:
      if (!draft.title.trim()) return "A title is required";
      if (draft.title.trim().length < 3) return "Title is too short";
      if (!draft.category) return "Select a category to continue";
      return null;
    case 2:
      return draft.condition ? null : "Select the item condition to continue";
    case 3: {
      const p = parseFloat(draft.price_amount || 0);
      return p > 0 ? null : "Set a listing price to continue";
    }
    default:
      return null;
  }
}

function buildDescription(draft) {
  const parts = [];
  if (draft.description) parts.push(draft.description);
  const ms = Object.entries(draft.measurements || {}).filter(([, v]) => v);
  if (ms.length > 0) {
    parts.push(
      "\n\nMeasurements (cm): " +
      ms.map(([k, v]) => `${k.replace(/_/g, " ")} ${v}`).join(", ")
    );
  }
  if (draft.condition_notes) parts.push("\n\nCondition: " + draft.condition_notes);
  if (draft.shipping_notes) parts.push("\n\nShipping: " + draft.shipping_notes);
  return parts.join("").trim();
}

const stepVariants = {
  enter: (d) => ({ opacity: 0, x: d > 0 ? 28 : -28 }),
  center: { opacity: 1, x: 0 },
  exit: (d) => ({ opacity: 0, x: d > 0 ? -16 : 16 }),
};
const stepTransition = { duration: 0.18, ease: [0, 0, 0.2, 1] };

export default function Sell() {
  const navigate = useNavigate();
  const { t } = useTranslation("sell");
  const [step, setStep] = useState(0);
  const [direction, setDirection] = useState(1);
  const [completed, setCompleted] = useState(new Set());
  const [draft, setDraft] = useState(EMPTY);
  const [stepError, setStepError] = useState(null);
  const [busy, setBusy] = useState(false);
  const [hasDraftBanner, setHasDraftBanner] = useState(false);
  const [meta, setMeta] = useState({ conditions: [], genders: [], sizes: [] });
  const [cats, setCats] = useState([]);
  const [brands, setBrands] = useState([]);
  const isDirty = useRef(false);

  // Load taxonomy data
  useEffect(() => {
    api.get("/taxonomy/meta").then(r => setMeta(r.data)).catch(() => {});
    api.get("/taxonomy/categories").then(r => setCats(r.data.categories || [])).catch(() => {});
    api.get("/taxonomy/brands").then(r => setBrands(r.data.brands || [])).catch(() => {});
  }, []);

  // Check for saved draft
  useEffect(() => {
    try {
      const saved = localStorage.getItem(DRAFT_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.title || parsed.price_amount || parsed.brand) {
          setHasDraftBanner(true);
        }
      }
    } catch (_) {}
  }, []);

  // Auto-save (text fields only — photos are too large)
  useEffect(() => {
    const { photos: _, ...saveable } = draft;
    const hasContent = saveable.title || saveable.price_amount || saveable.brand;
    if (!hasContent) return;
    isDirty.current = true;
    const timer = setTimeout(() => {
      try { localStorage.setItem(DRAFT_KEY, JSON.stringify(saveable)); } catch (_) {}
    }, 800);
    return () => clearTimeout(timer);
  }, [draft]);

  // Browser leave warning
  useEffect(() => {
    const handler = (e) => {
      if (isDirty.current) { e.preventDefault(); e.returnValue = ""; }
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, []);

  const restoreDraft = () => {
    try {
      const saved = localStorage.getItem(DRAFT_KEY);
      if (saved) {
        const { photos: _, ...data } = JSON.parse(saved);
        setDraft(prev => ({ ...prev, ...data }));
      }
    } catch (_) {}
    setHasDraftBanner(false);
  };

  const updateDraft = useCallback((updates) => {
    setDraft(prev =>
      typeof updates === "function" ? updates(prev) : { ...prev, ...updates }
    );
  }, []);

  const goTo = (target) => {
    setDirection(target > step ? 1 : -1);
    setStepError(null);
    setStep(target);
  };

  const next = () => {
    const err = validateStep(step, draft);
    if (err) { setStepError(err); toast.error(err); return; }
    setStepError(null);
    setCompleted(prev => new Set([...prev, step]));
    goTo(step + 1);
  };

  const back = () => goTo(step - 1);

  const publish = async () => {
    setBusy(true);
    try {
      const payload = {
        title: draft.title.trim(),
        description: buildDescription(draft),
        price_amount: Math.round(parseFloat(draft.price_amount) * 100),
        currency: draft.currency || "UAH",
        brand: draft.brand,
        category: draft.category,
        gender: draft.gender,
        size: draft.size,
        color: draft.color,
        material: draft.material,
        condition: draft.condition,
        season: draft.season,
        allow_offers: draft.allow_offers,
        images: draft.photos.map(p => ({ url: p.dataUrl })),
      };
      const { data } = await api.post("/listings", payload);
      await api.post(`/listings/${data.listing_id}/publish`);
      isDirty.current = false;
      localStorage.removeItem(DRAFT_KEY);
      toast.success(t("toast.published"));
      navigate(`/listing/${data.slug || data.listing_id}`);
    } catch (err) {
      toast.error(apiError(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="container" style={{ maxWidth: 680, paddingTop: 36, paddingBottom: 100 }}>

      {/* Draft restore banner */}
      {hasDraftBanner && (
        <div style={{
          marginBottom: 24, padding: "12px 16px",
          background: "var(--subtle)", borderRadius: 10,
          display: "flex", alignItems: "center", justifyContent: "space-between",
          fontSize: 13,
        }}>
          <span style={{ color: "var(--text-2)" }}>{t("draft.restoreBanner")}</span>
          <div style={{ display: "flex", gap: 16 }}>
            <button type="button" onClick={restoreDraft}
              style={{ fontSize: 13, fontWeight: 600, color: "var(--text)", background: "none", border: "none", cursor: "pointer" }}>
              {t("draft.restoreButton")}
            </button>
            <button type="button" onClick={() => setHasDraftBanner(false)}
              style={{ fontSize: 13, color: "var(--muted)", background: "none", border: "none", cursor: "pointer" }}>
              {t("draft.dismissButton")}
            </button>
          </div>
        </div>
      )}

      <WizardProgress current={step} completed={completed} onStepClick={goTo} />

      {/* Animated step panels */}
      <AnimatePresence mode="wait" custom={direction}>
        <motion.div
          key={step}
          custom={direction}
          variants={stepVariants}
          initial="enter"
          animate="center"
          exit="exit"
          transition={stepTransition}
        >
          {step === 0 && (
            <StepPhotos
              photos={draft.photos}
              onChange={(p) => updateDraft({ photos: p })}
              error={stepError}
            />
          )}
          {step === 1 && (
            <StepDetails
              form={draft}
              onChange={updateDraft}
              meta={meta}
              cats={cats}
              brands={brands}
              errors={stepError ? { title: stepError } : {}}
            />
          )}
          {step === 2 && (
            <StepCondition
              form={draft}
              onChange={updateDraft}
              errors={stepError ? { condition: stepError } : {}}
            />
          )}
          {step === 3 && (
            <StepPricing
              form={draft}
              onChange={updateDraft}
              errors={stepError ? { price_amount: stepError } : {}}
            />
          )}
          {step === 4 && (
            <StepShipping
              form={draft}
              onChange={updateDraft}
            />
          )}
          {step === 5 && (
            <StepReview
              draft={draft}
              onGoToStep={goTo}
              onPublish={publish}
              busy={busy}
            />
          )}
        </motion.div>
      </AnimatePresence>

      {/* Previous / Next navigation (hidden on review step) */}
      {step < 5 && (
        <div style={{
          display: "flex",
          justifyContent: step === 0 ? "flex-end" : "space-between",
          alignItems: "center",
          marginTop: 40,
          paddingTop: 24,
          borderTop: "1px solid var(--border)",
        }}>
          {step > 0 && (
            <button type="button" onClick={back} className="btn"
              style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <ArrowLeft size={14} />
              {t("wizard.button.back")}
            </button>
          )}
          <button type="button" onClick={next} className="btn btn-primary"
            style={{ display: "flex", alignItems: "center", gap: 6, minWidth: 130 }}>
            {t("wizard.button.next")}
            <ArrowRight size={14} />
          </button>
        </div>
      )}
    </div>
  );
}


