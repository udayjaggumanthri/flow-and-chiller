### download_func_controller.py

Location: TVCV_stable_Code/controllers/download_Controllers/download_func_controller.py

Purpose:  
Handles automated daily data extraction from Antar IIoT (ThingsBoard backend) and triggers Excel/PDF report generation for each registered TVCV device. This controller runs on a scheduler (invoked by main.py) and downloads one full day of timeseries telemetry for all devices.

Class: download_Class

Static Method: device_Name_From_AntarIIoT(item, token)

- Fetches the device name from Antar IIoT using its device ID.
- Sends a GET request to `/api/device/{item}` with a valid JWT token.
- Returns device name if successful; logs errors otherwise.

Static Method: AntarIIoT_data_check(data, i)

- Utility function to safely extract a `"value"` from a ThingsBoard timeseries entry.
- Returns zero if an index or key is missing.

Static Method: download_function()

Primary scheduler-triggered method responsible for:

1. **Determine yesterday date range**

   - Computes:
     - `startTs → yesterday 00:00:00`
     - `endTs → yesterday 23:59:59`
   - Converts timestamps to UNIX epoch (milliseconds).

2. **Authenticate with Antar IIoT**

   - Sends POST request to `/api/auth/login`
   - Retrieves access token.

3. **Iterate through all device IDs from DeviceManager**

   - For each device:
     - Retrieve device name using `device_Name_From_AntarIIoT()`
     - Build telemetry API request URL using:
       - Keys:  
         `RY_Voltage, YB_Voltage, BR_Voltage, currents, PF, frequency, KW, KWh, RN/YN/BN neutral voltages, status, avg_Current, avg_Voltage, Temperature & Vibration attributes`
       - Date range: StartTS → EndTS
       - interval = 1 day (`interval=86400000`)
       - limit = very high to fetch the entire dataset

4. **Send request to Antar IIoT timeseries API**

   - URL pattern:  
     `/api/plugins/telemetry/DEVICE/{deviceID}/values/timeseries?...`

5. **Process successful responses**

   - Pass the telemetry JSON to:
     - `pdf_Download_Class.pdf_download_function(data, FILE_PATH_PDF, device_name)`
   - Excel export is available in code but currently commented.

6. **Failure handling**
   - Logs HTTP status code when requests fail.

Data Download Details:

- Uses bare telemetry values (agg=NONE)
- Orders results ASC
- No pagination used (limit set extremely high)

Dependencies:

- `DeviceManager.get_device_ids()` → provides all TVCV devices to export.
- `pdf_Download_Class` → generates PDF daily report.
- `excel_Download_Class` → Excel report generator (optional).
- `config.py`:
  - `ANTAR_IIoT_URL`
  - `FILE_PATH_EXCEL`
  - `FILE_PATH_PDF`

Scheduling & Invocation:

- Called from main.py inside the scheduled thread (`excelAndPdf_function`)
- Executes everyday at configured time (e.g., 00:25 AM in main.py)
- Sleep cycles used to avoid repeated execution in the same minute.

Notes:

- This controller fetches a very large dataset (24 hours × all parameters × all devices). Ensure network and API capacity is appropriate.
- Uses tenant-level credentials (`tenant@antariiot.com`) for authentication.
- No retry logic implemented; consider adding for production stability.

### excel_Download_Controller.py

Location: TVCV_stable_Code/controllers/download_Controllers/excel_Download_Controller.py

Purpose:  
Responsible for generating structured Excel reports for each TVCV device based on one full day of telemetry received from Antar IIoT (ThingsBoard).  
This controller extracts timeseries data, converts timestamps, organizes measurements column-wise, and saves them into device-specific Excel files.

Class: excel_Download_Class

Static Method: AntarIIoT_data_check(data, i)

- Safely extracts `"value"` from a ThingsBoard telemetry element.
- Returns:
  - The numeric value if present
  - `0` if the index/key is missing or malformed
- Prevents crashes due to inconsistent telemetry arrays.

