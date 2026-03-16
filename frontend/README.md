# Antar IoT UI (Frontend)

This folder contains the React + Vite (TypeScript) web UI for the MQTT Gateway API backend.

---

## Requirements

- Node.js (LTS recommended)
- npm (comes with Node)

---

## Install

```bash
cd frontend
npm install
```

---

## Configure backend URL

By default the UI calls the backend at `http://127.0.0.1:8000`.

To change it, create `frontend/.env.local`:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Restart `npm run dev` after changing env vars.

---

## Run (development)

```bash
cd frontend
npm run dev
```

Open:
- `http://localhost:5173`

To expose the dev server on your local network so other devices on the same Wi‑Fi/LAN can access it:

```bash
cd frontend
npm run dev -- --host 0.0.0.0
```

Then, on this Windows machine, find your local IPv4 address:

```powershell
ipconfig
```

Look under the active network adapter for `IPv4 Address`, e.g. `192.168.0.42`.  
Other devices on the same network can then open:

- `http://192.168.0.42:5173`

---

## Build (production)

```bash
cd frontend
npm run build
```

Preview the production build:

```bash
npm run preview
```

---

## Pages / Routes

The app uses `react-router-dom` and provides these routes:

- `/download` – Download reports
- `/daily` – Daily consumption (table + CSV download)
- `/presets` – Device presets
- `/settings` – Settings (can be PIN-gated by backend `SETTINGS_PIN`)
- `/` redirects to `/download`

---

## Key files

- `src/App.tsx` – routing + page layout
- `src/components/Layout.tsx` – sidebar + navigation
- `src/api.ts` – API client and types (uses `VITE_API_BASE_URL`)
- `src/pages/DownloadPage.tsx`
- `src/pages/DailyConsumptionPage.tsx`
- `src/pages/PresetsPage.tsx`
- `src/pages/SettingsPage.tsx`
- `src/styles.css` – global styling

Static assets:
- `Antar_IoT_Logo.png` – sidebar logo

---

## Troubleshooting

### UI runs but shows API errors

- Ensure backend is running (default: `http://127.0.0.1:8000`)
- Or set `VITE_API_BASE_URL` in `frontend/.env.local`

### Settings PIN prompt

If backend sets `SETTINGS_PIN` in `backend_apis/.env`, the Settings page will prompt for PIN.
After a browser refresh, it will ask again.

