### data_push_controller.py

Location: TVCV_Demo_Code/controllers/data_Check_Controllers/data_push_controller.py

Purpose:
Receives validated MQTT payloads and orchestrates pushing structured telemetry to the ANTAR IIoT backend. Responsible for basic payload validation, separation of nested telemetry (via data separation utility), and POSTing the resulting telemetry JSON to the ThingsBoard/ANTAR API. The module also contains utilities for simple time calculations and (commented) on/off state tracking.

Primary class: data_push_class

Global state (module-level)

- last_time, last_state, Total_on_time, Total_off_time, last_off_time_update, timestamp_dict  
  These variables exist to support on/off uptime tracking logic (mostly commented) and are preserved for potential future use.

Static methods

1. contains_none(obj)

- Recursively checks an object (dict/list) for any `None` values.
- Returns True if any `None` found; otherwise False.
- Useful for early validation of incoming nested payloads.

2. data_check(data, i)

- Safe accessor for list-style payload entries.
- Returns `data[i]` if present and not `None`, otherwise returns `None`.
- Prints a debug/log line showing the check result.

3. calculate_total_times(x, y)

- Computes elapsed hours between two `datetime` objects.
- Returns absolute difference in hours (float).

4. check_for_CV_TV(token, converted_payload, original_payload, client, ACCESS_TOKEN_1)

- Core entrypoint invoked after an MQTT message is routed to this module.
- Responsibilities & flow:
  1. Resolve deviceID via `DeviceManager.get_device_id_by_token(token)`.
  2. Validate the incoming `converted_payload`:
     - Expects both `"CV"` and `"TV"` keys to exist and to contain non-empty lists.
     - If validation fails, logs "Payload was not in Right formate."
  3. Call `data_Seperation_Class.nested_Data_seperation(converted_payload, token)` to transform incoming raw payload into the nested telemetry structure expected by ANTAR IIoT.
  4. Convert the nested dict to JSON and POST it to:
     {ANTAR_IIoT_URL}/api/v1/{token}/telemetry
     - Uses `requests.post(...)` (no explicit headers — the method sends payload as raw JSON string).
     - On HTTP 200, prints success message with token and deviceID.
     - On non-200, prints failure status code.
     - Exceptions from requests are caught and logged.
  5. (Commented) Hooks for alarm/parameter checking:
     - There are commented calls to `parameter_Class.parameterCheckFuction(...)` and references to `alarm_Status_Class` for future or optional alarm generation and email notification flows.

Notes on behavior & design:

- The function treats the presence of both "CV" and "TV" as the primary acceptance criteria for a valid payload; other branches (single-key handling) exist but are currently commented out.
- The module contains substantial commented logic for tracking ON/OFF state durations and aggregating uptime/offtime metrics — kept for possible future activation.
- `data_Seperation_Class.nested_Data_seperation` is the key transformation point; this module focuses on routing/validation and delegates shape/format conversion to the separation utility.
- The module uses synchronous HTTP requests (`requests`); ensure calling thread/context can tolerate blocking network I/O.

Dependencies:

- requests
- device_Details.device_details_Controller.DeviceManager
- .data_Seperation_controller.data_Seperation_Class
- ..Alarm_Controllers.param_Check_Controller.parameter_Class (currently commented usage)
- ..Alarm_Controllers.alarm_Status_Controller.alarm_Status_Class (imported but not actively used)
- config.ANTAR_IIoT_URL, config.ANTAR_IIoT_IP_URL, config.MQTT_CLIENT

Error handling:

- Wraps the main processing in try/except to log unexpected errors without crashing the MQTT thread.
- Handles network exceptions from `requests` with a specific except for `requests.exceptions.RequestException`.

Operational considerations:

- The POST target expects telemetry for the ThingsBoard-style v1 API (`/api/v1/<token>/telemetry`).
- Ensure `nested_Data_seperation` returns the payload structure expected by the backend (dictionary serializable to JSON).
- If high message throughput is expected, consider making HTTP calls asynchronous or queued to avoid blocking the MQTT listener thread.
- For production use, replace print statements with structured logging and add retry/backoff for transient network failures.

