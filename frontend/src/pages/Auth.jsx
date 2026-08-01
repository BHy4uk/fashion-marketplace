import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { useTranslation } from "react-i18next";
import { useAuth } from "../context/AuthContext";
import { apiError } from "../lib/api";

const AUTH_IMG = "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?auto=format&fit=crop&w=1600&q=80";

export default function Auth({ mode }) {
  const isLogin = mode === "login";
  const { login, register } = useAuth();
  const navigate = useNavigate();
  const { t } = useTranslation("auth");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (isLogin) await login(email, password);
      else await register(email, password, name);
      toast.success(isLogin ? t("toast.loginSuccess") : t("toast.registerSuccess"));
      navigate("/");
    } catch (err) {
      setError(apiError(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="auth-layout">
      {/* ── Editorial image panel ── */}
      <div className="auth-img-panel" aria-hidden="true">
        <img
          src={AUTH_IMG}
          alt=""
          loading="eager"
          onError={(e) => { e.currentTarget.parentElement.style.background = "#111111"; e.currentTarget.style.display = "none"; }}
        />
          <span className="auth-img-overlay">
          <span className="brand" style={{ color: "#fff", fontSize: 20 }}>ARCHIVE</span>
          <p style={{ color: "rgba(255,255,255,0.6)", fontSize: 13, marginTop: 6 }}>
            {t("brand.tagline")}
          </p>
        </span>
      </div>

      {/* ── Form panel ── */}
      <div className="auth-form-panel">
        <div className="auth-form-inner">
          <span className="overline">{isLogin ? t("overline.login") : t("overline.register")}</span>
          <h1 style={{ fontSize: 28, margin: "8px 0 28px", letterSpacing: "-0.02em" }}>
            {isLogin ? t("heading.login") : t("heading.register")}
          </h1>

          <form onSubmit={submit} className="stack" style={{ gap: 16 }}>
            {!isLogin && (
              <div>
                <label className="field overline">{t("field.displayName")}</label>
                <input
                  data-testid="auth-name-input"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder={t("placeholder.name")}
                  required
                />
              </div>
            )}
            <div>
              <label className="field overline">{t("field.email")}</label>
              <input
                data-testid="auth-email-input"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder={t("placeholder.email")}
                required
              />
            </div>
            <div>
              <label className="field overline">{t("field.password")}</label>
              <input
                data-testid="auth-password-input"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={t("placeholder.password")}
                required
                minLength={8}
              />
            </div>
            {error && <div className="error-text" data-testid="auth-error">{error}</div>}
            <button
              className="btn btn-primary btn-block"
              disabled={busy}
              data-testid="auth-submit-button"
              style={{ marginTop: 4 }}
            >
              {busy ? t("button.loading") : isLogin ? t("button.login") : t("button.register")}
            </button>
          </form>

          <p className="hint" style={{ marginTop: 20 }}>
            {isLogin ? (
              <>{t("text.noAccount")}{" "}
                <Link to="/register" style={{ color: "var(--text)", fontWeight: 600, textDecoration: "underline" }} data-testid="auth-switch-register">
                  {t("link.register")}
                </Link>
              </>
            ) : (
              <>{t("text.haveAccount")}{" "}
                <Link to="/login" style={{ color: "var(--text)", fontWeight: 600, textDecoration: "underline" }} data-testid="auth-switch-login">
                  {t("link.login")}
                </Link>
              </>
            )}
          </p>
        </div>
      </div>
    </div>
  );
}
