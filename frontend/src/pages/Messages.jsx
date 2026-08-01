import React, { useCallback, useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import { toast } from "sonner";
import { useTranslation } from "react-i18next";
import api, { apiError, wsUrl } from "../lib/api";
import { useAuth } from "../context/AuthContext";

const fmtTime = (t) => {
  if (!t) return "";
  try { return new Date(t).toLocaleString("en-GB", { hour: "2-digit", minute: "2-digit", day: "2-digit", month: "short" }); }
  catch { return ""; }
};

export default function Messages() {
  const { user } = useAuth();
  const { t } = useTranslation("messages");
  const q = new URLSearchParams(useLocation().search);
  const initialConv = q.get("c");

  const [conversations, setConversations] = useState([]);
  const [activeId, setActiveId] = useState(initialConv || null);
  const [thread, setThread] = useState(null);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(true);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);
  const bottomRef = useRef(null);
  const activeIdRef = useRef(activeId);
  activeIdRef.current = activeId;

  const loadConversations = useCallback(async () => {
    try {
      const r = await api.get("/conversations");
      setConversations(r.data.items);
      if (!activeIdRef.current && r.data.items.length > 0) setActiveId(r.data.items[0].id);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadThread = useCallback(async (id) => {
    if (!id) return;
    try {
      const r = await api.get(`/conversations/${id}/messages`);
      setThread(r.data);
    } catch (e) {
      toast.error(apiError(e));
    }
  }, []);

  useEffect(() => { loadConversations(); }, [loadConversations]);
  useEffect(() => { if (activeId) loadThread(activeId); }, [activeId, loadThread]);
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [thread]);

  // real-time WebSocket
  useEffect(() => {
    if (!user) return;
    const ws = new WebSocket(wsUrl("/api/ws/messages"));
    wsRef.current = ws;
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (ev) => {
      let msg;
      try { msg = JSON.parse(ev.data); } catch { return; }
      if (msg.type === "message") {
        if (msg.conversation_id === activeIdRef.current) {
          setThread((t) => (t ? { ...t, messages: [...t.messages.filter((m) => m.message_id !== msg.message_id), msg] } : t));
          if (msg.author_id !== user.id) api.post(`/conversations/${msg.conversation_id}/read`).catch(() => {});
        }
        loadConversations();
      } else if (msg.type === "read" || msg.type === "closed") {
        if (msg.conversation_id === activeIdRef.current) loadThread(activeIdRef.current);
      }
    };
    return () => ws.close();
  }, [user, loadConversations, loadThread]);

  const send = async () => {
    const content = draft.trim();
    if (!content || !activeId) return;
    setDraft("");
    try {
      await api.post(`/conversations/${activeId}/messages`, { content });
    } catch (e) {
      toast.error(apiError(e));
      setDraft(content);
    }
  };

  if (!user) return null;

  return (
    <div className="container" style={{ paddingTop: 28, paddingBottom: 40 }}>

      {/* Header */}
      <div className="row" style={{ justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <h1 style={{ fontSize: 26, fontWeight: 700, letterSpacing: "-0.02em", margin: 0 }}
          data-testid="messages-heading">{t("heading")}</h1>
        <span className="overline" data-testid="ws-status"
          style={{ color: connected ? "var(--success)" : "var(--muted)", fontSize: 11 }}>
          {connected ? "● Live" : "○ Offline"}
        </span>
      </div>

      {loading ? (
        <div style={{ padding: "40px 0", display: "flex", justifyContent: "center" }}>
          <div className="spin" />
        </div>
      ) : conversations.length === 0 ? (
        <div className="empty" data-testid="messages-empty">
          {t("empty")}
        </div>
      ) : (
        <div style={{
          display: "grid",
          gridTemplateColumns: "280px 1fr",
          gap: 0,
          height: "calc(100vh - 220px)",
          minHeight: 500,
          border: "1px solid var(--border)",
          borderRadius: 12,
          overflow: "hidden",
          background: "var(--surface)",
        }}>

          {/* Conversation list */}
          <div style={{ borderRight: "1px solid var(--border)", overflowY: "auto" }}
            data-testid="conversation-list">
            {conversations.map((c) => (
              <button key={c.id}
                onClick={() => setActiveId(c.id)}
                data-testid={`conversation-${c.id}`}
                style={{
                  width: "100%", textAlign: "left", padding: "14px 16px",
                  background: c.id === activeId ? "var(--subtle)" : "transparent",
                  border: "none", borderBottom: "1px solid var(--border)",
                  cursor: "pointer",
                  transition: "background 0.12s",
                }}>
                <div className="row" style={{ justifyContent: "space-between", gap: 6, marginBottom: 4 }}>
                  <span style={{ fontWeight: 600, fontSize: 13, color: "var(--text)" }}>
                    {c.counterparty_name || "User"}
                  </span>
                  {c.unread > 0 && (
                    <span className="badge badge-primary" style={{ minWidth: 18, textAlign: "center" }}
                      data-testid={`conversation-unread-${c.id}`}>{c.unread}</span>
                  )}
                </div>
                <div style={{ fontSize: 12, color: "var(--muted)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                  {c.last_message || t("thread.empty")}
                </div>
              </button>
            ))}
          </div>

          {/* Chat panel */}
          <div style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}
            data-testid="message-thread">
            {!thread ? (
              <div style={{ display: "flex", alignItems: "center", justifyContent: "center", flex: 1 }}>
                <span className="hint">{t("prompt.select")}</span>
              </div>
            ) : (
              <>
                {/* Thread header */}
                <div className="row" style={{
                  padding: "14px 18px",
                  borderBottom: "1px solid var(--border)",
                  justifyContent: "space-between",
                  flexShrink: 0,
                }}>
                  <span style={{ fontWeight: 600, fontSize: 14 }} data-testid="thread-counterparty">
                    {thread.counterparty_name || "User"}
                  </span>
                  <span className="overline" style={{ color: "var(--muted)", fontSize: 10 }}>
                    {thread.context_type} · {thread.status}
                  </span>
                </div>

                {/* Messages */}
                <div style={{ flex: 1, overflowY: "auto", padding: "16px 18px", display: "flex", flexDirection: "column", gap: 8 }}
                  data-testid="thread-messages">
                  {thread.messages.map((m) => {
                    const mine = m.author_id === user.id;
                    return (
                      <div key={m.message_id} data-testid={`chat-bubble-${m.message_id}`}
                        style={{
                          alignSelf: mine ? "flex-end" : "flex-start",
                          maxWidth: "72%",
                          background: mine ? "var(--text)" : "var(--subtle)",
                          color: mine ? "#fff" : "var(--text)",
                          padding: "9px 14px",
                          borderRadius: mine ? "12px 12px 2px 12px" : "12px 12px 12px 2px",
                        }}>
                        <div style={{ fontSize: 14, lineHeight: 1.5 }}>{m.content}</div>
                        <div style={{ fontSize: 10, opacity: 0.55, marginTop: 3 }}>{fmtTime(m.created_at)}</div>
                      </div>
                    );
                  })}
                  {thread.messages.length === 0 && (
                    <span className="hint" style={{ alignSelf: "center", marginTop: 40 }}>Say hello 👋</span>
                  )}
                  <div ref={bottomRef} />
                </div>

                {/* Input */}
                {thread.status !== "Closed" ? (
                  <div className="row" style={{
                    padding: "12px 16px",
                    borderTop: "1px solid var(--border)",
                    gap: 8, flexShrink: 0,
                  }}>
                    <input data-testid="message-input" value={draft}
                      placeholder="Write a message…"
                      onChange={(e) => setDraft(e.target.value)}
                      onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
                      style={{ flex: 1 }} />
                    <button className="btn btn-primary btn-sm" onClick={send}
                      data-testid="message-send-button">Send</button>
                  </div>
                ) : (
                  <div className="hint" style={{ padding: "12px 16px", borderTop: "1px solid var(--border)", flexShrink: 0 }}>
                    This conversation is closed.
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
