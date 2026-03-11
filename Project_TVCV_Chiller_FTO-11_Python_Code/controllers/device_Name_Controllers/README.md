### device_Name_Controller.py

Location: TVCV_Demo_Code/controllers/device_Name_Controllers/device_Name_Controller.py

Purpose:
Provides a simple utility for retrieving the human-readable device name from the ANTAR IIoT backend (ThingsBoard API).  
This controller is typically used when generating reports (Excel/PDF) or logs that require device names rather than internal UUIDs.

Class: device_Name_Class

Static Method: device_Name_From_Thingsboard(item, token)

- Accepts:
  - item → Device ID (UUID)
  - token → Valid ThingsBoard Bearer token
- Builds API URL:
  {ANTAR_IIoT_URL}/api/device/{item}
- Sends GET request with header:
  "X-Authorization": "Bearer <token>"
- On success (HTTP 200):
  - Parses JSON response and returns `data["name"]`.
- On failure:
  - Prints an error message including the HTTP status code.

Usage:

- Used inside data download controllers to convert device IDs into readable device names.
- Helps maintain user-friendly naming in files, logs, and dashboard outputs.

Notes:

- Imports ANTAR_IIoT_URL dynamically inside the method to avoid circular import issues.
- Method includes basic error handling; for production, consider raising exceptions or implementing structured logging.
