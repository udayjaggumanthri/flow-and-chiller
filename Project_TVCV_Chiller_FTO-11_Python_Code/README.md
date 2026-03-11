TVCV_CODE Project

This repository contains a modular Python application organized into several controller-based components.

---

## PROJECT STRUCTURE

TVCV_stable_CODE
│
├── assets
│ └── reddy_icon.png
│
├── controllers
│ ├── access_Controllers
│ │ └── access_Controller.py
│ │
│ ├── Alarm_Controllers
│ │ ├── alarm_Status_Controller.py
│ │ ├── create_Alarm_Controller.py
│ │ └── get_Existing_Controller.py
│ │
│ ├── data_Check_Controllers
│ │ ├── data_push_controller.py
│ │ └── data_Seperation_controller.py
│ │
│ ├── device_Name_Controllers
│ │ └── device_Name_Controller.py
│ │
│ ├── download_controllers
│ │ ├── download_func_caller.py
│ │ ├── excel_Download_Controller.py
│ │ └── pdf_Download_Controller.py
│ │
│ ├── mail_Controllers
│ │ └── mail_Controller.py
│ │
│ └── mqtt_Controllers
│ ├── mqtt_Controller.py
│ └── mqtt_Data_Dump_Controller.py
│
├── device_Details
│ └── device_details_Controller.py
│
├── Thresholds
│ └── Thresholds_controller.py
│
├── config.py
└── main_Code.py

---

## FOLDER DESCRIPTIONS

assets → Static files like images/icons
controllers → All modular controllers grouped by functionality
device_Details → Device metadata and device configuration logic
Thresholds → Threshold validation and processing logic
config.py → Main configuration setup
main_Code.py → Entry point to run the full project

### main_Code.py

Location: TVCV_stable_Code/main_Code.py

Purpose:
Application entry point. Starts background threads to:

- run the MQTT listener (connect to broker and handle incoming messages),
- execute a time-based scheduler that triggers daily downloads (PDF/Excel) from the ANTAR IIoT backend.

Behavior & responsibilities:

- Imports configuration constants from `config.py`:
  - `BROKER_IP`, `BROKER_PORT`, `BROKER_USERNAME`, `BROKER_PASSWORD`, `BROKER_TOPIC`, `ANTAR_IIoT_URL`
- Uses `MQTTController` (controllers/mqtt_Controllers/mqtt_Controller.py) to connect and continuously listen on the configured `BROKER_TOPIC`.
- Runs `download_Class.download_function()` once per day when local time equals `"00:25"` (HH:MM). The scheduler checks time every 30 seconds and pauses 60 seconds after a download trigger to avoid duplicate runs.
- Optionally can refresh `ACCESS_TOKEN` periodically using `access_Token.access_Token_Generator()`; the token-refresh thread is present but currently commented out. When enabled, the token-refresh loop updates the module-level `ACCESS_TOKEN` every 840 seconds (14 minutes).

Threads:

- `mqtt_Function()` — creates `MQTTController(broker, port, username, password, topic, ACCESS_TOKEN)` and calls `connect_and_listen()`. Delays 1 second at start.
- `excelAndPdf_function()` — infinite loop, checks current time every 30 seconds; triggers `download_Class.download_function()` at `00:25`.
- `access_Token_Generator_Caller()` — (present but disabled in main) updates `ACCESS_TOKEN` periodically by calling `access_Token.access_Token_Generator()`.

Notes & considerations:

- `ACCESS_TOKEN` starts as `None`. If the MQTTController or downstream requests require a valid token at connect time, consider enabling the token thread or adapt the controller to fetch/refresh tokens on demand.
- The download schedule uses local system time; ensure host time and timezone are correct.
- `download_Class.download_function()` performs network requests and file I/O — running it on the same thread as MQTT would block message handling; the current design runs downloads in a separate thread to avoid blocking.
- The token-refresh thread is intentionally commented out. If you enable it, ensure any code that depends on `ACCESS_TOKEN` handles token updates safely (race conditions).
- All threads run indefinitely; the process must be stopped manually or wrapped with graceful shutdown handling for production.

### config.py

Location: TVCV_stable_Code/config.py

Purpose:
Central configuration file containing all environment-level constants used across the project, including:

- ANTAR IIoT backend URLs
- MQTT broker credentials
- File-path locations for Excel/PDF exports
- Buzzer controller topic
- Email SMTP configuration for alert notifications

This module is imported across controllers to maintain a single source of truth for runtime settings.

Configuration Sections:

1. ANTAR IIoT Backend URLs

- `ANTAR_IIoT_URL`  
  Main backend endpoint used for device metadata, telemetry push, alarm queries, and authentication.
- `ANTAR_IIoT_IP_URL`  
  Optional alternate backend endpoint (local/internal network).
- `MQTT_CLIENT`  
  Default `None`; can be used to store a shared MQTT client instance if required.

2. File Paths for Generated Reports

- `FILE_PATH_EXCEL`  
  Root directory where Excel reports (Temperature, Vibration, Current, Voltage) will be stored.
- `FILE_PATH_PDF`  
  Root directory for generated PDF reports.

3. MQTT Broker Configuration

- `BROKER_IP`  
  MQTT broker host IP.
- `BROKER_HOST`  
  Localhost reference (not used in main flow but retained for flexibility).
- `BROKER_PORT`  
  MQTT broker port, default 1883.
- `BROKER_USERNAME`, `BROKER_PASSWORD`  
  Credentials to authenticate with the broker.
- `BROKER_TOPIC`  
  Topic the application subscribes to for receiving device telemetry.

4. Buzzer Controller

- `BUZZER_ID`  
  MQTT topic/identifier used by buzzer_Controller.py to trigger buzzer ON/OFF instructions.

5. Email (SMTP) Alert Configuration

- `SMTP_SERVER`, `SMTP_PORT`  
  Outgoing mail server configuration.
- `USERNAME`, `PASSWORD`  
  Sender email account (password should ideally be stored securely outside the repo).
- `FROM_EMAIL`  
  Email displayed as the sender.
- `TO_EMAILS`  
  Primary alert recipients.
- `CC_EMAILS`  
  CC recipients for alert escalation.
- `SUBJECT`  
  Default subject line for alert emails.

Notes:

- Credentials (MQTT, SMTP, ANTAR IIoT) are hardcoded here for deployment convenience. For production use, move them to environment variables or an encrypted secrets vault.
- File paths must exist or be creatable by download controllers; ensure directory permissions allow file creation.
- `BROKER_TOPIC` determines which payload stream the MQTT listener receives; update when monitoring new devices.

---

## HOW TO RUN

python main_Code.py

---

## NOTES

- Controllers are separated for clean, modular, and scalable development.
- Easy to add new modules without affecting the existing system.

```

```
