import React, { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { Tag, ShieldCheck, Star, X } from "@phosphor-icons/react";
import { toast } from "sonner";
import api, { formatPrice, apiError } from "../lib/api";
import { useAuth } from "../context/AuthContext";
import { CONDITION_LABEL } from "../components/ProductCard";
import ReportButton from "../components/ReportButton";

export default function ListingDetail() {
  const { idOrSlug } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
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

  if (notFound) return <div className="container empty" style={{ marginTop: 40 }}>Listing not found.</div>;
  if (!listing) return <div className="container" style={{ padding: 80 }}><div className="spin" /></div>;

  const a = listing.attributes || {};
  const rows = [
    ["Brand", a.brand], ["Category", a.category], ["Size", a.size],
    ["Color", a.color], ["Material", a.material], ["Gender", a.gender],
    ["Condition", CONDITION_LABEL[a.condition] || a.condition], ["Season", a.season],
  ].filter(([, v]) => v);

  const action = (label) => {
    if (!user) { toast.error("Please log in to continue"); return; }
    toast.success(`${label} — checkout ships in the next milestone`);
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
      toast.success("Offer sent to the seller");
      setShowOffer(false);
      navigate("/offers");
    } catch (err) {
      toast.error(apiError(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="container" style={{ paddingTop: 24, paddingBottom: 60 }}>
      <div className="pdp">
        <div className="pdp-gallery" data-testid="pdp-gallery">
          <div className="pdp-main">
            {listing.images?.[active]?.url ? (
              <img src={listing.images[active].url} alt={listing.title}
                onError={(e) => { e.currentTarget.style.display = "none";
                  e.currentTarget.parentElement.classList.add("is-empty"); }} />
            ) : null}
            <div className="img-fallback pdp-fallback">{a.brand || "ARCHIVE"}</div>
          </div>
          {listing.images?.length > 1 && (
            <div className="pdp-thumbs">
              {listing.images.map((im, i) => (
                <div key={i} className={`pdp-thumb ${i === active ? "active" : ""}`}
                  onClick={() => setActive(i)} data-testid={`pdp-thumb-${i}`}>
                  <img src={im.url} alt="" />
                </div>
              ))}
            </div>
          )}
        </div>

        <div data-testid="pdp-info">
          <span className="overline">{a.brand}</span>
          <h1 style={{ fontSize: 28, margin: "6px 0 12px" }}>{listing.title}</h1>
          <div className="row" style={{ gap: 10, marginBottom: 10 }}>
            {a.condition && <span className="badge badge-solid">{CONDITION_LABEL[a.condition]}</span>}
            {a.size && <span className="badge">Size {a.size}</span>}
            {listing.state === "Reserved" && <span className="badge badge-primary">Reserved</span>}
          </div>
          <div className="heading" style={{ fontSize: 30, marginBottom: 16 }}
            data-testid="pdp-price">{formatPrice(listing.price)}</div>

          <button className="btn btn-primary btn-block mb-12" onClick={() => action("Buy Now")}
            data-testid="pdp-buy-button">
            <Tag size={18} weight="bold" /> Buy Now
          </button>
          {listing.allow_offers && (
            <button className="btn btn-block" onClick={openOffer}
              data-testid="pdp-offer-button">Make an Offer</button>
          )}
          <button className="btn btn-block mt-16" onClick={messageSeller}
            data-testid="pdp-message-seller-button">Message seller</button>
          <div className="row" style={{ justifyContent: "center", marginTop: 12 }}>
            <ReportButton targetType="listing" targetId={listing.id} label="Report listing" />
          </div>

          {showOffer && (
            <div className="offer-modal-backdrop" data-testid="offer-modal"
              onClick={() => setShowOffer(false)}>
              <div className="panel offer-modal" onClick={(e) => e.stopPropagation()}>
                <div className="row" style={{ justifyContent: "space-between", marginBottom: 12 }}>
                  <span className="overline">Make an offer</span>
                  <button onClick={() => setShowOffer(false)} data-testid="offer-modal-close"
                    style={{ border: "none", background: "none" }}><X size={18} /></button>
                </div>
                <p className="hint mb-12">Listing price: {formatPrice(listing.price)}</p>
                <form onSubmit={submitOffer}>
                  <label className="field overline">Your offer ({listing.price.currency})</label>
                  <input data-testid="offer-amount-input" type="number" min="1" step="0.01"
                    value={offerAmount} onChange={(e) => setOfferAmount(e.target.value)}
                    required autoFocus className="mb-12" />
                  <button className="btn btn-primary btn-block" disabled={submitting}
                    data-testid="offer-submit-button">
                    {submitting ? "Sending…" : "Send offer"}
                  </button>
                </form>
              </div>
            </div>
          )}

          <div className="row" style={{ gap: 8, marginTop: 14, color: "var(--success)" }}>
            <ShieldCheck size={18} /> <span className="hint" style={{ color: "var(--success)" }}>
              Secure escrow · funds released after delivery
            </span>
          </div>

          {listing.seller && (
            <Link to={`/`} className="seller" data-testid="pdp-seller">
              <div className="avatar">{listing.seller.display_name?.[0]?.toUpperCase()}</div>
              <div>
                <div style={{ fontWeight: 600, fontSize: 14 }}>{listing.seller.display_name}</div>
                <div className="row hint" style={{ gap: 4 }}>
                  <Star size={14} weight="fill" color="#FF4500" />
                  {listing.seller.reputation?.average_rating || "New"} ·{" "}
                  {listing.seller.reputation?.completed_reviews || 0} reviews
                </div>
              </div>
            </Link>
          )}

          <div className="attr-table" data-testid="pdp-attributes">
            {rows.map(([k, v]) => (
              <div className="attr-row" key={k}><div>{k}</div><div>{v}</div></div>
            ))}
          </div>

          {listing.description && (
            <p className="hint" style={{ marginTop: 18, lineHeight: 1.6 }}>{listing.description}</p>
          )}
        </div>
      </div>
    </div>
  );
}
