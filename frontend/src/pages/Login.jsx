import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login, register, setToken } from "../../api/client.js";

export default function Login() {
  const [mode, setMode] = useState("login"); // "login" | "register"
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = mode === "login" ? await login(email, password) : await register(name, email, password);
      setToken(res.access_token);
      navigate("/");
    } catch (err) {
      setError(err.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 24,
      }}
    >
      <div style={{ width: "100%", maxWidth: 400 }}>
        <div style={{ textAlign: "center", marginBottom: 28 }}>
          <Wordmark />
          <p style={{ color: "var(--text-mid)", fontSize: 14, marginTop: 10 }}>
            Panel intel, not paperwork.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="card" style={{ padding: 28, display: "flex", flexDirection: "column", gap: 16 }}>
          <div style={{ display: "flex", gap: 6, background: "var(--bg-raised)", padding: 4, borderRadius: 10 }}>
            <TabButton active={mode === "login"} onClick={() => setMode("login")}>
              Sign in
            </TabButton>
            <TabButton active={mode === "register"} onClick={() => setMode("register")}>
              Create account
            </TabButton>
          </div>

          {mode === "register" && (
            <div>
              <label className="label">Name</label>
              <input className="input" required value={name} onChange={(e) => setName(e.target.value)} placeholder="Ada Lovelace" />
            </div>
          )}
          <div>
            <label className="label">Email</label>
            <input
              className="input"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@fleet.io"
            />
          </div>
          <div>
            <label className="label">Password</label>
            <input
              className="input"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
            />
          </div>

          {error && (
            <div style={{ color: "var(--critical)", fontSize: 13, fontFamily: "var(--font-mono)" }}>{error}</div>
          )}

          <button type="submit" className="btn btn-primary" disabled={loading} style={{ marginTop: 4 }}>
            {loading ? "Working…" : mode === "login" ? "Sign in" : "Create account"}
          </button>
        </form>
      </div>
    </div>
  );
}

function TabButton({ active, onClick, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="btn"
      style={{
        flex: 1,
        background: active ? "var(--surface)" : "transparent",
        color: active ? "var(--text-hi)" : "var(--text-low)",
        boxShadow: "none",
        padding: "9px 12px",
      }}
    >
      {children}
    </button>
  );
}

function Wordmark() {
  return (
    <div style={{ display: "inline-flex", alignItems: "center", gap: 10 }}>
      <svg width="30" height="30" viewBox="0 0 30 30" fill="none">
        <circle cx="15" cy="15" r="7" fill="var(--gold)" style={{ filter: "drop-shadow(0 0 6px var(--gold))" }} />
        <g stroke="var(--gold)" strokeWidth="2" strokeLinecap="round" opacity="0.7">
          <line x1="15" y1="1" x2="15" y2="5" />
          <line x1="15" y1="25" x2="15" y2="29" />
          <line x1="1" y1="15" x2="5" y2="15" />
          <line x1="25" y1="15" x2="29" y2="15" />
        </g>
      </svg>
      <span className="h-display" style={{ fontSize: 24 }}>
        SolSight
      </span>
    </div>
  );
}
