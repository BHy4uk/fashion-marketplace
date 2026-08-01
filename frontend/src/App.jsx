import React from "react";
import { BrowserRouter, Routes, Route, Navigate, useLocation, Link } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { Toaster } from "sonner";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { ThemeProvider } from "./context/ThemeContext";
import { MarketProvider } from "./context/MarketContext";
import Nav from "./components/Nav";

function LogoMark({ size = 14 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 14 14" fill="none" aria-hidden="true">
      <path d="M7 0.5L13.5 7L7 13.5L0.5 7Z" fill="currentColor" />
    </svg>
  );
}
import Home from "./pages/Home";
import Shop from "./pages/Shop";
import ListingDetail from "./pages/ListingDetail";
import Auth from "./pages/Auth";
import Sell from "./pages/Sell";
import EditListing from "./pages/EditListing";
import Dashboard from "./pages/Dashboard";
import Offers from "./pages/Offers";
import Orders from "./pages/Orders";
import Messages from "./pages/Messages";
import AdminModeration from "./pages/AdminModeration";
import SellerAnalytics from "./pages/SellerAnalytics";
import AdminAnalytics from "./pages/AdminAnalytics";
import Checkout from "./pages/Checkout";
import { pageVariants } from "./lib/motion";

function PageLoader() {
  return (
    <div className="container" style={{ padding: "80px 24px" }}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 24 }}>
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i}>
            <div className="skeleton" style={{ aspectRatio: "3/4", marginBottom: 10, borderRadius: 8 }} />
            <div className="skeleton" style={{ height: 12, width: "55%", marginBottom: 6, borderRadius: 4 }} />
            <div className="skeleton" style={{ height: 12, width: "75%", borderRadius: 4 }} />
          </div>
        ))}
      </div>
    </div>
  );
}

function Protected({ children }) {
  const { user, ready } = useAuth();
  if (!ready) return <PageLoader />;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function Footer() {
  return (
    <footer className="footer">
      <div className="container footer-inner">
        <Link to="/" className="brand" style={{ fontSize: 15, display: "flex", alignItems: "center", gap: 7 }}>
          <LogoMark />
          ARCHIVE
        </Link>
        <nav style={{ display: "flex", gap: 24, alignItems: "center", flexWrap: "wrap" }}>
          <Link to="/shop" className="footer-link">Shop</Link>
          <Link to="/sell" className="footer-link">Sell</Link>
          <Link to="/login" className="footer-link">Sign in</Link>
          <Link to="/register" className="footer-link">Register</Link>
        </nav>
        <span className="footer-link" style={{ opacity: 0.45 }}>© 2026 ARCHIVE</span>
      </div>
    </footer>
  );
}

function AnimatedRoutes() {
  const location = useLocation();
  return (
    <AnimatePresence mode="wait" initial={false}>
      <motion.div
        key={location.pathname}
        variants={pageVariants}
        initial="hidden"
        animate="visible"
        exit="exit"
      >
        <Routes location={location}>
          <Route path="/" element={<Home />} />
          <Route path="/shop" element={<Shop />} />
          <Route path="/listing/:idOrSlug" element={<ListingDetail />} />
          <Route path="/login" element={<Auth mode="login" />} />
          <Route path="/register" element={<Auth mode="register" />} />
          <Route path="/sell" element={<Protected><Sell /></Protected>} />
          <Route path="/checkout" element={<Protected><Checkout /></Protected>} />
          <Route path="/edit/:id" element={<Protected><EditListing /></Protected>} />
          <Route path="/offers" element={<Protected><Offers /></Protected>} />
          <Route path="/orders" element={<Protected><Orders /></Protected>} />
          <Route path="/messages" element={<Protected><Messages /></Protected>} />
          <Route path="/admin/moderation" element={<Protected><AdminModeration /></Protected>} />
          <Route path="/admin/analytics" element={<Protected><AdminAnalytics /></Protected>} />
          <Route path="/analytics" element={<Protected><SellerAnalytics /></Protected>} />
          <Route path="/dashboard" element={<Protected><Dashboard /></Protected>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </motion.div>
    </AnimatePresence>
  );
}

function Shell() {
  return (
    <BrowserRouter>
      <Nav />
      <main>
        <AnimatedRoutes />
      </main>
      <Footer />
    </BrowserRouter>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <MarketProvider>
        <AuthProvider>
          <Toaster position="bottom-right" />
          <Shell />
        </AuthProvider>
      </MarketProvider>
    </ThemeProvider>
  );
}
