/**
 * Market Registry — every market the platform operates in.
 *
 * Adding a new market requires only adding an entry here.
 * All downstream systems (currency, payments, shipping, legal) derive from this registry.
 */

export const CURRENCIES = {
  UAH: { code: "UAH", symbol: "₴", name: "Ukrainian Hryvnia", decimals: 0 },
  EUR: { code: "EUR", symbol: "€", name: "Euro",              decimals: 2 },
  USD: { code: "USD", symbol: "$", name: "US Dollar",         decimals: 2 },
  GBP: { code: "GBP", symbol: "£", name: "British Pound",     decimals: 2 },
};

export const LANGUAGES = {
  en: { code: "en", name: "English",    nativeName: "English",    dir: "ltr" },
  uk: { code: "uk", name: "Ukrainian",  nativeName: "Українська", dir: "ltr" },
  fr: { code: "fr", name: "French",     nativeName: "Français",   dir: "ltr" },
  de: { code: "de", name: "German",     nativeName: "Deutsch",    dir: "ltr" },
  it: { code: "it", name: "Italian",    nativeName: "Italiano",   dir: "ltr" },
  es: { code: "es", name: "Spanish",    nativeName: "Español",    dir: "ltr" },
  nl: { code: "nl", name: "Dutch",      nativeName: "Nederlands", dir: "ltr" },
  pl: { code: "pl", name: "Polish",     nativeName: "Polski",     dir: "ltr" },
  pt: { code: "pt", name: "Portuguese", nativeName: "Português",  dir: "ltr" },
};

/** Static exchange rates — base UAH. Replace with live rates later. */
export const EXCHANGE_RATES = {
  UAH: 1,
  EUR: 44.5,
  USD: 41.2,
  GBP: 52.8,
};

export const MARKETS = {
  UA: {
    id: "UA",
    name: "Ukraine",
    nativeName: "Україна",
    flag: "🇺🇦",
    locale: "uk-UA",
    timezone: "Europe/Kyiv",
    measurementSystem: "metric",
    defaultLanguage: "uk",
    defaultCurrency: "UAH",
    supportedLanguages: ["uk", "en"],
    supportedCurrencies: ["UAH", "EUR", "USD"],
    vatRate: 20,
    paymentProviders: ["liqpay", "monobank"],
    shippingProviders: ["nova_poshta", "ukrposhta"],
    features: {
      multiCurrency: true,
      liveExchangeRates: false,
      vatDisplay: false,
    },
    legal: {
      termsUrl: "/legal/ua/terms",
      privacyUrl: "/legal/ua/privacy",
      cookieUrl: "/legal/ua/cookies",
      returnPolicyUrl: "/legal/ua/returns",
    },
  },

  EU: {
    id: "EU",
    name: "European Union",
    nativeName: "European Union",
    flag: "🇪🇺",
    locale: "en-IE",
    timezone: "Europe/Paris",
    measurementSystem: "metric",
    defaultLanguage: "en",
    defaultCurrency: "EUR",
    supportedLanguages: ["en", "fr", "de", "it", "es", "nl", "pl", "pt"],
    supportedCurrencies: ["EUR", "USD", "GBP"],
    vatRate: 20,
    paymentProviders: ["stripe", "adyen", "paypal"],
    shippingProviders: ["dhl", "dpd", "gls", "ups"],
    features: {
      multiCurrency: true,
      liveExchangeRates: false,
      vatDisplay: true,
    },
    legal: {
      termsUrl: "/legal/eu/terms",
      privacyUrl: "/legal/eu/privacy",
      cookieUrl: "/legal/eu/cookies",
      returnPolicyUrl: "/legal/eu/returns",
    },
  },

  GB: {
    id: "GB",
    name: "United Kingdom",
    nativeName: "United Kingdom",
    flag: "🇬🇧",
    locale: "en-GB",
    timezone: "Europe/London",
    measurementSystem: "metric",
    defaultLanguage: "en",
    defaultCurrency: "GBP",
    supportedLanguages: ["en"],
    supportedCurrencies: ["GBP", "EUR", "USD"],
    vatRate: 20,
    paymentProviders: ["stripe", "paypal"],
    shippingProviders: ["royal_mail", "dpd", "dhl"],
    features: {
      multiCurrency: true,
      liveExchangeRates: false,
      vatDisplay: true,
    },
    legal: {
      termsUrl: "/legal/gb/terms",
      privacyUrl: "/legal/gb/privacy",
      cookieUrl: "/legal/gb/cookies",
      returnPolicyUrl: "/legal/gb/returns",
    },
  },
};

/** Detect the best market from browser navigator */
export function detectMarketFromBrowser() {
  const lang = navigator.language || "en";
  if (lang.startsWith("uk")) return "UA";
  if (lang.startsWith("en-GB")) return "GB";
  const euLangs = ["fr", "de", "it", "es", "nl", "pl", "pt"];
  if (euLangs.some(l => lang.startsWith(l))) return "EU";
  return "UA"; // platform default
}

/** Detect best language for a given market from browser */
export function detectLanguageFromBrowser(marketId) {
  const market = MARKETS[marketId];
  if (!market) return "en";
  const browserLang = (navigator.language || "en").split("-")[0];
  return market.supportedLanguages.includes(browserLang) ? browserLang : market.defaultLanguage;
}
