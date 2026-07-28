import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight } from "@phosphor-icons/react";
import api from "../lib/api";
import ProductCard from "../components/ProductCard";

const HERO = "https://images.unsplash.com/photo-1508125673219-7cec6bc90159?crop=entropy&cs=srgb&fm=jpg&q=85&w=1200";

export default function Home() {
  const [items, setItems] = useState([]);
  const [cats, setCats] = useState([]);

  useEffect(() => {
    api.get("/listings?page_size=8").then((r) => setItems(r.data.items)).catch(() => {});
    api.get("/taxonomy/categories").then((r) => setCats(r.data.categories.slice(0, 8))).catch(() => {});
  }, []);

  return (
    <div className="container">
      <section className="hero" data-testid="home-hero">
        <div className="hero-copy">
          <span className="overline">Kyiv → Europe · Premium resale</span>
          <h1>Buy & sell the fashion worth keeping.</h1>
          <p className="hint" style={{ maxWidth: 420 }}>
            Curated designer, streetwear and archive pieces. Structured listings,
            transparent seller reputation, secure escrow. List an item in under a minute.
          </p>
          <div className="row" style={{ gap: 12 }}>
            <Link to="/shop" className="btn btn-primary" data-testid="hero-shop-button">
              Shop the marketplace <ArrowRight size={16} weight="bold" />
            </Link>
            <Link to="/sell" className="btn" data-testid="hero-sell-button">Start selling</Link>
          </div>
        </div>
        <div className="hero-img"><img src={HERO} alt="Fashion editorial"
          onError={(e) => { e.currentTarget.style.display = "none"; }} /></div>
      </section>

      <div className="toolbar" data-testid="home-categories">
        {cats.map((c) => (
          <Link key={c.slug} to={`/shop?category=${c.slug}`} className="chip">{c.name}</Link>
        ))}
      </div>

      <div className="section-head">
        <h2>Just dropped</h2>
        <Link to="/shop" className="overline" data-testid="home-viewall">View all →</Link>
      </div>
      <div className="grid grid-products" data-testid="home-latest-grid">
        {items.map((l) => <ProductCard key={l.id} listing={l} />)}
      </div>
    </div>
  );
}
