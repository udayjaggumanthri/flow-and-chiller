# MQTT Gateway API (Backend)

This folder contains the FastAPI backend that:

- Subscribes to MQTT topics and keeps a **latest snapshot** per gateway/meter
- (Optional) Pushes telemetry to ThingsBoard/Antar IoT (push mode)
- Downloads historical telemetry from ThingsBoard to generate **reports** (download mode)
- Stores editable configuration in Postgres (**Settings**) and supports **Device Presets**

---

## Project structure

High-level layout (enterprise-friendly):

- `app/main.py`: FastAPI app entrypoint (routers + startup/shutdown)
- `app/api/v1/api.py`: API router aggregator (includes all routers)
- `app/core/settings.py`: canonical settings loader (DB-first, then `.env`)
- `app/core/logging.py`: logging config
- `app/routers/`: HTTP endpoints (download, reports, settings, presets)
- `app/services/`: ThingsBoard clients/formatters + MQTT payload parsing
- `app/mqtt/`: MQTT client lifecycle + snapshot storage
- `app/models/`: Pydantic schemas + SQLAlchemy models
- `app/db.py`: SQLAlchemy engine/session (used by settings + presets)

Compatibility note:
- `app/config.py` remains as a **shim** that re-exports `get_settings()` and settings models from `app/core/settings.py` so older imports keep working.

---

## Requirements

- **Python**: 3.11 / 3.12 / 3.13 (recommended).  
  (`requirements.txt` warns that 3.14 may fail building `pydantic-core`.)
- **Postgres**: required for Settings + Device Presets persistence.

Install dependencies:

```bash
cd backend_apis
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## Database setup on a new system

The React frontend does not have its own database; it uses the **Postgres database configured for the backend**.  
On any new machine, follow these steps once to create the required tables.

### 1. Create the Postgres database

In Postgres (psql / pgAdmin), create the database that matches your `.env` / defaults:

- `DB_NAME = tb_setup_db`
- `DB_USER = postgres`
- `DB_PASSWORD = postgres`
- `DB_HOST = localhost`
- `DB_PORT = 5432`

Example with `psql`:

```bash
createdb tb_setup_db
```

### 2. Configure connection in `.env`

In `backend_apis/.env` on the new machine, make sure these values match your Postgres instance:

```env
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
DB_NAME=tb_setup_db
```

### 3. Install dependencies and create tables

From **PowerShell**:

```powershell
cd "g:\scripts_to_api\backend_apis"
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# ONE-TIME ONLY: create all tables in the configured database
python -c "from app.db import Base, engine; import app.models.db_models; Base.metadata.create_all(bind=engine)"
```

This last command:

- Uses the DB settings from `.env` (or defaults in `app/db.py`).
- Imports all SQLAlchemy models in `app/models/db_models.py`.
- Calls `Base.metadata.create_all(bind=engine)` to create the `system_settings` and `device_presets` tables (and any future models) in Postgres.

After this, you can run the backend normally.

---

## Configuration (`.env`)

Backend reads configuration in this priority order:

1. **Postgres `system_settings` row** (Settings page writes here)
2. Otherwise falls back to **environment variables** from `.env`

Your `.env` file is at `backend_apis/.env`.

`.env` loading:
- `app/main.py` loads `backend_apis/.env` automatically at startup using **python-dotenv** (see `requirements.txt`).
- If you deploy with environment variables already set (Docker/K8s/CI), those still work; `.env` is just a convenience for local dev.

### Postgres connection

Set these if your Postgres isn’t using defaults:

- `DB_USER` (default: `postgres`)
- `DB_PASSWORD` (default: `postgres`)
- `DB_HOST` (default: `localhost`)
- `DB_PORT` (default: `5432`)
- `DB_NAME` (default: `tb_setup_db`)

### MQTT

- `MQTT_HOST`
- `MQTT_PORT`
- `MQTT_USERNAME` (optional)
- `MQTT_PASSWORD` (optional)
- `MQTT_CLIENT_ID_PREFIX`
- `MQTT_KEEPALIVE`
- `MQTT_TOPIC_PATTERN` (supports wildcards; e.g. `FM/#`)
- `MQTT_QOS`

