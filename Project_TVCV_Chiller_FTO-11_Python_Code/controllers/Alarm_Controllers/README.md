### alarm_Status_Controller.py

Location: TVCV_Demo_Code/controllers/Alarm_Controllers/alarm_Status_Controller.py

Purpose:
Queries the ANTAR IIoT backend (ThingsBoard) to determine the number of ACTIVE alarms for a device within the current day (00:00:00–23:59:59).  
This controller is typically used by telemetry-processing modules to enrich outgoing payloads or notifications with daily alarm counts.

Class: alarm_Status_Class

Static Method: alarm_status_function(token)

- Accepts:
  - token → Device token used to locate the device ID and authenticate telemetry.
- Responsibilities:
  1. Build daily time window:
     - start_date = today's midnight
     - end_date = today's 23:59:59
     - Converted to epoch timestamps via parameter_Class.epoch_time_function.
  2. Obtain a valid Bearer Access Token:
     - Sends POST request to:
       {ANTAR_IIoT_URL}/api/auth/login
     - Credentials: username = tenant@antariiot.com, password = tenant
  3. Fetch device ID via:
     DeviceManager.get_device_id_by_token(token)
  4. Query active alarms:
     GET {ANTAR_IIoT_URL}/api/alarm/DEVICE/{deviceID}
     ?searchStatus=ACTIVE
     &pageSize=30
     &page=30
     &sortProperty=status
     &sortOrder=ASC
     &startTime={start_ts}
     &endTime={end_ts}
  5. Parse response:
     - Extracts "totalElements" which reflects number of active alarms today.
     - Returns total (0 when none).

Behavior:

- If token authentication fails, prints “Token generation failed.”
- If the alarm query succeeds, captures and returns the active alarm count.
- If no active alarms exist, returns 0.

Dependencies:

- parameter_Class.epoch_time_function → Converts human timestamp strings to epoch.
- DeviceManager → Resolves device UUID from token string.
- requests / json → For API communication.
- ANTAR_IIoT_URL → Backend endpoint base URL.

Notes:

- Authentication is performed on every call; consider caching tokens for efficiency.
- API pagination parameters (pageSize=30, page=30) are static—update if expecting larger volumes.
- Method simply returns total alarm count; consumers can add logic for severity, classification, or message formatting.
- This method is often used when building enriched telemetry or triggering notification workflows.

### alarm_Status_Controller.py

Location: TVCV_Demo_Code/controllers/Alarm_Controllers/alarm_Status_Controller.py

Purpose:
Queries the ANTAR IIoT backend (ThingsBoard) to determine the number of ACTIVE alarms for a device within the current day (00:00:00–23:59:59).  
This controller is typically used by telemetry-processing modules to enrich outgoing payloads or notifications with daily alarm counts.

Class: alarm_Status_Class

Static Method: alarm_status_function(token)

- Accepts:
  - token → Device token used to locate the device ID and authenticate telemetry.
- Responsibilities:
  1. Build daily time window:
     - start_date = today's midnight
     - end_date = today's 23:59:59
     - Converted to epoch timestamps via parameter_Class.epoch_time_function.
  2. Obtain a valid Bearer Access Token:
     - Sends POST request to:
       {ANTAR_IIoT_URL}/api/auth/login
     - Credentials: username = tenant@antariiot.com, password = tenant
  3. Fetch device ID via:
     DeviceManager.get_device_id_by_token(token)
  4. Query active alarms:
     GET {ANTAR_IIoT_URL}/api/alarm/DEVICE/{deviceID}
     ?searchStatus=ACTIVE
     &pageSize=30
     &page=30
     &sortProperty=status
     &sortOrder=ASC
     &startTime={start_ts}
     &endTime={end_ts}
  5. Parse response:
     - Extracts "totalElements" which reflects number of active alarms today.
     - Returns total (0 when none).

Behavior:

- If token authentication fails, prints “Token generation failed.”
- If the alarm query succeeds, captures and returns the active alarm count.
- If no active alarms exist, returns 0.

Dependencies:

- parameter_Class.epoch_time_function → Converts human timestamp strings to epoch.
- DeviceManager → Resolves device UUID from token string.
- requests / json → For API communication.
- ANTAR_IIoT_URL → Backend endpoint base URL.

Notes:

- Authentication is performed on every call; consider caching tokens for efficiency.
- API pagination parameters (pageSize=30, page=30) are static—update if expecting larger volumes.
- Method simply returns total alarm count; consumers can add logic for severity, classification, or message formatting.
- This method is often used when building enriched telemetry or triggering notification workflows.

### get_existing_Controller.py

Location: TVCV_Demo_Code/controllers/Alarm_Controllers/get_Existing_Controller.py

Purpose:
Checks whether an ACTIVE_UNACK alarm of type **"CBM Demo Alarm"** already exists for a specific device within the current day.  
This controller prevents duplicate alarm creation by verifying existing alarms before new alarms are triggered.

Class: get_Alarm_Class

Static Method: get_existing_alarm(ACCESS_TOKEN, deviceID)

Inputs:

- ACCESS_TOKEN → JWT Bearer token for authenticated API access.
- deviceID → UUID of the device whose alarms must be checked.

Responsibilities & Flow:

1. Build Daily Time Window:

   - today_date = current date
   - start_date = "<today> 00:00:00"
   - end_date = "<today> 23:59:59"
   - Convert these timestamps using:
     parameter_Class.epoch_time_function()

