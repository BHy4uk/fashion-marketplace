import React, { useState } from "react";
import { Link } from "react-router-dom";
import { formatPrice } from "../lib/api";

const CONDITION_LABEL = {
  BRAND_NEW: "Brand New",
  LIKE_NEW: "Like New",
  GENTLY_USED: "Gently Used",
  USED: "Used",
  WELL_WORN: "Well Worn",
};

export default function ProductCard({ listing }) {
  const img = listing.images?.[0]?.url;
  const [err, setErr] = useState(false);
  const showImg = img && !err;
  return (
    <Link to={`/listing/${listing.slug || listing.id}`} className="product"
      data-testid={`product-card-${listing.id}`}>
      <div className="product-img">
        {showImg ? (
          <img src={img} alt={listing.title} loading="lazy" onError={() => setErr(true)} />
        ) : (
          <div className="img-fallback" data-testid="img-fallback">
            {(listing.attributes?.brand || "ARCHIVE").slice(0, 12)}
          </div>
        )}
      </div>
      <div className="product-info">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <span className="product-brand">{listing.attributes?.brand || "—"}</span>
          {listing.attributes?.condition ? (
            <span className="overline" style={{ fontSize: 10 }}>
              {CONDITION_LABEL[listing.attributes.condition]}
            </span>
          ) : null}
        </div>
        <div className="product-title">{listing.title}</div>
        <div className="row" style={{ justifyContent: "space-between" }}>
          <span className="product-price">{formatPrice(listing.price)}</span>
          <span className="overline" style={{ fontSize: 10 }}>{listing.attributes?.size}</span>
        </div>
      </div>
    </Link>
  );
}

export { CONDITION_LABEL };
