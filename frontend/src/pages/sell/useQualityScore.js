/**
 * Listing Quality Score — pure function, no side effects.
 * Returns a score (0–100) and a checklist for the Review step.
 */

export function computeQualityScore(draft) {
  const checks = [
    {
      label: "Photos added",
      met: (draft.photos?.length ?? 0) >= 1,
      weight: 2,
    },
    {
      label: "3+ photos for better visibility",
      met: (draft.photos?.length ?? 0) >= 3,
      weight: 2,
    },
    {
      label: "Descriptive title",
      met: (draft.title || "").trim().length >= 10,
      weight: 2,
    },
    {
      label: "Category selected",
      met: !!draft.category,
      weight: 1,
    },
    {
      label: "Brand specified",
      met: !!draft.brand,
      weight: 1,
    },
    {
      label: "Condition specified",
      met: !!draft.condition,
      weight: 2,
    },
    {
      label: "Detailed description (80+ characters)",
      met: (draft.description || "").length >= 80,
      weight: 2,
    },
    {
      label: "Measurements added",
      met: Object.values(draft.measurements || {}).some(v => v),
      weight: 2,
    },
    {
      label: "Price set",
      met: parseFloat(draft.price_amount || 0) > 0,
      weight: 2,
    },
    {
      label: "Shipping configured",
      met: !!draft.ships_to,
      weight: 1,
    },
    {
      label: "Size specified",
      met: !!draft.size,
      weight: 1,
    },
  ];

  const total = checks.reduce((s, c) => s + c.weight, 0);
  const earned = checks.filter(c => c.met).reduce((s, c) => s + c.weight, 0);

  return {
    score: Math.round((earned / total) * 100),
    checks,
  };
}
