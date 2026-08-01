import i18n from "i18next";
import { initReactI18next } from "react-i18next";

const SUPPORTED = ["en", "uk"];
export const NAMESPACES = ["common", "auth", "home", "marketplace", "sell", "dashboard", "offers", "orders", "messages", "checkout", "analytics", "admin"];
const DEFAULT_NS = "common";

/** Load a translation bundle via Vite dynamic import (each locale chunk is code-split). */
async function loadBundle(lang, ns) {
  try {
    const mod = await import(`./locales/${lang}/${ns}.json`);
    return mod.default ?? mod;
  } catch {
    return {};
  }
}

/** Eagerly load all bundles for a single language. */
async function loadAllBundles(lang) {
  const bundles = await Promise.all(NAMESPACES.map(ns => loadBundle(lang, ns)));
  return Object.fromEntries(NAMESPACES.map((ns, i) => [ns, bundles[i]]));
}

export async function initI18n(initialLang = "en") {
  const resources = { en: await loadAllBundles("en") };

  if (initialLang !== "en" && SUPPORTED.includes(initialLang)) {
    resources[initialLang] = await loadAllBundles(initialLang);
  }

  await i18n
    .use(initReactI18next)
    .init({
      lng: initialLang,
      fallbackLng: "en",
      defaultNS: DEFAULT_NS,
      ns: NAMESPACES,
      resources,
      interpolation: { escapeValue: false },
      react: { useSuspense: false },
      // Surface missing keys clearly in development
      missingKeyHandler: (lngs, ns, key) => {
        if (import.meta.env.DEV) {
          console.warn(`[i18n] MISSING KEY — ns:"${ns}" key:"${key}" lang:${lngs.join(",")}`);
        }
      },
      parseMissingKeyHandler: (key) =>
        import.meta.env.DEV ? `⚠️${key}` : key,
      saveMissing: import.meta.env.DEV,
    });

  return i18n;
}

/** Lazy-load a language that hasn't been loaded yet. */
export async function loadLanguage(lang) {
  if (!SUPPORTED.includes(lang)) return;
  if (i18n.hasResourceBundle(lang, DEFAULT_NS)) return;
  const allBundles = await loadAllBundles(lang);
  NAMESPACES.forEach(ns => i18n.addResourceBundle(lang, ns, allBundles[ns] ?? {}, true, true));
}

export { SUPPORTED };
export default i18n;

