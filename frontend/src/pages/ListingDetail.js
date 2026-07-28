import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { Tag, ShieldCheck, Star } from "@phosphor-icons/react";
import { toast } from "sonner";
import api, { formatPrice, apiError } from "../lib/api";
import { useAuth } from "../context/AuthContext";
import { CONDITION_LABEL } from "../components/ProductCard";

export default function ListingDetail() {
  const { idOrSlug } = useParams();
  const { user } = useAuth();
  const [listing, setListing] = useState(null);
  const [active, setActive] = useState(0);
  const [notFound, setNotFound] = useState(false);

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
    toast.success(`${label} — checkout & offers ship in the next milestone`);
  };

  return (
    <div className="container" style={{ paddingTop: 24, paddingBottom: 60 }}>
      <div className="pdp">
        <div className="pdp-gallery" data-testid="pdp-gallery">
          <div className="pdp-main">
            <img src={listing.images?.[active]?.url} alt={listing.title} />
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
            <button className="btn btn-block" onClick={() => action("Make Offer")}
              data-testid="pdp-offer-button">Make an Offer</button>
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
