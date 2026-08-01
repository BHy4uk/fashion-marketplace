import React, { useRef, useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import {
  ListBullets, Tag, Package, ChatCircle, ChartBar,
  Shield, CaretDown, SignOut, File, Sun, Moon,
} from "@phosphor-icons/react";
import { useTranslation } from "react-i18next";
import { useTheme } from "../context/ThemeContext";
import { slideDownVariants } from "../lib/motion";
import api from "../lib/api";

function initials(name) {
  if (!name) return "?";
  return name.split(/\s+/).slice(0, 2).map(w => w[0]).join("").toUpperCase();
}

function Badge({ count }) {
  if (!count) return null;
  return <span className="dropdown-badge">{count > 99 ? "99+" : count}</span>;
}

function SectionLabel({ children }) {
  return <p className="dropdown-section-label">{children}</p>;
}

export default function AccountDropdown({ user, logout }) {
  const [open, setOpen] = useState(false);
  const [counts, setCounts] = useState(null);
  const ref = useRef(null);
  const { theme, setTheme } = useTheme();
  const { t } = useTranslation();
  const isDark = theme === "dark";

  useEffect(() => {
    const h = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener("mousedown", h);
    return () => document.removeEventListener("mousedown", h);
  }, []);

  useEffect(() => {
    if (!open) return;
    Promise.all([
      api.get("/offers/counts"),
      api.get("/conversations/unread-count"),
      api.get("/listings/mine/counts"),
    ]).then(([offers, msgs, listings]) => {
      setCounts({
        offersReceived: offers.data.seller,
        offersSent: offers.data.buyer,
        messages: msgs.data.count,
        drafts: listings.data.drafts,
      });
    }).catch(() => {});
  }, [open]);

  const close = () => setOpen(false);
  const displayName = user?.profile?.display_name || "Account";
  const isAdmin = ["admin", "moderator"].includes(user?.role);
  const hasDrafts = counts === null || counts?.drafts > 0; // show while loading

  return (
    <div className="nav-account" ref={ref}>
      <button
        className="nav-account-trigger"
        onClick={() => setOpen(v => !v)}
        aria-haspopup="true"
        aria-expanded={open}
        data-testid="nav-dashboard-link"
      >
        <span className="nav-avatar-sm">{initials(displayName)}</span>
        <span className="nav-account-name">{displayName.split(" ")[0]}</span>
        <CaretDown
          size={11}
          className="nav-caret"
          style={{ opacity: 0.5, transition: "transform 150ms", transform: open ? "rotate(180deg)" : "none" }}
        />
      </button>

      <AnimatePresence>
        {open && (
          <motion.nav
            className="nav-dropdown"
            variants={slideDownVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            role="menu"
          >
            {/* Profile header */}
            <div className="dropdown-profile">
              <span className="dropdown-avatar">{initials(displayName)}</span>
              <div>
                <p className="dropdown-profile-name">{displayName}</p>
                <p className="dropdown-profile-role">{isAdmin ? t("account.admin") : t("account.member")}</p>
              </div>
            </div>

            <div className="nav-dropdown-divider" />

            {/* SELL */}
            <SectionLabel>{t("account.sell")}</SectionLabel>
            <Link to="/dashboard" className="nav-dropdown-item" onClick={close} data-testid="nav-listings-link">
              <ListBullets size={14} /> {t("account.myListings")}
            </Link>
            <Link to="/offers?box=seller" className="nav-dropdown-item" onClick={close} data-testid="nav-offers-link">
              <Tag size={14} /> {t("account.offersReceived")}
              <Badge count={counts?.offersReceived} />
            </Link>
            {hasDrafts && (
              <Link to="/dashboard" className="nav-dropdown-item" onClick={close}>
                <File size={14} /> {t("account.drafts")}
                {counts?.drafts > 0 && <Badge count={counts.drafts} />}
              </Link>
            )}

            <div className="nav-dropdown-divider" />

            {/* BUY */}
            <SectionLabel>{t("account.buy")}</SectionLabel>
            <Link to="/orders" className="nav-dropdown-item" onClick={close} data-testid="nav-orders-link">
              <Package size={14} /> {t("account.orders")}
            </Link>
            <Link to="/offers?box=buyer" className="nav-dropdown-item" onClick={close}>
              <Tag size={14} /> {t("account.offersSent")}
              <Badge count={counts?.offersSent} />
            </Link>

            <div className="nav-dropdown-divider" />

            {/* ACCOUNT */}
            <SectionLabel>{t("account.account")}</SectionLabel>
            <Link to="/messages" className="nav-dropdown-item" onClick={close} data-testid="nav-messages-link">
              <ChatCircle size={14} /> {t("account.messages")}
              <Badge count={counts?.messages} />
            </Link>
            <Link to="/analytics" className="nav-dropdown-item" onClick={close} data-testid="nav-analytics-link">
              <ChartBar size={14} /> {t("account.analytics")}
            </Link>
            <button
              className="nav-dropdown-item"
              onClick={() => setTheme(isDark ? "light" : "dark")}
              role="menuitem"
            >
              {isDark ? <Sun size={14} /> : <Moon size={14} />}
              {isDark ? t("account.lightMode") : t("account.darkMode")}
            </button>

            {isAdmin && (
              <>
                <div className="nav-dropdown-divider" />
                <Link to="/admin/moderation" className="nav-dropdown-item" onClick={close} data-testid="nav-admin-link">
                  <Shield size={14} /> {t("account.moderation")}
                </Link>
                <Link to="/admin/analytics" className="nav-dropdown-item" onClick={close}>
                  <ChartBar size={14} /> {t("account.insights")}
                </Link>
              </>
            )}

            <div className="nav-dropdown-divider" />
            <button
              className="nav-dropdown-item nav-dropdown-item--signout"
              onClick={() => { close(); logout(); }}
              role="menuitem"
              data-testid="nav-logout-button"
            >
              <SignOut size={14} /> {t("account.signOut")}
            </button>
          </motion.nav>
        )}
      </AnimatePresence>
    </div>
  );
}
