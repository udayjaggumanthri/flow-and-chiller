import React, { useEffect, useState } from "react";
import {
  DevicePreset,
  fetchDevicePresets,
  createDevicePreset,
  deleteDevicePreset
} from "../api";

export const PresetsPage: React.FC = () => {
  const [presets, setPresets] = useState<DevicePreset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const [name, setName] = useState("");
  const [deviceIds, setDeviceIds] = useState("");
  const [keys, setKeys] = useState("flow_rate,total_consumption");

  const loadPresets = async () => {
    setError(null);
    try {
      const list = await fetchDevicePresets();
      setPresets(list);
    } catch (e: any) {
      setError(e.message || String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPresets();
  }, []);

  const onCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    const trimmedName = name.trim();
    if (!trimmedName) {
      setError("Preset name is required.");
      return;
    }
    const ids = deviceIds
      .split(",")
      .map(x => x.trim())
      .filter(Boolean);
    if (ids.length === 0) {
      setError("Enter at least one device UUID.");
      return;
    }
    setSaving(true);
    try {
      const created = await createDevicePreset({
        name: trimmedName,
        device_ids: ids,
        keys: keys.trim()
      });
      setPresets(prev =>
        [...prev, created].sort((a, b) => a.name.localeCompare(b.name))
      );
      setName("");
      setDeviceIds("");
    } catch (e: any) {
      setError(e.message || String(e));
    } finally {
      setSaving(false);
    }
  };

  const onDelete = async (id: number) => {
    setError(null);
    try {
      await deleteDevicePreset(id);
      setPresets(prev => prev.filter(p => p.id !== id));
    } catch (e: any) {
      setError(e.message || String(e));
    }
  };

  return (
    <div className="page">
      <h2>Device presets</h2>
      <form className="form-grid" onSubmit={onCreate}>
        <section className="card">
          <h3>Create preset</h3>
          <label>
            Name
            <input
              placeholder="e.g. Line 1 meters"
              value={name}
              onChange={e => setName(e.target.value)}
            />
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
            />
          </label>
          <div className="form-footer">
            <button type="submit" disabled={saving}>
              {saving ? "Saving…" : "Save preset"}
            </button>
            {error && <div className="message error">{error}</div>}
          </div>
        </section>

        <section className="card">
          <h3>Existing presets</h3>
          {loading ? (
            <div>Loading presets…</div>
          ) : presets.length === 0 ? (
            <div>No presets yet. Create one on the left.</div>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Device IDs</th>
                  <th>Keys</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {presets.map(p => (
                  <tr key={p.id}>
                    <td>{p.name}</td>
                    <td>{p.device_ids.join(", ")}</td>
                    <td>{p.keys}</td>
                    <td>
                      <button
                        type="button"
                        onClick={() => onDelete(p.id)}
                        className="link-button"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      </form>
    </div>
  );
};

