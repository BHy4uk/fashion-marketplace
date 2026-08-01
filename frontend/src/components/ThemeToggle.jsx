import React from "react";
import { Sun, Moon } from "@phosphor-icons/react";
import { useTheme } from "../context/ThemeContext";

export default function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const isDark = theme === "dark";

  return (
    <button
      className="theme-trigger"
      onClick={() => setTheme(isDark ? "light" : "dark")}
      title={isDark ? "Switch to light" : "Switch to dark"}
      aria-label={isDark ? "Switch to light theme" : "Switch to dark theme"}
    >
      {isDark ? <Sun size={16} weight="regular" /> : <Moon size={16} weight="regular" />}
    </button>
  );
}