Static Method: excel_download_function(data, file_path, device_name)

The main Excel generation workflow.  
This method performs the following activities:

1. **Initialize column lists**

   - Prepares empty arrays for:
     - Voltages (RY, YB, BR, RN, YN, BN)
     - Currents (R, Y, B)
     - Power factors (R, Y, B)
     - Frequency, KW, KWh
     - avg_Voltage, avg_Current
     - Timestamp conversion

2. **Validate data structure**

   - Confirms that `avg_Current` exists in the received telemetry.
   - Logs missing fields for debugging.

3. **Iterate through telemetry data**

   - Uses length of `Frequency` values as the iteration base.
   - Extracts timestamp from each row and converts milliseconds → datetime.
   - Appends values to respective lists using `AntarIIoT_data_check`.

4. **Build final dictionary**

   - Combines all lists into a `finaldata` dict.
   - Converts it into a Pandas DataFrame.

5. **Build directory structure**
   Output folder follows this hierarchy:
   {FILE_PATH_EXCEL}/{YEAR}/{MONTH}/device-{device_name}/

- Automatically creates directories if missing.

6. **Construct final filename**
   Filename syntax: {dd*YYYY_Day_Month*}{device_name}.xlsx

Example:  
`03_2025_Monday_March_device-TVCV1.xlsx`

7. **Export Excel file**

- Writes the DataFrame using `df.to_excel(output_path, index=False)`
- Prints confirmation on successful file creation.

Data Extracted Per Row:

- TimeStamp
- RY_Voltage, YB_Voltage, BR_Voltage
- R/Y/B_Phase_line_Current
- R/Y/B_power_factor
- Frequency
- Total_KW_wrt_line
- Total_KWh_wrt_line
- RN/YN/BN_Voltage
- Avg_Current, Avg_Voltage

Dependencies:

- pandas → DataFrame creation & Excel export.
- datetime → timestamp conversion & path formatting.
- os → directory creation.
- AntarIIoT_data_check → telemetry field extraction.
- Config constants:
- `FILE_PATH_EXCEL`
- Device name supplied from download_func_controller.

Notes:

- Temperature and vibration attributes are present in code but currently commented out.
- The function expects clean and aligned time-series arrays. If misaligned, output files may contain NaN values.
- All generated reports are device-specific and organized by date for long-term archival.



### pdf_Download_Controller.py

**Location:** `TVCV_stable_Code/controllers/download_Controllers/pdf_Download_Controller.py`

---

## Purpose
Generates human-readable PDF reports from one full day of telemetry for each TVCV device.  
This module formats timeseries telemetry into a landscape PDF table, includes a header logo, and stores files in a date-organized folder structure.

---

## Key Responsibilities
- Convert raw telemetry timeseries into row-wise table entries.
- Format multi-field cells (e.g., combined line voltages) for compact PDF presentation.
- Add header/logo and simple styling for readability.
- Create device- and date-specific directories and save PDF files.
- Handle missing fields gracefully and substitute placeholder values where needed.

---

## Class: `pdf_Download_Class`

### Static method: `data_formator_3(data1, data2, data3)`
- Purpose: Concatenate three values into a single string with separators.
- Returns: `f"{data1}: {data2}: {data3}"`

### Static method: `data_formator_2(data1, data2)`
- Purpose: Concatenate two values into a single string with a separator.
- Returns: `f"{data1}: {data2}"`

### Static method: `AntarIIoT_data_check(data, i)`
- Purpose: Safely extract numeric value from a ThingsBoard timeseries `data[i]["value"]`.
- Returns: numeric value or `0` on missing/invalid entries.

### Static method: `AntarIIOT_String_Data_Check(data, i)`
- Purpose: Safely extract string-like value from timeseries `data[i]["value"]`.
- Returns: value or `"NAN"` on missing/invalid entries.

### Static method: `pdf_download_function(data, file_path_pdf, device_name)`
**Purpose:** Main routine to build and save the PDF for the given telemetry `data`.

