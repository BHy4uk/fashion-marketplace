import React, { useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { formatPrice } from "../lib/api";

const CONDITION_LABEL = {
  BRAND_NEW: "Brand New",
  LIKE_NEW: "Like New",
  GENTLY_USED: "Gently Used",
  USED: "Used",
  WELL_WORN: "Well Worn",
};

/**
 * LazyImage — blur-up progressive image loading.
 * The image reveals itself with a soft opacity transition once loaded,
 * avoiding the hard pop-in that cheapens the product experience.
 */
function LazyImage({ src, alt }) {
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(false);

  if (!src || error) {
    return (
      <div className="img-fallback" data-testid="img-fallback">
        ARCHIVE
      </div>
    );
  }

  return (
    <motion.img
      src={src}
      alt={alt}
      loading="lazy"
      onLoad={() => setLoaded(true)}
      onError={() => setError(true)}
      animate={{ opacity: loaded ? 1 : 0 }}
      transition={{ duration: 0.4, ease: [0, 0, 0.2, 1] }}
      style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }}
    />
  );
}

export default function ProductCard({ listing }) {
  const img = listing.images?.[0]?.url;
  const a = listing.attributes || {};

  return (
    <Link
      to={`/listing/${listing.slug || listing.id}`}
      className="product"
      data-testid={`product-card-${listing.id}`}
    >
      {/* Image wrapper — scale on hover via CSS, opacity transition via motion */}
      <div className="product-img">
        <LazyImage src={img} alt={listing.title} />
      </div>

      <div className="product-info">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <span className="product-brand">{a.brand || "—"}</span>
          {a.condition && (
            <span className="overline" style={{ fontSize: 10 }}>
              {CONDITION_LABEL[a.condition]}
            </span>
          )}
        </div>
        <div className="product-title">{listing.title}</div>
        <div className="row" style={{ justifyContent: "space-between" }}>
          <span className="product-price">{formatPrice(listing.price)}</span>
          {a.size && <span className="overline" style={{ fontSize: 10 }}>{a.size}</span>}
        </div>
      </div>
    </Link>
  );
}

export { CONDITION_LABEL };
