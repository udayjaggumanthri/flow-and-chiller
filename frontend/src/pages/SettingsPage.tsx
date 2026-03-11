import React, { useEffect, useState } from "react";
import {
  SettingsPayload,
  fetchSettings,
  saveSettings,
  verifySettingsPin,
  isSettingsUnlocked,
  setSettingsUnlocked,
  TelemetrySettings,
  ThingsBoardDownloadSettings,
  MqttSettings
} from "../api";

export const SettingsPage: React.FC = () => {
  const [unlocked, setUnlocked] = useState(isSettingsUnlocked);
  const [pin, setPin] = useState("");
  const [pinError, setPinError] = useState<string | null>(null);
  const [settings, setSettings] = useState<SettingsPayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // If user is not unlocked, check whether a PIN is actually required.
  // - If backend has NO SETTINGS_PIN configured => verify with empty pin succeeds => auto-unlock.
  // - If backend requires PIN => verify with empty pin returns 401 => show PIN screen.
  useEffect(() => {
    if (unlocked) return;
    (async () => {
      try {
        await verifySettingsPin("");
        setSettingsUnlocked(true);
        setUnlocked(true);
      } catch {
        // PIN required (or backend unavailable). Keep locked and show PIN prompt.
        setSettingsUnlocked(false);
      }
    })();
  }, [unlocked]);

  useEffect(() => {
    if (!unlocked) return;
    setLoading(true);
    (async () => {
      try {
        const data = await fetchSettings();
        setSettings(data);
      } catch (e: any) {
        setError(e.message || String(e));
      } finally {
        setLoading(false);
      }
    })();
  }, [unlocked]);

  const onPinSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setPinError(null);
    try {
      await verifySettingsPin(pin);
      setSettingsUnlocked(true);
      setUnlocked(true);
    } catch (e: any) {
      setPinError(e.message || "Invalid PIN");
    }
  };

  if (!unlocked) {
    return (
      <div className="page">
        <h2>Settings</h2>
        <div className="card pin-gate">
          <p>Enter PIN to access settings.</p>
          <form onSubmit={onPinSubmit}>
            <label>
              PIN
              <input
                type="password"
                inputMode="numeric"
                autoComplete="off"
                placeholder="Enter PIN"
                value={pin}
                onChange={e => setPin(e.target.value)}
              />
            </label>
            {pinError && <div className="message error">{pinError}</div>}
            <div className="form-footer">
              <button type="submit">Continue</button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  const updateMqtt = (patch: Partial<MqttSettings>) => {
    if (!settings) return;
    setSettings({ ...settings, mqtt: { ...settings.mqtt, ...patch } });
  };

  const updateTelemetry = (patch: Partial<TelemetrySettings>) => {
    if (!settings) return;
    setSettings({ ...settings, telemetry: { ...settings.telemetry, ...patch } });
  };

  const updateDownload = (patch: Partial<ThingsBoardDownloadSettings>) => {
    if (!settings) return;
    setSettings({
      ...settings,
      thingsboard_download: { ...settings.thingsboard_download, ...patch }
    });
  };

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!settings) return;
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const saved = await saveSettings(settings);
      setSettings(saved);
      setSuccess("Settings saved.");
    } catch (e: any) {
      setError(e.message || String(e));
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div>Loading settings…</div>;
  }
  if (!settings) {
    return <div>Failed to load settings.</div>;
  }

  const d = settings.thingsboard_download;

  return (
    <div className="page">
      <h2>Settings</h2>
      <form onSubmit={onSubmit} className="form-grid">
        <section className="card">
          <h3>MQTT</h3>
          <label>
            Host
            <input
              value={settings.mqtt.host}
              onChange={e => updateMqtt({ host: e.target.value })}
            />
          </label>
          <label>
            Port
            <input
              type="number"
              value={settings.mqtt.port}
              onChange={e => updateMqtt({ port: Number(e.target.value) })}
            />
          </label>
          <label>
            Username
            <input
              value={settings.mqtt.username ?? ""}
              onChange={e => updateMqtt({ username: e.target.value || null })}
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={settings.mqtt.password ?? ""}
              onChange={e => updateMqtt({ password: e.target.value || null })}
            />
          </label>
          <label>
            Topic pattern
            <input
              value={settings.mqtt.topic_pattern}
              onChange={e => updateMqtt({ topic_pattern: e.target.value })}
            />
          </label>
        </section>

        <section className="card">
          <h3>ThingsBoard push</h3>
          <label>
            Base URL
            <input
              value={settings.telemetry.base_url ?? ""}
              onChange={e => updateTelemetry({ base_url: e.target.value || null })}
            />
          </label>
          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={settings.telemetry.enable_push}
              onChange={e => updateTelemetry({ enable_push: e.target.checked })}
            />
            Enable telemetry push
          </label>
          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={settings.telemetry.enable_auto_push}
              onChange={e => updateTelemetry({ enable_auto_push: e.target.checked })}
            />
            Auto push on MQTT message
          </label>
          <label>
            HTTP timeout (s)
            <input
              type="number"
              step="0.1"
              value={settings.telemetry.timeout_seconds}
              onChange={e =>
                updateTelemetry({ timeout_seconds: Number(e.target.value) })
              }
            />
          </label>
          <label>
            Device token (optional)
            <input
              value={settings.telemetry.device_token ?? ""}
              onChange={e => updateTelemetry({ device_token: e.target.value || null })}
            />
          </label>
          <label>
            Token from topic regex
            <input
              value={settings.telemetry.token_from_topic_regex ?? ""}
              onChange={e =>
                updateTelemetry({ token_from_topic_regex: e.target.value || null })
              }
            />
          </label>
          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={settings.telemetry.one_device_per_meter}
              onChange={e =>
                updateTelemetry({ one_device_per_meter: e.target.checked })
              }
            />
            One device per meter
          </label>
        </section>

        <section className="card">
          <h3>Download / credentials</h3>
          <label>
            ThingsBoard base URL
            <input
              value={d.base_url ?? ""}
              onChange={e => updateDownload({ base_url: e.target.value || null })}
            />
          </label>
          <label>
            Username
            <input
              value={d.username ?? ""}
              onChange={e => updateDownload({ username: e.target.value || null })}
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={d.password ?? ""}
              onChange={e => updateDownload({ password: e.target.value || null })}
            />
          </label>
          <label>
            Single device UUID
            <input
              value={d.device_id ?? ""}
              onChange={e => updateDownload({ device_id: e.target.value || null })}
            />
          </label>
          <label>
            Multiple device UUIDs (comma separated)
            <input
              value={d.device_ids.join(",")}
              onChange={e =>
                updateDownload({
                  device_ids: e.target.value
                    .split(",")
                    .map(x => x.trim())
                    .filter(Boolean)
                })
              }
            />
          </label>
          <label>
            Download timeout (s)
            <input
              type="number"
              step="0.1"
              value={d.timeout_seconds}
              onChange={e =>
                updateDownload({ timeout_seconds: Number(e.target.value) })
              }
            />
          </label>
        </section>

        <div className="form-footer">
          <button type="submit" disabled={saving}>
            {saving ? "Saving…" : "Save settings"}
          </button>
          {error && <div className="message error">{error}</div>}
          {success && <div className="message success">{success}</div>}
        </div>
      </form>
    </div>
  );
};

