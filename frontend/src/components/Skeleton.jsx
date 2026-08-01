import React from "react";
import { cn } from "../lib/utils";

/**
 * Skeleton — content-aware loading placeholder.
 * Matches the dimensions of the element it replaces via className.
 *
 * Usage:
 *   <Skeleton className="h-4 w-32" />            // inline
 *   <Skeleton className="aspect-[3/4] w-full" /> // product image slot
 */
export function Skeleton({ className, ...props }) {
  return (
    <div
      className={cn("skeleton", className)}
      aria-hidden="true"
      role="presentation"
      {...props}
    />
  );
}

/**
 * ProductCardSkeleton — exact placeholder for a ProductCard while loading.
 */
export function ProductCardSkeleton() {
  return (
    <div className="product" aria-hidden="true">
      <div className="product-img">
        <div className="skeleton" style={{ width: "100%", height: "100%" }} />
      </div>
      <div className="product-info">
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
          <div className="skeleton" style={{ width: 80, height: 13 }} />
          <div className="skeleton" style={{ width: 50, height: 11 }} />
        </div>
        <div className="skeleton" style={{ width: "90%", height: 13, marginBottom: 8 }} />
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <div className="skeleton" style={{ width: 60, height: 15 }} />
          <div className="skeleton" style={{ width: 30, height: 11 }} />
        </div>
      </div>
    </div>
  );
}

export default Skeleton;
