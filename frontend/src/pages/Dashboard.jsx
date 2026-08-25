import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { listPanels, createPanel, clearToken, me } from "../../api/client.js";
import PanelCard from "../components/PanelCard.jsx";

export default function Dashboard() {
  const [panels, setPanels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [user, setUser] = useState(null);
  const navigate = useNavigate();

  async function refresh() {
    try {
      const data = await listPanels();
      setPanels(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
    me().then(setUser).catch(() => {});
  }, []);

  function handleLogout() {
    clearToken();
    navigate("/login");
  }

  const summary = summarize(panels);

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto", padding: "32px 24px 64px" }}>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 32, gap: 16, flexWrap: "wrap" }}>
        <div>
          <div className="eyebrow">Fleet overview{user ? ` · ${user.name}` : ""}</div>
          <h1 className="h-display" style={{ fontSize: 32, margin: "6px 0 0" }}>
            Your panels, at a glance.
          </h1>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <button className="btn btn-primary" onClick={() => setShowForm((s) => !s)}>
            + Add panel
          </button>
          <button className="btn btn-ghost" onClick={handleLogout}>
            Log out
          </button>
        </div>
      </header>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14, marginBottom: 28 }}>
        <StatCard label="Panels tracked" value={panels.length} accent="var(--gold)" />
        <StatCard label="Needs attention" value={summary.warningOrCritical} accent="var(--warning)" />
        <StatCard label="Critical" value={summary.critical} accent="var(--critical)" />
      </div>

      {showForm && (
        <AddPanelForm
          onCreated={() => {
            setShowForm(false);
            refresh();
          }}
          onCancel={() => setShowForm(false)}
        />
      )}

      {loading && <div style={{ color: "var(--text-low)", fontFamily: "var(--font-mono)" }}>loading fleet…</div>}
      {error && <div style={{ color: "var(--critical)", fontFamily: "var(--font-mono)" }}>{error}</div>}

      {!loading && panels.length === 0 && !showForm && (
        <div className="card" style={{ padding: 40, textAlign: "center", color: "var(--text-mid)" }}>
          <div className="h-display" style={{ fontSize: 18, marginBottom: 6 }}>No panels yet</div>
          <p style={{ fontSize: 14, marginBottom: 16 }}>Add your first panel to start tracking its health.</p>
          <button className="btn btn-primary" onClick={() => setShowForm(true)}>
            + Add panel
          </button>
        </div>
      )}

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
          gap: 16,
        }}
      >
        {panels.map((p) => (
          <PanelCard key={p.id} panel={p} />
        ))}
      </div>
    </div>
  );
}

function summarize(panels) {
  const warningOrCritical = panels.filter((p) => p.latest_status === "Warning" || p.latest_status === "Critical").length;
  const critical = panels.filter((p) => p.latest_status === "Critical").length;
  return { warningOrCritical, critical };
}

function StatCard({ label, value, accent }) {
  return (
    <div className="card" style={{ padding: "18px 20px", borderLeft: `3px solid ${accent}` }}>
      <div className="eyebrow">{label}</div>
      <div className="h-display" style={{ fontSize: 30, marginTop: 6 }}>
        {value}
      </div>
    </div>
  );
}

function AddPanelForm({ onCreated, onCancel }) {
  const [panelId, setPanelId] = useState("");
  const [location, setLocation] = useState("");
  const [installDate, setInstallDate] = useState("");
  const [ratedPower, setRatedPower] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await createPanel({
        panel_id: panelId,
        location,
        installation_date: installDate,
        rated_power: parseFloat(ratedPower),
      });
      onCreated();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="card" style={{ padding: 22, marginBottom: 24, display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, alignItems: "end" }}>
      <div>
        <label className="label">Panel ID</label>
        <input className="input" required value={panelId} onChange={(e) => setPanelId(e.target.value)} placeholder="PNL-014" />
      </div>
      <div>
        <label className="label">Location</label>
        <input className="input" required value={location} onChange={(e) => setLocation(e.target.value)} placeholder="Rooftop A" />
      </div>
      <div>
        <label className="label">Installed</label>
        <input className="input" type="date" required value={installDate} onChange={(e) => setInstallDate(e.target.value)} />
      </div>
      <div>
        <label className="label">Rated power (W)</label>
        <input className="input" type="number" required value={ratedPower} onChange={(e) => setRatedPower(e.target.value)} placeholder="400" />
      </div>
      {error && <div style={{ gridColumn: "1 / -1", color: "var(--critical)", fontSize: 13, fontFamily: "var(--font-mono)" }}>{error}</div>}
      <div style={{ gridColumn: "1 / -1", display: "flex", gap: 10 }}>
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? "Adding…" : "Add panel"}
        </button>
        <button type="button" className="btn btn-ghost" onClick={onCancel}>
          Cancel
        </button>
      </div>
    </form>
  );
}
