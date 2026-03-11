import React, { useEffect, useState } from "react";
import {
  API_BASE_URL,
  DevicePreset,
  fetchDevicePresets,
  createDevicePreset
} from "../api";

type LayoutOption = "long" | "pivot";
type FormatOption = "csv" | "json";

export const DownloadPage: React.FC = () => {
  // Fixed output: CSV + pivot layout
  const format: FormatOption = "csv";
  const layout: LayoutOption = "pivot";
  const [keys, setKeys] = useState<string>("flow_rate,total_consumption");
  const [deviceIds, setDeviceIds] = useState<string>("");
  const [startDate, setStartDate] = useState<string>("");
  const [endDate, setEndDate] = useState<string>("");
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);
  const [presets, setPresets] = useState<DevicePreset[]>([]);
  const [selectedPresetId, setSelectedPresetId] = useState<number | "">("");
  const [newPresetName, setNewPresetName] = useState<string>("");

  useEffect(() => {
    (async () => {
      try {
        const list = await fetchDevicePresets();
        setPresets(list);
      } catch {
        // ignore; presets are optional
      }
    })();
  }, []);

  const buildUrl = () => {
    const params = new URLSearchParams();
    params.set("format", format);
    params.set("layout", layout);
    if (keys.trim()) params.set("keys", keys.trim());
    if (startDate && endDate) {
      params.set("start_date", startDate);
      params.set("end_date", endDate);
    }

    if (deviceIds.trim()) {
      params.set("device_ids", deviceIds.trim());
    }

    return `${API_BASE_URL}/download/thingsboard?${params.toString()}`;
  };

  const onDownload = async (e: React.FormEvent) => {
    e.preventDefault();
    const url = buildUrl();
    setStatus(`Preparing download…`);
    setError(null);
    setDownloading(true);
    try {
      const resp = await fetch(url);
      if (!resp.ok) {
        const text = await resp.text();
        let message = `Download failed (${resp.status}).`;
        try {
          const json = JSON.parse(text);
          if (json?.detail) {
            message = typeof json.detail === "string" ? json.detail : JSON.stringify(json.detail);
          }
        } catch {
          if (text) message = text;
        }
        setError(message);
        setStatus(null);
        return;
      }
      const blob = await resp.blob();
      const disposition = resp.headers.get("Content-Disposition") || "";
      const match = disposition.match(/filename=\"?([^\";]+)\"?/i);
      const filename = match ? match[1] : (format === "csv" ? "thingsboard_telemetry.csv" : "thingsboard_telemetry.json");

      const link = document.createElement("a");
      link.href = window.URL.createObjectURL(blob);
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      setStatus(`Download started (${filename}).`);
    } catch (e: any) {
      setError(e.message || String(e));
      setStatus(null);
    } finally {
      setDownloading(false);
    }
  };

  const applyPreset = (presetId: number | "") => {
    setSelectedPresetId(presetId);
    if (!presetId) return;
    const preset = presets.find(p => p.id === presetId);
    if (!preset) return;
    setDeviceIds(preset.device_ids.join(","));
    if (preset.keys) {
      setKeys(preset.keys);
    }
  };

  const onSavePreset = async () => {
    setError(null);
    setStatus(null);
    const name = newPresetName.trim();
    if (!name) {
      setError("Please enter a name for the preset.");
      return;
    }
    const ids = deviceIds
      .split(",")
      .map(x => x.trim())
      .filter(Boolean);
    if (ids.length === 0) {
      setError("Please enter at least one device UUID before saving a preset.");
      return;
    }
    try {
      const created = await createDevicePreset({
        name,
        device_ids: ids,
        keys: keys.trim()
      });
      const next = [...presets, created].sort((a, b) =>
        a.name.localeCompare(b.name)
      );
      setPresets(next);
      setSelectedPresetId(created.id);
      setNewPresetName("");
      setStatus(`Preset "${created.name}" saved.`);
    } catch (e: any) {
      setError(e.message || String(e));
    }
  };

  return (
    <div className="page">
      <h2>Download reports</h2>
      <form onSubmit={onDownload} className="download-form">
        <div className="download-cards">
          <section className="card">
            <h3>Time range</h3>
            <label>
              Date range
              <div className="inline">
                <input
                  type="date"
                  value={startDate}
                  onChange={e => setStartDate(e.target.value)}
                />
                <span>to</span>
                <input
                  type="date"
                  value={endDate}
                  onChange={e => setEndDate(e.target.value)}
                />
              </div>
            </label>
          </section>

          <section className="card">
            <h3>Devices & keys</h3>
            <label>
              Preset
              <div className="inline">
                <select
                  value={selectedPresetId}
                  onChange={e =>
                    applyPreset(
                      e.target.value === "" ? "" : Number(e.target.value)
                    )
                  }
                >
                  <option value="">Custom (manual)</option>
                  {presets.map(p => (
                    <option key={p.id} value={p.id}>
                      {p.name}
                    </option>
                  ))}
                </select>
              </div>
            </label>
            <label>
              Device IDs (UUID, comma separated)
              <input
                placeholder="0f32...,43cd..."
                value={deviceIds}
                onChange={e => setDeviceIds(e.target.value)}
              />
            </label>
            <label>
              Keys
              <input
                value={keys}
                onChange={e => setKeys(e.target.value)}
                placeholder="flow_rate,total_consumption"
              />
            </label>
            <label>
              Save as preset
              <div className="inline">
                <input
                  placeholder="Preset name (e.g. Line 1 meters)"
                  value={newPresetName}
                  onChange={e => setNewPresetName(e.target.value)}
                />
                <button
                  type="button"
                  onClick={onSavePreset}
                  disabled={downloading}
                >
                  Save
                </button>
              </div>
            </label>
          </section>

          <section className="card">
            <h3>Format</h3>
            <p style={{ marginBottom: "0.5rem", color: "#64748b" }}>
              <strong>Output format:</strong> CSV
            </p>
            <p style={{ marginBottom: 0, color: "#64748b" }}>
              <strong>CSV layout:</strong> Pivot (columns per meter like spreadsheet)
            </p>
          </section>
        </div>

        <div className="form-footer">
          <button type="submit" disabled={downloading}>
            {downloading ? "Downloading…" : "Download"}
          </button>
          {status && <div className="message info">{status}</div>}
          {error && <div className="message error">{error}</div>}
        </div>
      </form>
    </div>
  );
};

