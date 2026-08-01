/**
 * Category-driven schema — maps category slugs to extra fields and measurement sets.
 * Add a new group here to extend the wizard without touching any component.
 */

export function getCategoryGroup(slug = "") {
  const s = slug.toLowerCase();
  if (["shoe", "boot", "sneaker", "loafer", "sandal", "heel", "mule", "slipper"].some(k => s.includes(k))) return "shoes";
  if (["jacket", "coat", "blazer", "outerwear", "parka", "bomber", "anorak", "puffer", "windbreaker"].some(k => s.includes(k))) return "outerwear";
  if (["pant", "trouser", "jean", "short", "denim", "chino", "cargo", "legging"].some(k => s.includes(k))) return "pants";
  if (["dress", "skirt", "gown"].some(k => s.includes(k))) return "dresses";
  if (["bag", "backpack", "wallet", "purse", "clutch", "belt", "glove", "scarf", "hat", "cap", "beanie", "accessories"].some(k => s.includes(k))) return "accessories";
  if (["watch"].some(k => s.includes(k))) return "watches";
  if (["top", "shirt", "tee", "t-shirt", "sweatshirt", "hoodie", "knit", "sweater", "pullover", "blouse"].some(k => s.includes(k))) return "tops";
  return "general";
}

export const CATEGORY_EXTRA_FIELDS = {
  shoes: [
    { key: "box_included", label: "Original box included", type: "toggle" },
    { key: "extra_laces", label: "Extra laces included", type: "toggle" },
  ],
  outerwear: [
    { key: "fit", label: "Fit", type: "select", options: ["", "Slim", "Regular", "Relaxed", "Oversized"] },
    { key: "has_hood", label: "Includes hood", type: "toggle" },
    { key: "has_lining", label: "Fully lined", type: "toggle" },
  ],
  accessories: [
    { key: "dimensions", label: "Dimensions (cm)", type: "text", placeholder: "e.g. 35 × 25 × 10" },
    { key: "strap_length", label: "Strap length (cm)", type: "text", placeholder: "e.g. 110" },
    { key: "hardware_color", label: "Hardware color", type: "text", placeholder: "e.g. Gold, Silver" },
  ],
  watches: [
    { key: "serial_number", label: "Serial number", type: "text" },
    { key: "has_papers", label: "Papers included", type: "toggle" },
    { key: "has_watch_box", label: "Original box included", type: "toggle" },
    { key: "has_warranty_card", label: "Warranty card", type: "toggle" },
  ],
};

export const CATEGORY_MEASUREMENTS = {
  outerwear: [
    { key: "chest", label: "Chest" },
    { key: "shoulder", label: "Shoulder" },
    { key: "sleeve", label: "Sleeve" },
    { key: "length", label: "Length" },
  ],
  tops: [
    { key: "chest", label: "Chest" },
    { key: "shoulder", label: "Shoulder" },
    { key: "sleeve", label: "Sleeve" },
    { key: "length", label: "Length" },
  ],
  pants: [
    { key: "waist", label: "Waist" },
    { key: "rise", label: "Rise" },
    { key: "inseam", label: "Inseam" },
    { key: "leg_opening", label: "Leg opening" },
  ],
  shoes: [
    { key: "insole", label: "Insole length" },
    { key: "outsole", label: "Outsole length" },
  ],
  dresses: [
    { key: "chest", label: "Chest" },
    { key: "waist", label: "Waist" },
    { key: "hip", label: "Hip" },
    { key: "length", label: "Length" },
  ],
  accessories: [
    { key: "width", label: "Width" },
    { key: "height", label: "Height" },
    { key: "depth", label: "Depth" },
  ],
  general: [
    { key: "chest", label: "Chest / Width" },
    { key: "length", label: "Length / Height" },
  ],
};

export function getExtraFields(group) {
  return CATEGORY_EXTRA_FIELDS[group] || [];
}

export function getMeasurements(group) {
  return CATEGORY_MEASUREMENTS[group] || CATEGORY_MEASUREMENTS.general;
}
