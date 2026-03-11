# Postman (Backend API)

This folder contains a ready-to-import Postman collection + environment for the FastAPI backend.

Files:
- `MQTT-Gateway-API.postman_collection.json`
- `MQTT-Gateway-API.postman_environment.json`

---

## Import into Postman

1. Open Postman
2. Import → select:
   - `postman/MQTT-Gateway-API.postman_collection.json`
   - `postman/MQTT-Gateway-API.postman_environment.json`
3. Select the environment **“MQTT Gateway API (Local)”**

Set environment variables:
- `baseUrl`: backend URL (default `http://127.0.0.1:8000`)
- `settingsPin`: PIN for Settings (only if backend `.env` has `SETTINGS_PIN`)
- `tbUsername`, `tbPassword`: ThingsBoard credentials (for download/reports)
- `tbDeviceIdsCsv`: comma-separated ThingsBoard device UUIDs (for report/download requests)
- `startDate`, `endDate`, `reportDate`: report dates in `YYYY-MM-DD`

---

## Typical usage flow

### 1) Verify backend is running

- **System → Health**
- **System → Latest data (snapshot)** (will be empty until MQTT messages arrive)

### 2) (Optional) Verify Settings PIN

If you set `SETTINGS_PIN` in `backend_apis/.env`:
- Set environment variable `settingsPin`
- Call **Settings → Verify settings PIN**
  - 200 = ok
  - 401 = wrong pin

### 3) Configure ThingsBoard download credentials

Reports and ThingsBoard download require credentials and valid device UUIDs.

Options:
- Use the UI Settings page, OR
- Call **Settings → Update settings (PUT)**

Important:
- `thingsboard_download.device_ids` must be real ThingsBoard device UUIDs (Device → Details → Copy ID).
- If you pass request query param `device_ids=...` on report/download endpoints, it overrides settings.

### 4) Device presets

- **Device presets → Create preset**
- **Device presets → List presets**
- **Device presets → Delete preset (by id)**

Presets are used by the UI and can be referenced in report endpoints via `preset_id`.

### 5) Reports (daily consumption)

- **Reports → Daily consumption (JSON)**  
  Query:
  - `date=YYYY-MM-DD`
  - optional `device_ids=<uuid,uuid>` OR optional `preset_id=<id>`
  - `key=total_consumption` (default)

- **Reports → Daily consumption (CSV download)**  
  Query:
  - `start_date=YYYY-MM-DD`
  - `end_date=YYYY-MM-DD`
  - optional `device_ids=<uuid,uuid>` OR optional `preset_id=<id>`
  - `key=total_consumption` (default)

CSV columns:
- `device_name, device_id, date, start_time_ist, end_time_ist, start_value, end_value, daily_consumption, status`

Status values:
- `OK`: normal
- `Missing`: no data points for the day
- `Reset`: meter reset detected (end < start)

### 6) Download (ThingsBoard telemetry)

- **Download → ThingsBoard download (CSV pivot)**  
  Query:
  - `start_date=YYYY-MM-DD`
  - `end_date=YYYY-MM-DD`
  - `keys=flow_rate,total_consumption` (optional)
  - `device_ids=<uuid,uuid>` (optional override)
  - `format=csv`
  - `layout=pivot` (timestamp + per-device columns)

Other useful download endpoints:
- **Download → Latest snapshot (JSON file)**: current in-memory MQTT snapshot as JSON attachment
- **Download → Latest snapshot (CSV file)**: current in-memory MQTT snapshot as CSV attachment

### 7) Telemetry push (manual)

Only works if telemetry push is enabled (`ENABLE_TELEMETRY_PUSH=true` or DB Settings override).

- **Telemetry push → Push latest (all gateways)**: pushes all latest snapshot gateways
- **Telemetry push → Push latest (selected gateway topics)**: pushes only selected topics
- **Telemetry push → Push single gateway (by topic)**: pushes one topic

If there is no MQTT snapshot yet, these may return 404.

---

## Notes / Gotchas

- **Date range semantics** (download endpoints): `start_date` uses start-of-day UTC, `end_date` uses end-of-day UTC.
- **IST in CSV**: daily consumption CSV timestamps are output in IST (UTC+05:30) using a fixed offset for Windows compatibility.
- **Settings persistence**: UI/PUT settings are stored in Postgres and can override `.env`.

