import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { MARKETS, EXCHANGE_RATES, detectMarketFromBrowser, detectLanguageFromBrowser } from "../markets";
import { loadLanguage } from "../i18n";
import i18n from "../i18n";

const STORAGE_KEY = "archive_market_prefs";

const MarketCtx = createContext({
  market: MARKETS.UA,
  language: "uk",
  currency: "UAH",
  exchangeRates: EXCHANGE_RATES,
  setMarket: () => {},
  setLanguage: () => {},
  setCurrency: () => {},
});

function readPrefs() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch { return null; }
}

function savePrefs(prefs) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs)); } catch {}
}

function resolveInitial() {
  const stored = readPrefs();
  if (stored?.marketId && MARKETS[stored.marketId]) {
    const market = MARKETS[stored.marketId];
    const language = stored.language && market.supportedLanguages.includes(stored.language)
      ? stored.language : market.defaultLanguage;
    const currency = stored.currency && market.supportedCurrencies.includes(stored.currency)
      ? stored.currency : market.defaultCurrency;
    return { market, language, currency };
  }

  // Fall back to browser detection
  const marketId = detectMarketFromBrowser();
  const market = MARKETS[marketId];
  const language = detectLanguageFromBrowser(marketId);
  return { market, language, currency: market.defaultCurrency };
}

export function MarketProvider({ children }) {
  const initial = resolveInitial();
  const [market, setMarketState] = useState(initial.market);
  const [language, setLanguageState] = useState(initial.language);
  const [currency, setCurrencyState] = useState(initial.currency);
  // Exchange rates — static now, replaceable with live feed later
  const [exchangeRates] = useState(EXCHANGE_RATES);

  // Apply language to i18n and html[lang]
  useEffect(() => {
    (async () => {
      await loadLanguage(language);
      i18n.changeLanguage(language);
      document.documentElement.lang = language;
    })();
  }, [language]);

  const setMarket = useCallback((marketId) => {
    const m = MARKETS[marketId];
    if (!m) return;
    const lang = m.supportedLanguages.includes(language) ? language : m.defaultLanguage;
    const cur = m.supportedCurrencies.includes(currency) ? currency : m.defaultCurrency;
    setMarketState(m);
    setLanguageState(lang);
    setCurrencyState(cur);
    savePrefs({ marketId, language: lang, currency: cur });
  }, [language, currency]);

  const setLanguage = useCallback((lang) => {
    if (!market.supportedLanguages.includes(lang)) return;
    setLanguageState(lang);
    savePrefs({ marketId: market.id, language: lang, currency });
  }, [market, currency]);

  const setCurrency = useCallback((cur) => {
    if (!market.supportedCurrencies.includes(cur)) return;
    setCurrencyState(cur);
    savePrefs({ marketId: market.id, language, currency: cur });
  }, [market, language]);

  return (
    <MarketCtx.Provider value={{ market, language, currency, exchangeRates, setMarket, setLanguage, setCurrency }}>
      {children}
    </MarketCtx.Provider>
  );
}

export function useMarket() { return useContext(MarketCtx); }
