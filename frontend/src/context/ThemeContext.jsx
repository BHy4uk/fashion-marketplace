import React, { createContext, useContext, useEffect, useState } from "react";

const THEME_KEY = "archive_theme";
const ThemeCtx = createContext({ theme: "light", setTheme: () => {} });

function readStored() {
  try {
    const v = localStorage.getItem(THEME_KEY);
    // coerce legacy "system" to "light"
    return v === "dark" ? "dark" : "light";
  } catch { return "light"; }
}

export function ThemeProvider({ children }) {
  const [theme, setThemeState] = useState(readStored);

  useEffect(() => {
    const html = document.documentElement;
    if (theme === "dark") {
      html.setAttribute("data-theme", "dark");
    } else {
      html.removeAttribute("data-theme");
    }
  }, [theme]);

  const setTheme = (t) => {
    try { localStorage.setItem(THEME_KEY, t); } catch {}
    setThemeState(t);
  };

  return (
    <ThemeCtx.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeCtx.Provider>
  );
}

export function useTheme() { return useContext(ThemeCtx); }
