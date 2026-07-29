import React, { useCallback, useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import { toast } from "sonner";
import api, { apiError, wsUrl } from "../lib/api";
import { useAuth } from "../context/AuthContext";

const fmtTime = (t) => {
  if (!t) return "";
  try { return new Date(t).toLocaleString("en-GB", { hour: "2-digit", minute: "2-digit", day: "2-digit", month: "short" }); }
  catch { return ""; }
};

export default function Messages() {
  const { user } = useAuth();
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
    <div className="container" style={{ paddingTop: 24, paddingBottom: 40 }}>
      <div className="section-head">
        <h2 data-testid="messages-heading">Messages</h2>
        <span className="overline" data-testid="ws-status"
          style={{ color: connected ? "var(--success)" : "var(--muted, #999)" }}>
          {connected ? "● Live" : "○ Offline"}
        </span>
      </div>

      {loading ? (
        <div style={{ padding: 40 }}><div className="spin" /></div>
      ) : conversations.length === 0 ? (
        <div className="empty" data-testid="messages-empty">
          No conversations yet. Start one from a listing or an order.
        </div>
      ) : (
        <div className="msg-layout" style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: 16 }}>
          <div className="stack" style={{ gap: 8 }} data-testid="conversation-list">
            {conversations.map((c) => (
              <button key={c.id}
                className={`panel ${c.id === activeId ? "chip-active" : ""}`}
                onClick={() => setActiveId(c.id)}
                data-testid={`conversation-${c.id}`}
                style={{ textAlign: "left", padding: 12, border: c.id === activeId ? "2px solid var(--primary)" : undefined, cursor: "pointer" }}>
                <div className="row" style={{ justifyContent: "space-between", gap: 8 }}>
                  <span style={{ fontWeight: 600, fontSize: 14 }}>{c.counterparty_name || "User"}</span>
                  {c.unread > 0 && (
                    <span className="badge badge-primary" data-testid={`conversation-unread-${c.id}`}>{c.unread}</span>
                  )}
                </div>
                <div className="hint" style={{ marginTop: 4, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                  {c.context_type} · {c.last_message || "No messages yet"}
                </div>
              </button>
            ))}
          </div>

          <div className="panel" style={{ padding: 0, display: "flex", flexDirection: "column", minHeight: 460 }}
            data-testid="message-thread">
            {!thread ? (
              <div className="empty" style={{ margin: "auto" }}>Select a conversation</div>
            ) : (
              <>
                <div className="row" style={{ padding: 14, borderBottom: "1px solid var(--line, #eee)", justifyContent: "space-between" }}>
                  <span style={{ fontWeight: 600 }} data-testid="thread-counterparty">{thread.counterparty_name || "User"}</span>
                  <span className="overline">{thread.context_type} · {thread.status}</span>
                </div>
                <div style={{ flex: 1, overflowY: "auto", padding: 14, display: "flex", flexDirection: "column", gap: 8, maxHeight: 420 }}
                  data-testid="thread-messages">
                  {thread.messages.map((m) => {
                    const mine = m.author_id === user.id;
                    return (
                      <div key={m.message_id} data-testid={`chat-bubble-${m.message_id}`}
                        style={{ alignSelf: mine ? "flex-end" : "flex-start", maxWidth: "70%",
                          background: mine ? "var(--primary)" : "var(--bg-soft, #f2f2f2)",
                          color: mine ? "#fff" : "inherit", padding: "8px 12px", borderRadius: 12 }}>
                        <div style={{ fontSize: 14 }}>{m.content}</div>
                        <div style={{ fontSize: 10, opacity: 0.7, marginTop: 2 }}>{fmtTime(m.created_at)}</div>
                      </div>
                    );
                  })}
                  {thread.messages.length === 0 && <div className="hint">Say hello 👋</div>}
                  <div ref={bottomRef} />
                </div>
                {thread.status !== "Closed" ? (
                  <div className="row" style={{ padding: 12, borderTop: "1px solid var(--line, #eee)", gap: 8 }}>
                    <input data-testid="message-input" value={draft} placeholder="Write a message…"
                      onChange={(e) => setDraft(e.target.value)}
                      onKeyDown={(e) => { if (e.key === "Enter") send(); }}
                      style={{ flex: 1 }} />
                    <button className="btn btn-primary btn-sm" onClick={send} data-testid="message-send-button">Send</button>
                  </div>
                ) : (
                  <div className="hint" style={{ padding: 12 }}>This conversation is closed.</div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
