import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { MagnifyingGlass, User, Plus, SignOut } from "@phosphor-icons/react";
import { useAuth } from "../context/AuthContext";

export default function Nav() {
  const { user, logout } = useAuth();
  const [q, setQ] = useState("");
  const navigate = useNavigate();

  const submit = (e) => {
    e.preventDefault();
    navigate(`/shop?q=${encodeURIComponent(q)}`);
  };

  return (
    <header className="nav">
      <div className="container nav-inner">
        <Link to="/" className="brand" data-testid="brand-logo">
          ARCHIVE<span>.</span>
        </Link>
        <form className="nav-search" onSubmit={submit}>
          <input
            data-testid="nav-search-input"
            type="text"
            placeholder="Search brands, items, categories…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            style={{ paddingLeft: 40 }}
          />
          <MagnifyingGlass
            size={18}
            style={{ position: "absolute", left: 14, top: 13, color: "#525252" }}
          />
        </form>
        <div className="spacer" />
        <nav className="nav-links">
          <Link to="/shop" className="nav-link" data-testid="nav-shop-link">Shop</Link>
          {user ? (
            <>
              <Link to="/sell" className="btn btn-primary btn-sm" data-testid="nav-sell-button">
                <Plus size={16} weight="bold" /> Sell
              </Link>
              <Link to="/offers" className="nav-link" data-testid="nav-offers-link">Offers</Link>
              <Link to="/orders" className="nav-link" data-testid="nav-orders-link">Orders</Link>
              <Link to="/dashboard" className="nav-link row" data-testid="nav-dashboard-link" style={{ gap: 6 }}>
                <User size={18} /> {user.profile?.display_name?.split(" ")[0] || "Account"}
              </Link>
              <button className="nav-link row" onClick={logout} data-testid="nav-logout-button"
                style={{ gap: 6, background: "none", border: "none" }}>
                <SignOut size={18} />
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="nav-link" data-testid="nav-login-link">Log in</Link>
              <Link to="/sell" className="btn btn-primary btn-sm" data-testid="nav-sell-button">
                <Plus size={16} weight="bold" /> Sell
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
