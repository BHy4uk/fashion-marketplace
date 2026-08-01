import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight } from "@phosphor-icons/react";
import { motion } from "framer-motion";
import { useTranslation } from "react-i18next";
import api from "../lib/api";
import ProductCard from "../components/ProductCard";
import { ProductCardSkeleton } from "../components/Skeleton";
import { listVariants, listItemVariants } from "../lib/motion";

const HERO_IMG = "https://images.unsplash.com/photo-1624353656309-8be1a6c457be?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1NjZ8MHwxfHNlYXJjaHwzfHxzdHJlZXR3ZWFyJTIwZmFzaGlvbiUyMHBvcnRyYWl0fGVufDB8fHx8MTc4NTI1ODU1MXww&ixlib=rb-4.1.0&q=85&w=1400";

export default function Home() {
  const { t } = useTranslation("home");
  const [items, setItems] = useState([]);
  const [cats, setCats] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get("/listings?page_size=8").catch(() => ({ data: { items: [] } })),
      api.get("/taxonomy/categories").catch(() => ({ data: { categories: [] } })),
    ]).then(([listingsRes, catsRes]) => {
      setItems(listingsRes.data.items);
      setCats(catsRes.data.categories.slice(0, 8));
      setLoading(false);
    });
  }, []);

  return (
    <>
      {/* ── Full-bleed editorial hero (outside container) ─────────────── */}
      <section className="hero" data-testid="home-hero">
        <div className="hero-copy">
          <h1>{t("hero.title").split("\n").map((line, i) => <React.Fragment key={i}>{line}{i < 2 && <br />}</React.Fragment>)}</h1>
          <p className="hint" style={{ maxWidth: 380, lineHeight: 1.7, fontSize: 14 }}>
            {t("hero.description")}
          </p>
          <div className="row" style={{ gap: 12, flexWrap: "wrap" }}>
            <Link to="/shop" className="btn btn-primary" data-testid="hero-shop-button">
              {t("hero.shopButton")} <ArrowRight size={15} weight="bold" />
            </Link>
            <Link to="/sell" className="btn" data-testid="hero-sell-button">{t("hero.sellButton")}</Link>
          </div>
        </div>
        <div className="hero-img">
          <img
            src={HERO_IMG}
            alt={t("hero.imgAlt")}
            loading="eager"
            onError={(e) => { e.currentTarget.parentElement.style.display = "none"; }}
          />
        </div>
      </section>

      {/* ── Container: categories + grid ──────────────────────────────── */}
      <div className="container">
        {cats.length > 0 && (
          <div className="toolbar" data-testid="home-categories">
            {cats.map((c) => (
              <Link key={c.slug} to={`/shop?category=${c.slug}`} className="chip">{c.name}</Link>
            ))}
          </div>
        )}

        <div className="section-head">
          <h2>{t("section.justDropped")}</h2>
          <Link to="/shop" className="overline" style={{ letterSpacing: "0.12em" }} data-testid="home-viewall">{t("section.viewAll")}</Link>
        </div>

        {loading ? (
          <div className="grid grid-products">
            {Array.from({ length: 8 }).map((_, i) => <ProductCardSkeleton key={i} />)}
          </div>
        ) : (
          <motion.div
            className="grid grid-products"
            variants={listVariants}
            initial="hidden"
            animate="visible"
            data-testid="home-latest-grid"
          >
            {items.map((l) => (
              <motion.div key={l.id} variants={listItemVariants}>
                <ProductCard listing={l} />
              </motion.div>
            ))}
          </motion.div>
        )}
      </div>
    </>
  );
}
