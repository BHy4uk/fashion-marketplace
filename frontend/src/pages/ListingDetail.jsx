import React, { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ShieldCheck, Star, X, Package } from "@phosphor-icons/react";
import { toast } from "sonner";
import api, { formatPrice, apiError } from "../lib/api";
import { useAuth } from "../context/AuthContext";
import { CONDITION_LABEL } from "../components/ProductCard";
import ReportButton from "../components/ReportButton";
import AIInsights from "../components/AIInsights";

export default function ListingDetail() {
  const { idOrSlug } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const { t } = useTranslation("marketplace");
  const [listing, setListing] = useState(null);
  const [active, setActive] = useState(0);
  const [notFound, setNotFound] = useState(false);
  const [showOffer, setShowOffer] = useState(false);
  const [offerAmount, setOfferAmount] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    api.get(`/listings/${idOrSlug}`)
      .then((r) => setListing(r.data.listing))
      .catch(() => setNotFound(true));
  }, [idOrSlug]);

  if (notFound) return (
    <div className="container" style={{ paddingTop: 80, paddingBottom: 80 }}>
      <div className="empty">
        <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 8 }}>{t("listing.notFound")}</div>
        <p className="hint" style={{ marginBottom: 20 }}>{t("listing.notFoundMessage")}</p>
        <Link to="/shop" className="btn">{t("listing.backToShop")}</Link>
      </div>
    </div>
  );

  if (!listing) return (
    <div style={{ display: "flex", justifyContent: "center", padding: "80px 0" }}>
      <div className="spin" />
    </div>
  );

  const a = listing.attributes || {};
  const rows = [
    [t("listing.attribute.brand"), a.brand], [t("listing.attribute.category"), a.category], [t("listing.attribute.size"), a.size],
    [t("listing.attribute.color"), a.color], [t("listing.attribute.material"), a.material], [t("listing.attribute.gender"), a.gender],
    [t("listing.attribute.condition"), CONDITION_LABEL[a.condition] || a.condition], [t("listing.attribute.season"), a.season],
  ].filter(([, v]) => v);

  const action = () => {
    if (!user) { navigate("/login"); return; }
    navigate(`/checkout?listing_id=${listing.id}`);
  };

  const openOffer = () => {
    if (!user) { navigate("/login"); return; }
    setOfferAmount(String(Math.round((listing.price.amount / 100) * 0.9)));
    setShowOffer(true);
  };

  const messageSeller = async () => {
    if (!user) { navigate("/login"); return; }
    try {
      const { data } = await api.post("/conversations", {
        context_type: "listing", context_id: listing.id,
      });
      navigate(`/messages?c=${data.conversation_id}`);
    } catch (err) {
      toast.error(apiError(err));
    }
  };

  const submitOffer = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.post("/offers", {
        listing_id: listing.id,
        amount: Math.round(parseFloat(offerAmount) * 100),
      });
      toast.success(t("listing.toast.offerSent"));
      setShowOffer(false);
      navigate("/offers");
    } catch (err) {
      toast.error(apiError(err));
    } finally {
      setSubmitting(false);
    }
  };

  const isSeller = user?.id === listing.seller_id;
  const isAdmin = ["admin", "moderator"].includes(user?.role);

  return (
    <div className="container" style={{ paddingTop: 28, paddingBottom: 80 }}>

      {/* ── Breadcrumb ──────────────────────────────────────────── */}
      <nav aria-label="Breadcrumb" className="row" style={{ gap: 8, marginBottom: 28, flexWrap: "wrap" }}>
        <Link to="/shop" className="overline" style={{ color: "var(--muted)" }}>{t("listing.breadcrumb.shop")}</Link>
        {a.category && (
          <>
            <span style={{ color: "var(--disabled)", fontSize: 10, letterSpacing: 0 }}>/</span>
            <Link to={`/shop?category=${a.category}`} className="overline" style={{ color: "var(--muted)" }}>
              {a.category}
            </Link>
          </>
        )}
        {a.brand && (
          <>
            <span style={{ color: "var(--disabled)", fontSize: 10, letterSpacing: 0 }}>/</span>
            <Link to={`/shop?brand=${encodeURIComponent(a.brand)}`} className="overline" style={{ color: "var(--text-2)" }}>
              {a.brand}
            </Link>
          </>
        )}
      </nav>

      <div className="pdp">

        {/* ── Gallery ─────────────────────────────────────────── */}
        <div className="pdp-gallery" data-testid="pdp-gallery">
          <div className="pdp-main">
            {listing.images?.[active]?.url ? (
              <img
                src={listing.images[active].url}
                alt={listing.title}
                onError={(e) => {
                  e.currentTarget.style.display = "none";
                  e.currentTarget.parentElement.classList.add("is-empty");
                }}
              />
            ) : null}
            <div className="img-fallback pdp-fallback">{a.brand || "ARCHIVE"}</div>
          </div>
          {listing.images?.length > 1 && (
            <div className="pdp-thumbs">
              {listing.images.map((im, i) => (
                <div
                  key={i}
                  className={`pdp-thumb ${i === active ? "active" : ""}`}
                  onClick={() => setActive(i)}
                  data-testid={`pdp-thumb-${i}`}
                >
                  <img src={im.url} alt="" />
                </div>
              ))}
            </div>
          )}
        </div>

        {/* ── Info ────────────────────────────────────────────── */}
        <div data-testid="pdp-info">

          {/* Brand */}
          {a.brand && (
            <Link
              to={`/shop?brand=${encodeURIComponent(a.brand)}`}
              className="overline"
              style={{ color: "var(--text-2)" }}
            >
              {a.brand}
            </Link>
          )}

          {/* Title */}
          <h1 style={{ fontSize: 26, fontWeight: 700, margin: "6px 0 14px", lineHeight: 1.3, letterSpacing: "-0.02em" }}>
            {listing.title}
          </h1>

          {/* Condition + size */}
          <div className="row" style={{ gap: 6, marginBottom: 20, flexWrap: "wrap" }}>
            {a.condition && <span className="badge badge-solid">{CONDITION_LABEL[a.condition]}</span>}
            {a.size && <span className="badge">Size {a.size}</span>}
            {listing.state === "Reserved" && <span className="badge badge-primary">{t("listing.badge.reserved")}</span>}
          </div>

          {/* Price */}
          <div
            data-testid="pdp-price"
            style={{ fontSize: 32, fontWeight: 700, letterSpacing: "-0.03em", marginBottom: 24 }}
          >
            {formatPrice(listing.price)}
          </div>

          {/* Actions */}
          <div className="stack" style={{ gap: 8 }}>
            <button
              className="btn btn-primary btn-block"
              onClick={action}
              style={{ height: 52, fontSize: 15 }}
              data-testid="pdp-buy-button"
            >
              {t("listing.button.buyNow")}
            </button>
            <div style={{
              display: "grid",
              gridTemplateColumns: listing.allow_offers ? "1fr 1fr" : "1fr",
              gap: 8,
            }}>
              {listing.allow_offers && (
                <button className="btn" onClick={openOffer} data-testid="pdp-offer-button">
                  {t("listing.button.makeOffer")}
                </button>
              )}
              <button className="btn" onClick={messageSeller} data-testid="pdp-message-seller-button">
                {t("listing.button.messageSeller")}
              </button>
            </div>
          </div>

          {/* Trust strip */}
          <div style={{
            display: "grid", gridTemplateColumns: "1fr 1fr 1fr",
            borderTop: "1px solid var(--border)", borderBottom: "1px solid var(--border)",
            marginTop: 20, padding: "14px 0",
          }}>
            {[
              [<ShieldCheck key="sc" size={16} />, t("listing.trust.escrow")],
              [<Package key="pkg" size={16} />, t("listing.trust.delivery")],
              [<Star key="st" size={16} />, t("listing.trust.verified")],
            ].map(([icon, label]) => (
              <div key={label} style={{
                display: "flex", flexDirection: "column", alignItems: "center",
                gap: 5, fontSize: 10, color: "var(--text-2)",
                textAlign: "center", letterSpacing: "0.08em",
                textTransform: "uppercase", fontWeight: 600,
              }}>
                {icon}
                {label}
              </div>
            ))}
          </div>

          {/* Seller */}
          {listing.seller && (
            <Link to="/" className="seller" data-testid="pdp-seller">
              <div className="avatar">{listing.seller.display_name?.[0]?.toUpperCase()}</div>
              <div>
                <div style={{ fontWeight: 600, fontSize: 14 }}>{listing.seller.display_name}</div>
                <div className="row" style={{ gap: 4, marginTop: 2 }}>
                  <Star size={13} weight="fill" color="var(--text)" />
                  <span className="hint">{listing.seller.reputation?.average_rating || "New"}</span>
                  <span className="hint" style={{ color: "var(--disabled)" }}>·</span>
                  <span className="hint">{listing.seller.reputation?.completed_reviews || 0} reviews</span>
                </div>
              </div>
            </Link>
          )}

          {/* Description — shown before spec table */}
          {listing.description && (
            <div style={{ marginTop: 28, paddingTop: 20, borderTop: "1px solid var(--border)" }}>
              <h4 style={{
                fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase",
                marginBottom: 10, color: "var(--text-2)", fontWeight: 600,
              }}>
                {t("listing.descriptionHeading")}
              </h4>
              <p style={{ fontSize: 14, lineHeight: 1.8, color: "var(--text-2)" }}>
                {listing.description}
              </p>
            </div>
          )}

          {/* Attribute table */}
          {rows.length > 0 && (
            <div className="attr-table" data-testid="pdp-attributes">
              {rows.map(([k, v]) => (
                <div className="attr-row" key={k}><div>{k}</div><div>{v}</div></div>
              ))}
            </div>
          )}

          {/* AI Insights — authorized users only */}
          {(isSeller || isAdmin) && <AIInsights listingId={listing.id} />}

          {/* Report */}
          <div style={{ marginTop: 24, paddingTop: 16, borderTop: "1px solid var(--border)" }}>
            <ReportButton targetType="listing" targetId={listing.id} label="Report listing" />
          </div>
        </div>
      </div>

      {/* ── Offer Modal ────────────────────────────────────────── */}
      {showOffer && (
        <div
          className="offer-modal-backdrop"
          data-testid="offer-modal"
          onClick={() => setShowOffer(false)}
        >
          <div className="panel offer-modal" onClick={(e) => e.stopPropagation()}>
            <div className="row" style={{ justifyContent: "space-between", marginBottom: 16 }}>
              <span style={{ fontWeight: 700, fontSize: 15 }}>{t("listing.button.makeOffer")}</span>
              <button
                onClick={() => setShowOffer(false)}
                data-testid="offer-modal-close"
                style={{ border: "none", background: "none", cursor: "pointer" }}
              >
                <X size={18} />
              </button>
            </div>
            <p className="hint" style={{ marginBottom: 16 }}>
              Listed at {formatPrice(listing.price)}
            </p>
            <form onSubmit={submitOffer}>
              <label className="field overline" style={{ marginBottom: 6 }}>
                {t("listing.offer.amountPlaceholder", { currency: listing.price.currency })}
              </label>
              <input
                data-testid="offer-amount-input"
                type="number" min="1" step="0.01"
                value={offerAmount}
                onChange={(e) => setOfferAmount(e.target.value)}
                required autoFocus
                style={{ marginBottom: 16 }}
              />
              <button
                className="btn btn-primary btn-block"
                disabled={submitting}
                data-testid="offer-submit-button"
              >
              {submitting ? t("listing.offer.sending") : t("listing.offer.send")}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
