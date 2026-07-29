import React, { useEffect, useState } from "react";
import { Sparkle, ArrowClockwise } from "@phosphor-icons/react";
import { toast } from "sonner";
import api, { apiError } from "../lib/api";

const KIND_LABEL = {
  detected_brand: "Detected brand",
  category_suggestion: "Suggested category",
  quality_score: "Listing quality",
  condition_estimate: "Condition estimate",
};

export default function AIInsights({ listingId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);

  const load = () => {
    setLoading(true);
    api.get(`/ai/listings/${listingId}`)
      .then((r) => setData(r.data.enrichment))
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  };
  useEffect(load, [listingId]);

  const run = async () => {
    setRunning(true);
    try {
      const { data: res } = await api.post(`/ai/listings/${listingId}/enrich`);
      setData(res.enrichment);
      toast.success("AI insights refreshed");
    } catch (e) {
      toast.error(apiError(e));
    } finally {
      setRunning(false);
    }
  };

  const quality = data?.analyses?.find((a) => a.kind === "quality_score");
  const attrs = data?.analyses?.filter((a) => a.kind !== "quality_score") || [];

  return (
    <div className="panel" data-testid="ai-insights" style={{ marginTop: 20 }}>
      <div className="row" style={{ justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <div className="row" style={{ gap: 8, color: "var(--primary)" }}>
          <Sparkle size={18} weight="fill" />
          <span className="overline">AI insights</span>
        </div>
        <button className="btn btn-sm" onClick={run} disabled={running}
          data-testid="ai-insights-refresh" style={{ display: "inline-flex", gap: 6, alignItems: "center" }}>
          <ArrowClockwise size={14} weight="bold" /> {running ? "Analysing…" : (data ? "Refresh" : "Analyse")}
        </button>
      </div>

      {loading ? (
        <div style={{ padding: 20 }}><div className="spin" /></div>
      ) : !data ? (
        <p className="hint" data-testid="ai-insights-empty">No AI analysis yet. Run one to get advisory suggestions.</p>
      ) : (
        <>
          {quality && (
            <div style={{ marginBottom: 14 }} data-testid="ai-quality-score">
              <div className="row" style={{ justifyContent: "space-between", marginBottom: 4 }}>
                <span className="hint">Listing quality</span>
                <span style={{ fontWeight: 700 }}>{quality.value}/100</span>
              </div>
              <div style={{ background: "#f0f0f0", height: 8, borderRadius: 5 }}>
                <div style={{ width: `${quality.value}%`, height: "100%",
                  background: Number(quality.value) > 60 ? "var(--success)" : "var(--primary)", borderRadius: 5 }} />
              </div>
            </div>
          )}

          {attrs.length > 0 && (
            <div className="row" style={{ gap: 8, flexWrap: "wrap", marginBottom: 12 }} data-testid="ai-attributes">
              {attrs.map((a, i) => (
                <span key={i} className="badge" title={`${Math.round(a.confidence * 100)}% confidence`}>
                  {(KIND_LABEL[a.kind] || a.kind)}: <b style={{ marginLeft: 4 }}>{a.value}</b>
                </span>
              ))}
            </div>
          )}

          {data.recommendations?.length > 0 && (
            <ul style={{ margin: 0, paddingLeft: 18 }} data-testid="ai-recommendations">
              {data.recommendations.map((r, i) => (
                <li key={i} className="hint" style={{ marginBottom: 6, lineHeight: 1.5 }}>{r.message}</li>
              ))}
            </ul>
          )}
          <p className="hint" style={{ marginTop: 10, fontSize: 11, opacity: 0.7 }}>
            Advisory only — AI never changes your listing automatically.
          </p>
        </>
      )}
    </div>
  );
}
