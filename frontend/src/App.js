import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "sonner";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Nav from "./components/Nav";
import Home from "./pages/Home";
import Shop from "./pages/Shop";
import ListingDetail from "./pages/ListingDetail";
import Auth from "./pages/Auth";
import Sell from "./pages/Sell";
import Dashboard from "./pages/Dashboard";
import Offers from "./pages/Offers";
import Orders from "./pages/Orders";
import Messages from "./pages/Messages";
import AdminModeration from "./pages/AdminModeration";

function Protected({ children }) {
  const { user, ready } = useAuth();
  if (!ready) return <div className="container" style={{ padding: 80 }}><div className="spin" /></div>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function Footer() {
  return (
    <footer className="footer">
      <div className="container row" style={{ justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
        <span className="brand" style={{ fontSize: 16 }}>ARCHIVE<span style={{ color: "var(--primary)" }}>.</span></span>
        <span className="overline">Premium fashion resale · Kyiv → Europe</span>
      </div>
    </footer>
  );
}

function Shell() {
  return (
    <BrowserRouter>
      <Nav />
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/shop" element={<Shop />} />
          <Route path="/listing/:idOrSlug" element={<ListingDetail />} />
          <Route path="/login" element={<Auth mode="login" />} />
          <Route path="/register" element={<Auth mode="register" />} />
          <Route path="/sell" element={<Protected><Sell /></Protected>} />
          <Route path="/offers" element={<Protected><Offers /></Protected>} />
          <Route path="/orders" element={<Protected><Orders /></Protected>} />
          <Route path="/messages" element={<Protected><Messages /></Protected>} />
          <Route path="/admin/moderation" element={<Protected><AdminModeration /></Protected>} />
          <Route path="/dashboard" element={<Protected><Dashboard /></Protected>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      <Footer />
    </BrowserRouter>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Toaster position="bottom-right" theme="light" />
      <Shell />
    </AuthProvider>
  );
}
