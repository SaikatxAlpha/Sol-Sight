import React from "react";

const STATUS_COLOR = {
  Healthy: "var(--healthy)",
  Warning: "var(--warning)",
  Critical: "var(--critical)",
};

/**
 * A 270° arc gauge styled like a sunrise sweep — the needle-less instrument
 * this dashboard is built around. Size is intentionally generous so it can
 * anchor a card as the hero number.
 */
export default function HealthGauge({ score = 0, status = "Healthy", size = 168 }) {
  const clamped = Math.max(0, Math.min(100, score));
  const color = STATUS_COLOR[status] || "var(--text-mid)";

  const radius = (size - 20) / 2;
  const circumference = 2 * Math.PI * radius;
  const arcFraction = 0.75; // 270° of the circle is the visible track
  const trackLength = circumference * arcFraction;
  const progress = trackLength * (clamped / 100);
  const rotation = 135; // start angle so the gap sits at the bottom

  return (
    <div
      style={{ width: size, height: size, position: "relative" }}
      role="img"
      aria-label={`Health score ${clamped} percent, status ${status}`}
    >
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--border)"
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={`${trackLength} ${circumference}`}
          transform={`rotate(${rotation} ${size / 2} ${size / 2})`}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={`${progress} ${circumference}`}
          transform={`rotate(${rotation} ${size / 2} ${size / 2})`}
          style={{
            filter: `drop-shadow(0 0 8px ${color})`,
            transition: "stroke-dasharray 0.6s cubic-bezier(.3,.9,.3,1)",
          }}
        />
      </svg>
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <span
          className="h-display"
          style={{ fontSize: size * 0.26, lineHeight: 1, color: "var(--text-hi)" }}
        >
          {Math.round(clamped)}
        </span>
        <span
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: 11,
            letterSpacing: "0.08em",
            color,
            marginTop: 6,
            textTransform: "uppercase",
          }}
        >
          {status}
        </span>
      </div>
    </div>
  );
}