2. Build Authentication Header:
   {
   "Content-Type": "application/json",
   "X-Authorization": f"Bearer {ACCESS_TOKEN}"
   }
3. Construct Alarm Query URL:
   GET {ANTAR_IIoT_URL}/api/alarms
   ?entityId={deviceID}
   &entityType=DEVICE
   &pageSize=10
   &page=0
   &sortProperty=startTs
   &sortOrder=DESC
   &startTs={start_ts}
   &endTs={end_ts}
   &searchStatus=ACTIVE

4. Process API Response:

- On HTTP 200:
  - Extract `alarms = response.json().get("data", [])`
  - Iterate through alarms to check whether:
    - originator.id matches deviceID
    - alarm["type"] == "CBM Demo Alarm"
    - alarm["status"] == "ACTIVE_UNACK"
- If a matching alarm exists:
  - Print debug logs
  - Return the alarm object
- If none are found:
  - Return None

5. Return Value:
   Returns:

- Alarm object → if a matching active, unacknowledged alarm already exists
- None → if no duplicate alarm exists for the day

Dependencies:

- parameter_Class.epoch_time_function → timestamp conversion
- ANTAR_IIoT_URL → IIoT backend base URL
- Python dependencies: datetime, requests, json, time

Notes:

- Time window ensures alarms are checked only for the current day.
- Method prevents duplicate alarms by ensuring uniqueness of:
  deviceID + alarmType + ACTIVE_UNACK status
- Throttles loop with time.sleep(1) before returning None (minor delay for backend pacing).
- Extend alarm matching logic if more alarm types need evaluation in future versions.

### param_Check_Controller.py

Location: TVCV_Demo_Code/controllers/Alarm_Controllers/param_Check_Controller.py

Purpose:
Validates incoming telemetry against configured thresholds and triggers alarm creation when one or more parameters exceed their thresholds. Contains utilities for timestamp conversion and a parameter-check routine that supports both range-based and multi-severity threshold definitions.

Primary class: parameter_Class

Public methods:

1. epoch_time_function(date)

- Input: `date` string in the format `"YYYY-MM-DD HH:MM:SS"`.
- Behavior:
  - Parses the input string to a `datetime` object.
  - Converts to epoch seconds, appends `"000"` to produce millisecond timestamp (int).
  - Returns the millisecond timestamp (int).
- On parsing error: prints an error message and returns `None`.

2. parameterCheckFuction(deviceID, data, token, ACCESS_TOKEN_1, client)

- Purpose:

  - Parses telemetry JSON and compares each parameter to the device-specific thresholds defined in `THRESHOLDS`.
  - Collects exceeded parameters and prepares a concise alarm message.
  - Calls `create_Alarm_Class.create_thingsboard_alarm()` when any thresholds are breached.

- Inputs:

  - `deviceID` → Device UUID (string).
  - `data` → JSON string payload (telemetry) that will be `json.loads`-ed inside the method.
  - `token` → Device token used to lookup thresholds in `THRESHOLDS`.
  - `ACCESS_TOKEN_1` → Authorization token forwarded to the alarm creation routine.
  - `client` → MQTT client instance (passed on to alarm creation).

- Threshold evaluation logic:

  - Retrieves `device_thresholds = THRESHOLDS.get(token)`. If not found, logs and returns.
  - Iterates over each `param, value` in the parsed telemetry.
  - If the threshold for a parameter is a dictionary (multi-severity):
    - Evaluates severities in order `["critical", "major", "minor"]` (most severe first).
    - For each severity:
      - If threshold value is a tuple `(min, max)`: counts as a range — a breach occurs when `value` is not within `[min, max]`.
      - If threshold value is numeric: counts as an upper-bound breach when `value > threshold`.
      - On first matching severity breach, records the parameter with its alert level and stops further checks for that parameter.
  - If the threshold is a tuple at the top level (flat range): a breach is reported when `value` falls outside the range.
  - If the threshold is a single numeric value at the top level: a breach is reported when `value > threshold`.
  - Each exceeded parameter is appended to `exceeded_params` with:
    - `Parameter`, `Value`, `Alert` (severity), and `Threshold` (textual representation).

- Alarm creation:
  - If `exceeded_params` is non-empty, builds a human-readable `alarm_message` combining all exceeded parameter entries.
  - Calls:
    `create_Alarm_Class.create_thingsboard_alarm(ACCESS_TOKEN_1, deviceID, alarm_message, data, token, client)`
    to create the alarm in ThingsBoard / ANTAR IIoT.

Dependencies:

- `Thresholds.Thresholds_controller.THRESHOLDS` — device-specific threshold definitions.
- `device_Details.device_details_Controller.DeviceManager` — (not directly used here but commonly related in alarm flows).
- `create_Alarm_Controller.create_Alarm_Class` — called to create alarms when breaches are detected.
- Standard libs: `datetime`, `json`.

Notes & recommendations:

- Severity order is explicit and intentional: `critical` → `major` → `minor`. The function reports only the highest-severity breach per parameter.
- The method expects `data` to be a JSON string. Callers should ensure payload format or pass a pre-parsed dictionary (you can adapt the function accordingly).
- Currently the function prints messages to stdout. Replace prints with structured logging for production.
- Consider normalizing numeric conversions (e.g., safely casting `value` to float) and handling missing/`None` values explicitly before comparisons.
- For high-throughput environments, consider queueing alarm creation (async or background worker) instead of calling the ThingsBoard API synchronously inside the checking routine.
