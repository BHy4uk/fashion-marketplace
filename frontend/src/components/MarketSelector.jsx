import React, { useRef, useState, useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Globe, Check, CaretDown } from "@phosphor-icons/react";
import { useTranslation } from "react-i18next";
import { useMarket } from "../context/MarketContext";
import { MARKETS, LANGUAGES, CURRENCIES } from "../markets";

const TAB_MARKET   = "market";
const TAB_LANGUAGE = "language";
const TAB_CURRENCY = "currency";

const popoverVariants = {
  hidden:  { opacity: 0, scale: 0.97, y: -4 },
  visible: { opacity: 1, scale: 1,    y: 0, transition: { duration: 0.15, ease: "easeOut" } },
  exit:    { opacity: 0, scale: 0.97, y: -4, transition: { duration: 0.1 } },
};

export default function MarketSelector() {
  const { t } = useTranslation();
  const { market, language, currency, setMarket, setLanguage, setCurrency } = useMarket();
  const [open, setOpen] = useState(false);
  const [tab, setTab] = useState(TAB_MARKET);
  const ref = useRef(null);

  useEffect(() => {
    const h = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener("mousedown", h);
    return () => document.removeEventListener("mousedown", h);
  }, []);

  return (
    <div className="market-selector" ref={ref}>
      <button
        className="market-trigger"
        onClick={() => setOpen(v => !v)}
        aria-label={t("market.selectorTitle")}
        title={t("market.selectorTitle")}
      >
        <span className="market-trigger-flag">{market.flag}</span>
        <CaretDown size={10} style={{ opacity: 0.5, transition: "transform 150ms", transform: open ? "rotate(180deg)" : "none" }} />
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            className="market-popover"
            variants={popoverVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            role="dialog"
            aria-label={t("market.selectorTitle")}
          >
            <p className="market-popover-title">{t("market.selectorTitle")}</p>

            {/* Tab bar */}
            <div className="market-tabs">
              {[
                { id: TAB_MARKET,   label: t("market.market") },
                { id: TAB_LANGUAGE, label: t("market.language") },
                { id: TAB_CURRENCY, label: t("market.currency") },
              ].map(({ id, label }) => (
                <button
                  key={id}
                  className={`market-tab ${tab === id ? "market-tab--active" : ""}`}
                  onClick={() => setTab(id)}
                >
                  {label}
                </button>
              ))}
            </div>

            <div className="market-options">

              {/* MARKET tab */}
              {tab === TAB_MARKET && Object.values(MARKETS).map(m => (
                <button
                  key={m.id}
                  className={`market-option ${m.id === market.id ? "market-option--active" : ""}`}
                  onClick={() => { setMarket(m.id); setOpen(false); }}
                >
                  <span className="market-option-flag">{m.flag}</span>
                  <span className="market-option-name">{m.name}</span>
                  {m.id === market.id && <Check size={13} weight="bold" className="market-check" />}
                </button>
              ))}

              {/* LANGUAGE tab */}
              {tab === TAB_LANGUAGE && market.supportedLanguages.map(code => {
                const lang = LANGUAGES[code];
                if (!lang) return null;
                return (
                  <button
                    key={code}
                    className={`market-option ${code === language ? "market-option--active" : ""}`}
                    onClick={() => { setLanguage(code); setOpen(false); }}
                  >
                    <span className="market-option-native">{lang.nativeName}</span>
                    <span className="market-option-en">{lang.name}</span>
                    {code === language && <Check size={13} weight="bold" className="market-check" />}
                  </button>
                );
              })}

              {/* CURRENCY tab */}
              {tab === TAB_CURRENCY && market.supportedCurrencies.map(code => {
                const cur = CURRENCIES[code];
                if (!cur) return null;
                return (
                  <button
                    key={code}
                    className={`market-option ${code === currency ? "market-option--active" : ""}`}
                    onClick={() => { setCurrency(code); setOpen(false); }}
                  >
                    <span className="market-option-flag">{cur.symbol}</span>
                    <span className="market-option-name">{cur.code}</span>
                    <span className="market-option-en">{cur.name}</span>
                    {code === currency && <Check size={13} weight="bold" className="market-check" />}
                  </button>
                );
              })}

            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
