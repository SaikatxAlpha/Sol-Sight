import React from "react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div
      style={{
        background: "var(--bg-raised)",
        border: "1px solid var(--border)",
        borderRadius: 10,
        padding: "8px 12px",
        fontFamily: "var(--font-mono)",
        fontSize: 12,
      }}
    >
      <div style={{ color: "var(--text-low)" }}>{label}</div>
      <div style={{ color: "var(--gold)", fontWeight: 600 }}>
        {payload[0].value}% health
      </div>
    </div>
  );
}

/**
 * history: [{ date, health_score }]
 * forecast: [{ day, predicted_health }]  (day = +N from today, e.g. 30/60/90)
 */
export default function DegradationChart({ history = [], forecast = [] }) {
  const historyPoints = history.map((h) => ({
    label: new Date(h.date).toLocaleDateString(undefined, { month: "short", day: "numeric" }),
    actual: h.health_score,
  }));

  const forecastPoints = forecast.map((f) => ({
    label: `+${f.day}d`,
    projected: f.predicted_health,
  }));

  const bridge =
    historyPoints.length > 0
      ? [{ ...historyPoints[historyPoints.length - 1], projected: historyPoints[historyPoints.length - 1].actual }]
      : [];

  const data = [...historyPoints, ...bridge, ...forecastPoints];

  return (
    <div style={{ width: "100%", height: 220 }}>
      <ResponsiveContainer>
        <AreaChart data={data} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
          <defs>
            <linearGradient id="actualFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--gold)" stopOpacity={0.35} />
              <stop offset="100%" stopColor="var(--gold)" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="projectedFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--violet)" stopOpacity={0.3} />
              <stop offset="100%" stopColor="var(--violet)" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="var(--border-soft)" vertical={false} />
          <XAxis
            dataKey="label"
            tick={{ fill: "var(--text-low)", fontSize: 11, fontFamily: "var(--font-mono)" }}
            axisLine={{ stroke: "var(--border)" }}
            tickLine={false}
          />
          <YAxis
            domain={[0, 100]}
            tick={{ fill: "var(--text-low)", fontSize: 11, fontFamily: "var(--font-mono)" }}
            axisLine={false}
            tickLine={false}
            width={34}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area
            type="monotone"
            dataKey="actual"
            stroke="var(--gold)"
            strokeWidth={2}
            fill="url(#actualFill)"
            connectNulls
          />
          <Area
            type="monotone"
            dataKey="projected"
            stroke="var(--violet)"
            strokeWidth={2}
            strokeDasharray="5 4"
            fill="url(#projectedFill)"
            connectNulls
          />
        </AreaChart>
      </ResponsiveContainer>
      <div style={{ display: "flex", gap: 16, marginTop: 4, justifyContent: "center" }}>
        <Legend swatch="var(--gold)" label="Recorded" />
        <Legend swatch="var(--violet)" label="Forecast" dashed />
      </div>
    </div>
  );
}

function Legend({ swatch, label, dashed }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
      <span
        style={{
          width: 14,
          height: 2,
          background: dashed
            ? `repeating-linear-gradient(90deg, ${swatch} 0 4px, transparent 4px 7px)`
            : swatch,
          display: "inline-block",
        }}
      />
      <span style={{ fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--text-low)" }}>
        {label}
      </span>
    </div>
  );
}
