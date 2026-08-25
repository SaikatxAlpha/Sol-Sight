import React, { useState, useRef } from "react";
import { predictDefect } from "../../api/client.js";

export default function UploadForm({ panelId, onResult }) {
  const [voltage, setVoltage] = useState("");
  const [current, setCurrent] = useState("");
  const [temperature, setTemperature] = useState("");
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const fileRef = useRef(null);

  function handleFile(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setImage(file);
    setPreview(URL.createObjectURL(file));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const result = await predictDefect({
        panelId,
        voltage: parseFloat(voltage),
        current: parseFloat(current),
        temperature: parseFloat(temperature),
        image,
      });
      onResult?.(result);
      setVoltage("");
      setCurrent("");
      setTemperature("");
      setImage(null);
      setPreview(null);
      if (fileRef.current) fileRef.current.value = "";
    } catch (err) {
      setError(err.message || "Analysis failed. Try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="card" style={{ padding: 24, display: "flex", flexDirection: "column", gap: 18 }}>
      <div>
        <div className="eyebrow">New reading</div>
        <div className="h-display" style={{ fontSize: 18, marginTop: 4 }}>
          Run an inspection
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
        <div>
          <label className="label">Voltage (V)</label>
          <input
            className="input"
            type="number"
            step="0.01"
            required
            value={voltage}
            onChange={(e) => setVoltage(e.target.value)}
            placeholder="32.40"
          />
        </div>
        <div>
          <label className="label">Current (A)</label>
          <input
            className="input"
            type="number"
            step="0.01"
            required
            value={current}
            onChange={(e) => setCurrent(e.target.value)}
            placeholder="8.10"
          />
        </div>
        <div>
          <label className="label">Temp (°C)</label>
          <input
            className="input"
            type="number"
            step="0.1"
            required
            value={temperature}
            onChange={(e) => setTemperature(e.target.value)}
            placeholder="41.5"
          />
        </div>
      </div>

      <div>
        <label className="label">Panel image (optional — thermal or visual)</label>
        <div
          onClick={() => fileRef.current?.click()}
          style={{
            border: "1px dashed var(--border)",
            borderRadius: "var(--radius-sm)",
            padding: preview ? 0 : 24,
            textAlign: "center",
            cursor: "pointer",
            overflow: "hidden",
            background: "var(--bg-raised)",
          }}
        >
          {preview ? (
            <img src={preview} alt="Selected inspection" style={{ width: "100%", maxHeight: 180, objectFit: "cover", display: "block" }} />
          ) : (
            <span style={{ color: "var(--text-low)", fontFamily: "var(--font-mono)", fontSize: 13 }}>
              tap to attach an image
            </span>
          )}
        </div>
        <input ref={fileRef} type="file" accept="image/*" onChange={handleFile} hidden />
      </div>

      {error && (
        <div style={{ color: "var(--critical)", fontSize: 13, fontFamily: "var(--font-mono)" }}>{error}</div>
      )}

      <button type="submit" className="btn btn-primary" disabled={loading}>
        {loading ? "Analyzing…" : "Analyze panel"}
      </button>
    </form>
  );
}
