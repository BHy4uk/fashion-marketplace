import React from "react";
import { Link } from "react-router-dom";
import { Plus } from "@phosphor-icons/react";
import { useTranslation } from "react-i18next";
import { useAuth } from "../context/AuthContext";
import NotificationBell from "./NotificationBell";
import SearchBar from "./SearchBar";
import ThemeToggle from "./ThemeToggle";
import AccountDropdown from "./AccountDropdown";
import MarketSelector from "./MarketSelector";

function LogoMark({ size = 14 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 14 14" fill="none" aria-hidden="true">
      <path d="M7 0.5L13.5 7L7 13.5L0.5 7Z" fill="currentColor" />
    </svg>
  );
}

export default function Nav() {
  const { user, logout } = useAuth();
  const { t } = useTranslation();

  return (
    <header className="nav">
      <div className="container nav-inner">
        <Link to="/" className="brand" data-testid="brand-logo" style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <LogoMark />
          ARCHIVE
        </Link>

        <SearchBar />

        <div className="spacer" />

        <nav className="nav-links">
          <Link to="/shop" className="nav-link" data-testid="nav-shop-link">{t("nav.shop")}</Link>
          <MarketSelector />
          <ThemeToggle />

          {user ? (
            <>
              <Link to="/sell" className="btn btn-primary btn-sm" data-testid="nav-sell-button">
                <Plus size={14} weight="bold" /> {t("nav.sell")}
              </Link>
              <NotificationBell />
              <AccountDropdown user={user} logout={logout} />
            </>
          ) : (
            <>
              <Link to="/login" className="nav-link" data-testid="nav-login-link">{t("nav.login")}</Link>
              <Link to="/sell" className="btn btn-primary btn-sm" data-testid="nav-sell-button">
                <Plus size={14} weight="bold" /> {t("nav.sell")}
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
