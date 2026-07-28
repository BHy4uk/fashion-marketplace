import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import api, { formatPrice, apiError } from "../lib/api";
import { useAuth } from "../context/AuthContext";

const STATE_BADGE = {
  Published: "badge-solid", Draft: "badge", Reserved: "badge-primary",
  Sold: "badge", Archived: "badge",
};

export default function Dashboard() {
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    api.get("/listings/mine").then((r) => setItems(r.data.items)).finally(() => setLoading(false));
  };
  useEffect(load, []);

  const remove = async (id) => {
    try {
      await api.delete(`/listings/${id}`);
      toast.success("Listing removed");
      load();
    } catch (e) {
      toast.error(apiError(e));
    }
  };

  const rep = user?.reputation || {};

  return (
    <div className="container" style={{ paddingTop: 24, paddingBottom: 60 }}>
      <div className="panel mb-24" data-testid="dashboard-header">
        <span className="overline">Seller dashboard</span>
        <h1 style={{ fontSize: 26, margin: "6px 0" }}>{user?.profile?.display_name}</h1>
        <div className="row" style={{ gap: 24 }}>
          <div><div className="heading" style={{ fontSize: 22 }}>{items.length}</div><span className="overline">Listings</span></div>
          <div><div className="heading" style={{ fontSize: 22 }}>{rep.average_rating || "—"}</div><span className="overline">Rating</span></div>
          <div><div className="heading" style={{ fontSize: 22 }}>{rep.completed_reviews || 0}</div><span className="overline">Reviews</span></div>
          <div className="spacer" />
          <Link to="/sell" className="btn btn-primary" data-testid="dashboard-new-listing">+ New listing</Link>
        </div>
      </div>

      <div className="section-head"><h2>My listings</h2></div>
      {loading ? (
        <div style={{ padding: 40 }}><div className="spin" /></div>
      ) : items.length === 0 ? (
        <div className="empty" data-testid="dashboard-empty">
          No listings yet. <Link to="/sell" style={{ color: "var(--primary)" }}>Create your first one →</Link>
        </div>
      ) : (
        <div className="grid grid-products" data-testid="dashboard-grid">
          {items.map((l) => (
            <div key={l.id} data-testid={`dashboard-item-${l.id}`}>
              <Link to={`/listing/${l.slug || l.id}`} className="product-img" style={{ display: "block" }}>
                {l.images?.[0] && <img src={l.images[0].url} alt={l.title} />}
              </Link>
              <div className="product-info">
                <div className="row" style={{ justifyContent: "space-between" }}>
                  <span className="product-brand">{l.attributes?.brand || "—"}</span>
                  <span className={`badge ${STATE_BADGE[l.state] || "badge"}`}>{l.state}</span>
                </div>
                <div className="product-title">{l.title}</div>
                <div className="row" style={{ justifyContent: "space-between" }}>
                  <span className="product-price">{formatPrice(l.price)}</span>
                  {["Published", "Draft", "Ready", "Archived"].includes(l.state) && (
                    <button className="btn btn-sm" onClick={() => remove(l.id)}
                      data-testid={`dashboard-archive-${l.id}`}>Remove</button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
