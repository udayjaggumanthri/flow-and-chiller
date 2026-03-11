# Scripts to API (Antar IoT)

This repository contains a complete local setup for:

- A **FastAPI backend** that ingests MQTT data, optionally pushes telemetry to ThingsBoard, and generates downloadable reports.
- A **React (Vite) frontend** UI for Download reports, Daily consumption, Device presets, and Settings.
- A legacy/alternate Python project folder (`Project_TVCV_Chiller_FTO-11_Python_Code/`) kept in the repo.

If you are new to the repo, start here.

---

## Repository layout

- `backend_apis/`: FastAPI backend (MQTT + ThingsBoard + reports)
- `frontend/`: React UI (Vite + TypeScript)
- `Project_TVCV_Chiller_FTO-11_Python_Code/`: additional Python codebase (separate from FastAPI backend)

Each folder has its own documentation:
- Backend details: `backend_apis/README.md`

---

## Quick start (Windows)

You will run **two** processes in two terminals:

- Backend: `http://127.0.0.1:8000`
- Frontend: `http://localhost:5173`

### 1) Backend setup & run

```powershell
cd "g:\scripts_to_api\backend_apis"
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Create your env file (safe template provided)
copy example.env .env

# Start the API
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Verify:
- Health: `GET` `http://127.0.0.1:8000/health`
- Swagger: `http://127.0.0.1:8000/docs`

### 2) Frontend setup & run

```powershell
cd "g:\scripts_to_api\frontend"
npm install
npm run dev
```

The UI will call the backend at `http://127.0.0.1:8000` by default.

If your backend runs on a different URL/port, set:
- `frontend/.env.local` with `VITE_API_BASE_URL=http://127.0.0.1:8000`

---

## What the system does (high level)

### MQTT ingestion (backend)

The backend subscribes to `MQTT_TOPIC_PATTERN` and parses incoming messages into a normalized in-memory snapshot (`/latest-data`).

### ThingsBoard integration

Two modes:

- **Push (realtime)**: when enabled, incoming MQTT data is pushed to ThingsBoard automatically.
- **Download (reports)**: credentials + device UUIDs are used to download timeseries for CSV reports.

### Reports

- **Daily consumption** computes per device/day usage from ThingsBoard timeseries using:
  - \(daily = last\_value\_in\_day - first\_value\_in\_day\)
- CSV output includes sample start/end timestamps and values.
- User-facing CSV times are output in **IST (UTC+05:30)** using a fixed offset (works on Windows without `tzdata`).

---

## Configuration overview

### Backend `.env`

Backend config is in `backend_apis/.env`. A safe template exists at `backend_apis/example.env`.

Important variables:
- **MQTT**: `MQTT_HOST`, `MQTT_PORT`, `MQTT_TOPIC_PATTERN`
- **ThingsBoard base URL**: `THINGSBOARD_BASE_URL`
- **Download credentials**: `THINGSBOARD_USERNAME`, `THINGSBOARD_PASSWORD`
- **Device UUIDs for reports/download**: `THINGSBOARD_DEVICE_ID` or `THINGSBOARD_DEVICE_IDS`
- **Settings PIN (optional)**: `SETTINGS_PIN=1234`

Note:
- Backend loads `backend_apis/.env` automatically at startup (via `python-dotenv`).
- Settings stored in Postgres (from the UI) can override env values.

### Frontend API base URL

- Default backend URL: `http://127.0.0.1:8000`
- Override with `frontend/.env.local`:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

---

## UI pages (frontend)

- **Download reports** (`/download`): download CSV reports
- **Daily consumption** (`/daily`): view daily consumption table + download daily report CSV
- **Device presets** (`/presets`): save device ID + key presets
- **Settings** (`/settings`): configure backend settings (can be PIN-protected)

---

## Common troubleshooting

### Backend: “ModuleNotFoundError: fastapi”

Activate the venv and install deps:

```powershell
cd "g:\scripts_to_api\backend_apis"
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Frontend cannot reach backend

- Ensure backend is running at `http://127.0.0.1:8000`
- Or set `frontend/.env.local` with `VITE_API_BASE_URL=...`, then restart the frontend dev server.

### Settings PIN not prompting

- Set `SETTINGS_PIN` in `backend_apis/.env`
- Restart backend
- Refresh `/settings` in the browser (PIN is required again after refresh)

---

## More documentation

- Backend deep dive: `backend_apis/README.md`