How it integrates:

- Called from `mqtt_Data_Dump_Controller.mqtt_Data_Controller.send_dump()` when a valid MQTT message is received.
- Downstream alarm generation/notification can be triggered after successful push by re-enabling the commented parameter/alarm calls.


### data_Seperation_controller.py

Location: TVCV_Demo_Code/controllers/data_Check_Controllers/data_Seperation_controller.py

Purpose:
Transforms raw MQTT payloads into a structured telemetry dictionary matching the ANTAR IIoT / ThingsBoard v1 API format.  
This module is responsible for extracting values from CV (Current/Voltage) and TV (Temperature/Vibration) arrays, converting units, calculating derived metrics (average line-line voltage, avg current, etc.), and generating a clean, normalized payload ready for POST operations.

Primary Class: data_Seperation_Class

Utility Methods:

1. data_check(data, i)
- Safely extracts data[i] if present; otherwise returns None.
- Prints debug output for tracing.
- Used extensively when pulling values from CV/TV arrays.

2. data_check_float(data, i)
- Same as data_check, but falls back to 0.0 when IndexError occurs.
- Useful when numeric computations depend on presence of values.

3. avg_LL_Voltage_Cal(value1, value2, value3)
- Computes the average of three line-line voltages.
- Returns None when any of the inputs are invalid or <= 0.

4. safe_float(value)
- Attempts to convert a value to float.
- Returns None on failure.
- Used throughout voltage/current/power-factor parsing.

5. nested_Data_seperation(d, token)
- The core transformation function.
- Accepts:
    - d → incoming MQTT payload dictionary
    - token → device token ("Demo", etc.)
- Determines which data path to follow:
    - Combined CV + TV in same payload → primary logic
    - Only TV → fallback TV-only structure
    - Only CV → fallback CV-only structure

Processing Flow (CV + TV Case):
1. Validates presence of non-empty "CV" and "TV" lists.
2. Computes average phase current from CV indices [3,4,5].  
   Determines motor status:
      ≥ 0.5 amps → "ON", otherwise "OFF".
3. Normalizes and maps values into a nested dict including:
    - R/Y/B line voltages
    - Average LL Voltage
    - Phase currents
    - Power factors
    - Frequency
    - Total KW / KWh
    - RN / YN / BN voltages
    - avg_Voltage, avg_Current, avg_Power_Factor
    - Temperature (scaled /100)
    - Vibration RMS values (scaled /1000)
    - status (ON/OFF)
4. Includes additional metadata:
    - "TVCVtopic": token
    - (Commented) Alarm status, on/off duration tracking, timestamps

Processing Flow (TV Only):
- Extracts temperature (scaled /100)
- Extracts X/Z RMS vibration values (scaled /1000)
- Forces:
      status = "OFF"
- Adds:
      Alarm_Status = alarm_Status_Class.alarm_status_function(token)

Processing Flow (CV Only):
- Computes ON/OFF status using currents at indices [3,4,5].
- Maps all CV values as in full CV/TV logic.
- Adds:
      logic: "CV"
      Alarm_Status = alarm_Status_Class.alarm_status_function(token)

Output:
- Returns a fully flattened dictionary ready to be JSON-encoded and POSTed to:
      /api/v1/{token}/telemetry

Dependencies:
- alarm_Status_Class → used for computing Alarm_Status
- Internal helpers (data_check, safe_float, avg_LL_Voltage_Cal)
- Expected payload layout:
    CV list: indices map to RY, YB, BR voltages, currents, PFs, Frequency, KW, KWh, RN/YN/BN voltages, avgVoltage, avgCurrent, avgPowerFactor  
    TV list: indices map to Temperature, RMS vibration, Peak/Acc values (commented)

Notes:
- This module prints debugging logs; replace with structured logging for production.
- Robust against missing or malformed payload values due to safe defaults.
- Any new sensor fields must be added here so they propagate correctly to the telemetry POST payload.
- The design supports full device telemetry normalization before pushing data to IIoT backend.

