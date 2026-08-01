import React from "react";
import { useCurrency } from "../hooks/useCurrency";

/**
 * Displays a price in the user's preferred currency with locale-aware formatting.
 * price: { amount, currency } | number | null
 */
export function PriceDisplay({ price, className, originalCurrency }) {
  const { format, currency } = useCurrency();
  const raw = (originalCurrency && typeof price === "number")
    ? { amount: price, currency: originalCurrency }
    : price;

  return <span className={className}>{format(raw)}</span>;
}
