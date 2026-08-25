import React from "react";
import { useNavigate } from "react-router-dom";
import HealthGauge from "./HealthGauge.jsx";

export default function PanelCard({ panel }) {
  const navigate = useNavigate();
  const hasData = panel.latest_health_score != null;

  return (
    <div
      className="card"
      onClick={() => navigate(`/panels/${panel.panel_id}`)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && navigate(`/panels/${panel.panel_id}`)}
      style={{
        padding: 20,
        cursor: "pointer",
        display: "flex",
        flexDirection: "column",
        gap: 14,
        transition: "border-color 0.15s ease, transform 0.15s ease",
      }}
      onMouseEnter={(e) => (e.currentTarget.style.borderColor = "var(--text-low)")}
      onMouseLeave={(e) => (e.currentTarget.style.borderColor = "var(--border)")}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <div className="eyebrow">{panel.location}</div>
          <div className="h-display" style={{ fontSize: 20, marginTop: 4 }}>
            {panel.panel_id}
          </div>
          <div style={{ fontSize: 12, color: "var(--text-low)", fontFamily: "var(--font-mono)", marginTop: 4 }}>
            {panel.rated_power}W rated
          </div>
        </div>
        {panel.latest_status && (
          <span
            className={`pill pill-${panel.latest_status.toLowerCase()}`}
          >
            <Dot color={`var(--${panel.latest_status.toLowerCase()})`} />
            {panel.latest_status}
          </span>
        )}
      </div>

      <div style={{ display: "flex", justifyContent: "center", padding: "4px 0" }}>
        {hasData ? (
          <HealthGauge score={panel.latest_health_score} status={panel.latest_status} size={128} />
        ) : (
          <div
            style={{
              width: 128,
              height: 128,
              borderRadius: "50%",
              border: "1px dashed var(--border)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "var(--text-low)",
              fontFamily: "var(--font-mono)",
              fontSize: 12,
              textAlign: "center",
              padding: 12,
            }}
          >
            no inspections yet
          </div>
        )}
      </div>
    </div>
  );
}

function Dot({ color }) {
  return (
    <span
      style={{
        width: 6,
        height: 6,
        borderRadius: "50%",
        background: color,
        display: "inline-block",
      }}
    />
  );
}
