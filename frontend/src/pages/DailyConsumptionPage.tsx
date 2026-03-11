import React, { useEffect, useMemo, useState } from "react";
import {
  API_BASE_URL,
  DailyConsumptionRow,
  DevicePreset,
  fetchDailyConsumption,
  fetchDevicePresets
} from "../api";

function formatTime(iso?: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  // Show actual sample time as HH:MM:SS in IST (Asia/Kolkata)
  return d.toLocaleTimeString("en-IN", {
    hour12: false,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    timeZone: "Asia/Kolkata"
  });
}

function formatNumber(v?: number | null): string {
  if (v === null || v === undefined) return "";
  return v.toFixed(2);
}

export const DailyConsumptionPage: React.FC = () => {
  const today = useMemo(() => {
    const d = new Date();
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    return `${yyyy}-${mm}-${dd}`;
  }, []);

  const [rows, setRows] = useState<DailyConsumptionRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [presets, setPresets] = useState<DevicePreset[]>([]);
  const [selectedPresetId, setSelectedPresetId] = useState<number | "">("");
  const [deviceIds, setDeviceIds] = useState<string>("");
  const [rangeStart, setRangeStart] = useState<string>(today);
  const [rangeEnd, setRangeEnd] = useState<string>(today);
  const [dlStatus, setDlStatus] = useState<string | null>(null);
  const [dlError, setDlError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await fetchDailyConsumption({ date: today });
      setRows(data);
      setError(null);
    } catch (e: any) {
      setError(e.message || String(e));
    } finally {
      setLoading(false);
    }
  };

  // Automatically load today's daily consumption for all configured devices
  // once when the page is opened.
  useEffect(() => {
    void loadData();
  }, [today]);

  useEffect(() => {
    (async () => {
      try {
        const list = await fetchDevicePresets();
        setPresets(list);
      } catch {
        // optional
      }
    })();
  }, []);

  const applyPreset = (presetId: number | "") => {
    setSelectedPresetId(presetId);
    if (!presetId) return;
    const preset = presets.find(p => p.id === presetId);
    if (!preset) return;
    setDeviceIds(preset.device_ids.join(","));
  };

  const buildCsvUrl = () => {
    const params = new URLSearchParams();
    params.set("start_date", rangeStart);
    params.set("end_date", rangeEnd);
    if (selectedPresetId !== "") {
      params.set("preset_id", String(selectedPresetId));
    }
    if (deviceIds.trim()) {
      params.set("device_ids", deviceIds.trim());
    }
    // key left default (total_consumption)
    return `${API_BASE_URL}/reports/daily-consumption-csv?${params.toString()}`;
  };

  const onDownloadCsv = async () => {
    setDlError(null);
    setDlStatus(null);
    if (!rangeStart || !rangeEnd) {
      setDlError("Please select a start and end date.");
      return;
    }
    try {
      setDownloading(true);
      const url = buildCsvUrl();
      const resp = await fetch(url);
      if (!resp.ok) {
        const text = await resp.text();
        setDlError(
          text || `Download failed with status ${resp.status}.`
        );
        return;
      }
      const blob = await resp.blob();
      const disposition = resp.headers.get("Content-Disposition") || "";
      const match = disposition.match(/filename=\"?([^\";]+)\"?/i);
      const filename =
        match?.[1] ||
        `daily_consumption_${rangeStart}_to_${rangeEnd}.csv`;
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      setDlStatus(`Download started (${filename}).`);
    } catch (e: any) {
      setDlError(e.message || String(e));
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="page">
      <h2>Daily consumption</h2>
      <section className="card" style={{ maxWidth: 960, marginBottom: "1.5rem" }}>
        <h3>Download daily report (CSV)</h3>
        <div className="form-grid" style={{ gridTemplateColumns: "1fr 1.3fr" }}>
          <div>
            <label>
              Date range
              <div className="inline">
                <input
                  type="date"
                  value={rangeStart}
                  onChange={e => setRangeStart(e.target.value)}
                />
                <span>to</span>
                <input
                  type="date"
                  value={rangeEnd}
                  onChange={e => setRangeEnd(e.target.value)}
                />
              </div>
            </label>
          </div>
          <div>
            <label>
              Preset (optional)
              <select
                value={selectedPresetId}
                onChange={e =>
                  applyPreset(
                    e.target.value === "" ? "" : Number(e.target.value)
                  )
                }
              >
                <option value="">All devices (from Settings)</option>
                {presets.map(p => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Device IDs (optional, comma separated UUIDs)
              <input
                value={deviceIds}
                onChange={e => setDeviceIds(e.target.value)}
                placeholder="0f32...,43cd..."
              />
            </label>
          </div>
        </div>
        <div className="form-footer" style={{ paddingTop: 0 }}>
          <button type="button" onClick={onDownloadCsv} disabled={downloading}>
            {downloading ? "Preparing CSV…" : "Download CSV"}
          </button>
          {dlStatus && <div className="message info">{dlStatus}</div>}
          {dlError && <div className="message error">{dlError}</div>}
        </div>
      </section>

      <section className="card" style={{ maxWidth: 960 }}>
        <h3>Daily consumption (all devices)</h3>
        <p style={{ marginBottom: "1rem", color: "#64748b" }}>
          Automatically showing daily consumption for <strong>{today}</strong> (UTC) for
          all devices configured in Settings.
        </p>

        {loading && <div className="message info">Loading daily consumption…</div>}
        {error && <div className="message error">{error}</div>}

        {!loading && !error && rows.length === 0 && (
          <div>No results yet. Check Settings &gt; ThingsBoard download device IDs.</div>
        )}

        {!loading && !error && rows.length > 0 && (
          <table className="table">
            <thead>
              <tr>
                <th>Meter</th>
                <th>Date</th>
                <th>Start time</th>
                <th>Start value</th>
                <th>End time</th>
                <th>End value</th>
                <th>Daily</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map(r => (
                <tr key={r.device_id}>
                  <td>{r.device_name}</td>
                  <td>{r.date}</td>
                  <td>{formatTime(r.start_ts_iso)}</td>
                  <td>{formatNumber(r.start_value)}</td>
                  <td>{formatTime(r.end_ts_iso)}</td>
                  <td>{formatNumber(r.end_value)}</td>
                  <td>{formatNumber(r.daily_consumption)}</td>
                  <td>{r.missing ? "Missing" : r.reset_detected ? "Reset" : "OK"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
};