### ThingsBoard / Antar IoT (Push)

- `THINGSBOARD_BASE_URL`
- `ENABLE_TELEMETRY_PUSH` (`true/false`)
- `ENABLE_AUTO_TELEMETRY_PUSH` (`true/false`)
- `TELEMETRY_TIMEOUT_SECONDS`
- `ONE_DEVICE_PER_METER` (`true/false`)
- `TELEMETRY_PUSH_INTERVAL_SECONDS` (0 = only push when MQTT arrives)

Realtime “Inactive” support:
- `TELEMETRY_INACTIVITY_TIMEOUT_SECONDS` (e.g. `60`)

### ThingsBoard (Download / Reports)

These are used for downloading telemetry for reports:

- `THINGSBOARD_USERNAME`
- `THINGSBOARD_PASSWORD`
- `THINGSBOARD_DEVICE_ID` (single UUID) OR
- `THINGSBOARD_DEVICE_IDS` (comma-separated UUIDs)
- `THINGSBOARD_DOWNLOAD_TIMEOUT_SECONDS`

### Settings page PIN (optional)

To require a PIN before the UI can access `/settings`:

- `SETTINGS_PIN=1234`

If `SETTINGS_PIN` is empty/not set, Settings access is allowed without a PIN.

---

## How to run

Activate your venv, then run:

```bash
cd backend_apis
venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

---

## How it works (runtime behavior)

### Startup

On startup (`app/main.py`):

- Logging is configured (level from `APP_LOG_LEVEL`)
- MQTT client starts and begins tracking latest gateway snapshots
- If `TELEMETRY_INACTIVITY_TIMEOUT_SECONDS > 0`, backend can set ThingsBoard device inactivity timeout (uses download credentials + device UUIDs)
- Optional periodic push loop may start if enabled and interval > 0

### MQTT snapshot

MQTT ingestion keeps the latest parsed `GatewayData` in memory.

Endpoints like `/latest-data` and the download router can access that snapshot.

### Reports (daily consumption)

Daily consumption is computed from ThingsBoard timeseries:

- For each device and day:  
  **daily = last_value_in_day - first_value_in_day**
- CSV download includes:
  - start/end sample timestamps and values
  - daily consumption
  - status flags (missing/reset)

Timezone behavior:
- UI-facing CSV times are output in **IST (UTC+05:30)** using a fixed offset to work on Windows without `tzdata`.

### Device presets

Device presets live in Postgres and contain:
- `name`
- `device_ids` (comma-separated UUIDs)
- `keys` (telemetry key list)

Presets are used by reports and download screens to quickly pick devices/keys.

---

## API overview (most used endpoints)

### System

- `GET /health` → `{ "status": "ok" }`
- `GET /latest-data` → latest MQTT snapshot

### Settings

- `GET /settings` → current settings payload (DB row or env fallback)
- `PUT /settings` → upsert settings payload (writes DB + clears settings cache)
- `POST /settings/verify-pin` → verifies Settings PIN (401 if invalid)

### Device presets

- `GET /device-presets`
- `POST /device-presets`
- `DELETE /device-presets/{id}`

### Reports

- `GET /reports/daily-consumption?date=YYYY-MM-DD&key=total_consumption`
- `GET /reports/daily-consumption-csv?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD...`

### Download

- `GET /download/thingsboard?...` (downloads telemetry and returns CSV)

---

## Troubleshooting

### “ModuleNotFoundError: fastapi”

You’re not in the correct venv (or dependencies aren’t installed). Run:

```bash
cd backend_apis
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Windows timezone errors (tzdata / ZoneInfo)

This project uses a fixed IST offset (UTC+05:30) for report CSV timestamps to avoid `ZoneInfoNotFoundError` on Windows. No extra packages are required for timezone conversion.

### Postgres connection errors

Verify `DB_*` env vars and that Postgres is reachable. Settings/presets require DB access.

---

## Development notes

- The API router aggregation lives at `app/api/v1/api.py`.
- `app/config.py` is intentionally kept as a shim so older imports do not break.

