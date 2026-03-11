### mail_Controller.py

**Location:** `TVCV_stable_Code/controllers/mail_Controllers/mail_Controller.py`

---

## Purpose
Handles alert email generation and delivery when telemetry parameters exceed configured thresholds.  
It converts incoming telemetry JSON into formatted HTML tables, evaluates parameters against configured limits, and sends a color-coded email alert to configured recipients.

---

## Key Responsibilities
- Parse incoming telemetry JSON and map values to threshold definitions.
- Determine whether any parameter exceeds its threshold(s).
- Build two HTML sections:
  - Temperature & Vibration parameters
  - Current & Voltage parameters
- Format breached values in **red**, normal values in **green**, threshold references in **blue**.
- Send alert emails via SMTP only when at least one breach is detected.
- Log errors for malformed payloads or SMTP failures.

---

## Class: `mail_sender_Class`

### `mailSender(data, token, device_Name)`
Main function responsible for evaluating parameters and sending alert emails.

#### Parameters
- `data` — JSON string of parameter → value mappings.
- `token` — used to lookup threshold rules from `THRESHOLDS`.
- `device_Name` — human-friendly device name to include in the subject and email tables.

#### Core Logic
1. Parse `data` → Python dictionary.
2. Retrieve threshold group:
   ```python
   thresholds = THRESHOLDS.get(token, {})
   ```
3. For each parameter:
   - Skip if no threshold defined.
   - Attempt float conversion; skip non-numeric values.
   - Select threshold priority:
     - `minor` → `major` → `critical`
   - Evaluate:
     - **Tuple threshold:** breach if outside `(min, max)`
     - **Numeric threshold:** breach if `value > threshold`
   - Color code:
     - Red → breach  
     - Green → normal  
   - Build HTML row and append to:
     - `temp_vib_table` or  
     - `curr_volt_table`

4. If **no breach detected**:
   - Suppress email and exit.

5. Construct HTML sections only if rows exist.

6. Build full HTML message:
   - Includes device name
   - Two tables (if populated)
   - Reference dashboard link

7. Use SMTP client:
   - `starttls()`
   - `login(USERNAME, PASSWORD)`
   - Send to `TO_EMAILS + CC_EMAILS`

---

## Dependencies
- `Thresholds.Thresholds_controller.THRESHOLDS`
- Configuration variables from `config.py`:
  - FROM_EMAIL, TO_EMAILS, CC_EMAILS  
  - SUBJECT, SMTP_SERVER, SMTP_PORT  
  - USERNAME, PASSWORD
- Standard Python libraries:
  - `smtplib`, `json`
  - `email.mime.multipart.MIMEMultipart`
  - `email.mime.text.MIMEText`

---

## Workflow Summary
```
Telemetry JSON → Parse → Threshold Evaluation
       ↓
Any breach?
  ↓ Yes                                ↓ No
Build HTML tables                  Suppress email
       ↓
Send SMTP alert
```

---

## Notes & Recommendations
- Non-numeric telemetry values are skipped automatically.
- Email alerts are sent **only when breaches occur**, preventing unnecessary notifications.
- If threshold priority logic should be reversed (critical → major → minor), update selection order.
- SMTP credentials should ideally be moved to environment variables.
- Consider adding a queue or retry mechanism for SMTP failures in production.
- The system logs warnings and exceptions using `print()`; integrate `logging` module for production usage.

---

## Example Invocation
```python
from controllers.mail_Controllers.mail_Controller import mail_sender_Class

sample_payload = '{"Temperature": 55.2, "RN_Voltage": 252}'
mail_sender_Class.mailSender(sample_payload, token="tvcv4", device_Name="Chiller-4A")
```

