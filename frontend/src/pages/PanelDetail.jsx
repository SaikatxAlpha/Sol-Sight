import React, { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getPanel, getPanelHistory, getPanelPrediction } from "../../api/client.js";
import HealthGauge from "../components/HealthGauge.jsx";
import DegradationChart from "../components/DegradationChart.jsx";
import UploadForm from "../components/UploadForm.jsx";

export default function PanelDetail() {
  const { panelId } = useParams();
  const navigate = useNavigate();
  const [panel, setPanel] = useState(null);
  const [history, setHistory] = useState([]);
  const [prediction, setPrediction] = useState(null);
  const [lastResult, setLastResult] = useState(null);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    try {
      const [p, h] = await Promise.all([getPanel(panelId), getPanelHistory(panelId)]);
      setPanel(p);
      setHistory(h);
      try {
        setPrediction(await getPanelPrediction(panelId));
      } catch {
        setPrediction(null);
      }
    } catch (err) {
      setError(err.message);
    }
  }, [panelId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  function handleResult(result) {
    setLastResult(result);
    refresh();
  }

  if (error) {
    return (
      <div style={{ maxWidth: 900, margin: "60px auto", padding: 24 }}>
        <div style={{ color: "var(--critical)", fontFamily: "var(--font-mono)" }}>{error}</div>
        <button className="btn btn-ghost" style={{ marginTop: 16 }} onClick={() => navigate("/")}>
          ← Back to fleet
        </button>
      </div>
    );
  }

  if (!panel) {
    return <div style={{ padding: 40, color: "var(--text-low)", fontFamily: "var(--font-mono)" }}>loading panel…</div>;
  }

  return (
    <div style={{ maxWidth: 1000, margin: "0 auto", padding: "32px 24px 64px" }}>
      <button className="btn btn-ghost" onClick={() => navigate("/")} style={{ marginBottom: 20 }}>
        ← Fleet
      </button>

      <header style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 20, marginBottom: 28 }}>
        <div>
          <div className="eyebrow">{panel.location}</div>
          <h1 className="h-display" style={{ fontSize: 30, margin: "6px 0 4px" }}>
            {panel.panel_id}
          </h1>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 13, color: "var(--text-low)" }}>
            {panel.rated_power}W rated · installed {panel.installation_date}
          </div>
        </div>
        {panel.latest_health_score != null && (
          <HealthGauge score={panel.latest_health_score} status={panel.latest_status} size={140} />
        )}
      </header>

      <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: 20, alignItems: "start" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          <div className="card" style={{ padding: 22 }}>
            <div className="eyebrow" style={{ marginBottom: 12 }}>Degradation forecast</div>
            <DegradationChart history={history} forecast={prediction?.degradation_forecast || []} />
          </div>

          {prediction?.recommendation && (
            <div className="card" style={{ padding: 20, borderLeft: "3px solid var(--gold)" }}>
              <div className="eyebrow" style={{ marginBottom: 8 }}>Recommendation</div>
              <p style={{ fontSize: 14, color: "var(--text-hi)", margin: 0, lineHeight: 1.5 }}>
                {prediction.recommendation}
              </p>
            </div>
          )}

          {lastResult && (
            <div className="card" style={{ padding: 20 }}>
              <div className="eyebrow" style={{ marginBottom: 12 }}>Latest analysis</div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, fontFamily: "var(--font-mono)", fontSize: 13 }}>
                <Metric label="Detected" value={lastResult.detected_defect} />
                <Metric label="Confidence" value={`${lastResult.confidence}%`} />
                <Metric label="Power output" value={`${lastResult.power_output} W`} />
                <Metric label="Power loss" value={`${lastResult.power_loss_pct}%`} />
              </div>
            </div>
          )}
        </div>

        <UploadForm panelId={panelId} onResult={handleResult} />
      </div>

      <section style={{ marginTop: 32 }}>
        <div className="eyebrow" style={{ marginBottom: 12 }}>Inspection log</div>
        <div className="card" style={{ overflow: "hidden" }}>
          {history.length === 0 ? (
            <div style={{ padding: 24, color: "var(--text-low)", fontFamily: "var(--font-mono)", fontSize: 13 }}>
              No inspections recorded yet.
            </div>
          ) : (
            <table style={{ width: "100%", borderCollapse: "collapse", fontFamily: "var(--font-mono)", fontSize: 13 }}>
              <thead>
                <tr style={{ textAlign: "left", color: "var(--text-low)" }}>
                  <Th>Date</Th>
                  <Th>Health</Th>
                  <Th>Status</Th>
                  <Th>Defect</Th>
                  <Th>Confidence</Th>
                </tr>
              </thead>
              <tbody>
                {[...history].reverse().map((row, i) => (
                  <tr key={i} style={{ borderTop: "1px solid var(--border-soft)" }}>
                    <Td>{new Date(row.date).toLocaleString()}</Td>
                    <Td>{row.health_score}</Td>
                    <Td>
                      <span className={`pill pill-${row.status?.toLowerCase()}`}>{row.status}</span>
                    </Td>
                    <Td>{row.detected_defect}</Td>
                    <Td>{row.confidence}%</Td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </section>
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <div>
      <div style={{ color: "var(--text-low)", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.06em" }}>{label}</div>
      <div style={{ color: "var(--text-hi)", marginTop: 2 }}>{value}</div>
    </div>
  );
}

function Th({ children }) {
  return <th style={{ padding: "12px 16px", fontWeight: 500 }}>{children}</th>;
}
function Td({ children }) {
  return <td style={{ padding: "12px 16px", color: "var(--text-hi)" }}>{children}</td>;
}