**Processing Flow**
1. **Table header initialization**
   - Builds `final_data` list with a single header row containing compact column titles:
     - TimeStamp
     - RY_Voltage / YB_Voltage / BR_Voltage
     - Phase currents (R / Y / B)
     - Power factors (Rph / Yph / Bph)
     - Frequency
     - KW / KWh
     - RN/YN/BN voltages
     - Status
     - Surface Temperature
     - X_RMS_Vel / Z_RMS_Vel

2. **Iterate telemetry rows**
   - Uses `len(data["Frequency"])` as iteration base (assumes frequency is always present).
   - For each index `i`:
     - Convert `ts` milliseconds → human timestamp string.
     - Compose combined multi-field strings using `data_formator_3` or `data_formator_2`.
     - Use `AntarIIoT_data_check` to safely read numeric fields.
     - Use `AntarIIOT_String_Data_Check` for `status` string values.
     - Append a populated `pdf_data` row to `final_data`.

3. **Filesystem preparation**
   - Compute `year` and `month` strings.
   - Build `final_path = {file_path_pdf}\{year}\{month}\device-{device_name}`.
   - Create directories if missing.

4. **File naming**
   - Use `yesterday` date and format: `dd_YYYY_AAA_BBB_{device_name}.pdf` where:
     - `dd` → day
     - `YYYY` → year
     - `AAA` → weekday
     - `BBB` → month name
   - Example filename: `03_2025_Monday_March_Chiller-1.pdf`

5. **PDF composition**
   - Uses ReportLab `SimpleDocTemplate` (landscape letter).
   - Adds company logo (from `assets/reddy_icon.png` via `icon_path`).
   - Builds a `Table` from `final_data`.
   - Applies `TableStyle`:
     - Header background (cornflower blue)
     - Header text color (white)
     - Row background (pastel blue)
     - Grid lines and center alignment
   - Adds table to document `elements` and `doc.build(elements)` to save PDF.

6. **Completion**
   - Prints confirmation: `PDF data1 created successfully.`

---

## Workflow / Data Flow
```
Telemetry JSON (timeseries) →
  iterate indexes →
    read fields safely →
    format combined cells →
    append rows to final_data →
  create PDF with ReportLab →
  save under {file_path_pdf}/{YEAR}/{MONTH}/device-{device_name}/
```

---

## Dependencies
- `reportlab` (platypus, colors, pagesizes, units) — PDF creation and styling.
- `datetime`, `os` — timestamp conversion and file system operations.
- `config` (indirect) — `FILE_PATH_PDF` passed in by caller.
- Local assets: `assets/reddy_icon.png` — company logo.
- The module computes `icon_path` relative to the project root for reliable logo loading.

---

## Error Handling & Robustness
- Uses `try/except` patterns within `AntarIIoT_data_check` and `AntarIIOT_String_Data_Check` to avoid crashes on missing indexes or malformed payload arrays.
- If `data` is falsy or empty, the function will skip PDF creation (no rows appended).
- Directory creation uses `os.makedirs(final_path)` guarded by `if not os.path.exists(final_path)`.

---

## Notes & Recommendations
- The implementation assumes the `Frequency` timeseries defines the canonical row count. If telemetry arrays are misaligned (different lengths), consider normalizing data prior to PDF generation.
- `icon_path` resolves relative to the package root — confirm `assets/reddy_icon.png` exists and path is correct when deploying.
- Consider adding pagination or row-limiting for very large datasets to avoid oversized PDFs.
- Replace `print()` with Python `logging` for production observability.
- If required, add document metadata (title, author) or a cover page with device details and date-range summary.

---

## Example invocation
```python
from controllers.download_Controllers.pdf_Download_Controller import pdf_Download_Class

# assuming `data` is the telemetry JSON returned from the ThingsBoard timeseries API:
pdf_Download_Class.pdf_download_function(data, FILE_PATH_PDF, device_name="Chiller-4A")
```
