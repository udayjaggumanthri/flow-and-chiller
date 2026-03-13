const DEFAULT_BASE_URL = "http://127.0.0.1:8000";

export const API_BASE_URL =
  (import.meta as any).env?.VITE_API_BASE_URL || DEFAULT_BASE_URL;

async function handleJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(
      `Request failed with ${response.status}: ${text || response.statusText}`
    );
  }
  return (await response.json()) as T;
}

export type MqttSettings = {
  host: string;
  port: number;
  username: string | null;
  password: string | null;
  client_id_prefix: string;
  keepalive: number;
  topic_pattern: string;
  qos: number;
};

export type TelemetrySettings = {
  base_url: string | null;
  enable_push: boolean;
  enable_auto_push: boolean;
  timeout_seconds: number;
  device_token: string | null;
  token_from_topic_regex: string | null;
  one_device_per_meter: boolean;
  push_interval_seconds: number;
  inactivity_minutes: number;
  inactivity_check_interval_seconds: number;
  inactivity_timeout_seconds: number;
};

export type ThingsBoardDownloadSettings = {
  base_url: string | null;
  username: string | null;
  password: string | null;
  device_id: string | null;
  device_ids: string[];
  timeout_seconds: number;
};

export type SettingsPayload = {
  mqtt: MqttSettings;
  telemetry: TelemetrySettings;
  thingsboard_download: ThingsBoardDownloadSettings;
};

export type DevicePreset = {
  id: number;
  name: string;
  device_ids: string[];
  keys: string;
};

export type DailyConsumptionRow = {
  device_id: string;
  device_name: string;
  date: string;
  key: string;
  start_ts_iso?: string | null;
  end_ts_iso?: string | null;
  start_ts?: number | null;
  end_ts?: number | null;
  start_value?: number | null;
  end_value?: number | null;
  daily_consumption?: number | null;
  points: number;
  missing: boolean;
  reset_detected: boolean;
};

/**
 * Settings PIN is intentionally NOT persisted.
 * Requirement: after a browser refresh, user must enter PIN again.
 */
export function isSettingsUnlocked(): boolean {
  return false;
}

export function setSettingsUnlocked(_unlocked: boolean): void {
  // no-op (do not persist)
}

export async function verifySettingsPin(pin: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/settings/verify-pin`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pin: pin || "" })
  });
  if (res.status === 401) {
    const data = await res.json().catch(() => ({}));
    throw new Error((data as { detail?: string }).detail || "Invalid PIN");
  }
  await handleJson(res);
}

export async function fetchSettings(): Promise<SettingsPayload> {
  const res = await fetch(`${API_BASE_URL}/settings`);
  return handleJson<SettingsPayload>(res);
}

export async function saveSettings(payload: SettingsPayload): Promise<SettingsPayload> {
  const res = await fetch(`${API_BASE_URL}/settings`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });
  return handleJson<SettingsPayload>(res);
}

export async function fetchDevicePresets(): Promise<DevicePreset[]> {
  const res = await fetch(`${API_BASE_URL}/device-presets`);
  return handleJson<DevicePreset[]>(res);
}

export async function createDevicePreset(
  preset: { name: string; device_ids: string[]; keys: string }
): Promise<DevicePreset> {
  const res = await fetch(`${API_BASE_URL}/device-presets`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(preset)
  });
  return handleJson<DevicePreset>(res);
}

export async function deleteDevicePreset(id: number): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/device-presets/${id}`, {
    method: "DELETE"
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(
      `Failed to delete preset (${res.status}): ${text || res.statusText}`
    );
  }
}

export async function fetchDailyConsumption(params: {
  date: string;
  preset_id?: number;
  device_ids?: string;
  key?: string;
  start_iso?: string;
  end_iso?: string;
}): Promise<DailyConsumptionRow[]> {
  const qs = new URLSearchParams();
  qs.set("date", params.date);
  if (params.preset_id !== undefined) qs.set("preset_id", String(params.preset_id));
  if (params.device_ids) qs.set("device_ids", params.device_ids);
  if (params.key) qs.set("key", params.key);
  if (params.start_iso) qs.set("start_iso", params.start_iso);
  if (params.end_iso) qs.set("end_iso", params.end_iso);
  const res = await fetch(`${API_BASE_URL}/reports/daily-consumption?${qs.toString()}`);
  return handleJson<DailyConsumptionRow[]>(res);
}

