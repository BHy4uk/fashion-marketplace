import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { useAuth } from "../context/AuthContext";
import { apiError } from "../lib/api";

export default function Auth({ mode }) {
  const isLogin = mode === "login";
  const { login, register } = useAuth();
  const navigate = useNavigate();
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
      toast.success(isLogin ? "Welcome back" : "Account created");
      navigate("/");
    } catch (err) {
      setError(apiError(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="container">
      <div className="form-narrow">
        <div className="panel">
          <span className="overline">{isLogin ? "Welcome back" : "Join ARCHIVE"}</span>
          <h1 style={{ fontSize: 26, margin: "6px 0 20px" }}>
            {isLogin ? "Log in" : "Create your account"}
          </h1>
          <form onSubmit={submit} className="stack" style={{ gap: 14 }}>
            {!isLogin && (
              <div>
                <label className="field overline">Display name</label>
                <input data-testid="auth-name-input" value={name}
                  onChange={(e) => setName(e.target.value)} required />
              </div>
            )}
            <div>
              <label className="field overline">Email</label>
              <input data-testid="auth-email-input" type="email" value={email}
                onChange={(e) => setEmail(e.target.value)} required />
            </div>
            <div>
              <label className="field overline">Password</label>
              <input data-testid="auth-password-input" type="password" value={password}
                onChange={(e) => setPassword(e.target.value)} required minLength={8} />
            </div>
            {error && <div className="error-text" data-testid="auth-error">{error}</div>}
            <button className="btn btn-primary btn-block" disabled={busy}
              data-testid="auth-submit-button">
              {busy ? "…" : isLogin ? "Log in" : "Create account"}
            </button>
          </form>
          <p className="hint mt-16">
            {isLogin ? (
              <>No account? <Link to="/register" style={{ color: "var(--primary)" }} data-testid="auth-switch-register">Register</Link></>
            ) : (
              <>Have an account? <Link to="/login" style={{ color: "var(--primary)" }} data-testid="auth-switch-login">Log in</Link></>
            )}
          </p>
        </div>
      </div>
    </div>
  );
}
