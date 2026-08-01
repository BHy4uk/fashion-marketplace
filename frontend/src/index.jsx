import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import App from "./App";
import { initI18n } from "./i18n";
import { detectLanguageFromBrowser, detectMarketFromBrowser } from "./markets";

function getBootLanguage() {
  try {
    const prefs = JSON.parse(localStorage.getItem("archive_market_prefs") || "null");
    if (prefs?.language) return prefs.language;
  } catch {}
  return detectLanguageFromBrowser(detectMarketFromBrowser());
}

initI18n(getBootLanguage()).then(() => {
  ReactDOM.createRoot(document.getElementById("root")).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
});
