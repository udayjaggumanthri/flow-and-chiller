import smtplib
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from Thresholds.Thresholds_controller import THRESHOLDS
from config import (
    FROM_EMAIL,
    TO_EMAILS,
    CC_EMAILS,
    SUBJECT,
    SMTP_PORT,
    SMTP_SERVER,
    USERNAME,
    PASSWORD,
)


class mail_sender_Class:
    @staticmethod
    def mailSender(data, token,device_Name):
        """
        Sends an alert email if given data exceeds defined thresholds.

        :param data: JSON string of parameter values (e.g., voltages, currents, temperature, etc.)
        :param token: Key to fetch corresponding threshold values from THRESHOLDS
        """

        try:
            # Convert incoming JSON string to dictionary
            array_Data = json.loads(data)

            # Get threshold config for this device/token
            thresholds = THRESHOLDS.get(token, {})
            print("Thresholds:", thresholds)

            # Tables for different parameter categories
            temp_vib_table = ""
            curr_volt_table = ""
            # CRITICAL FIX: Track if any breach occurred
            breach_detected = False

            for param, value in array_Data.items():
                try:
                    # 1. Skip if parameter is not in the threshold config
                    threshold_info = thresholds.get(param)
                    if threshold_info is None:
                        continue

                    # 2. Convert value to float (skip if not possible)
                    try:
                        value = float(value)
                    except Exception:
                        print(f"⚠️ Skipping {param}: value '{value}' is not a number.")
                        continue

                    # 3. Check threshold definition: Prioritize minor > major > critical
                    threshold_key = "minor"
                    if threshold_info.get(threshold_key) is None:
                        threshold_key = "major"
                    if threshold_info.get(threshold_key) is None:
                        threshold_key = "critical"

                    effective_threshold = threshold_info.get(threshold_key)

                    is_breach = False
                    threshold_display = ""

                    if effective_threshold is None:
                        # This happens if none of minor, major, or critical are defined
                        print(
                            f"⚠️ Skipping {param}: no 'minor', 'major', or 'critical' threshold found."
                        )
                        continue

                    # Now check against effective_threshold

                    # Case A: Threshold defined as a tuple (min, max)
                    if (
                        isinstance(effective_threshold, tuple)
                        and len(effective_threshold) == 2
                        and all(m is not None for m in effective_threshold)
                    ):
                        min_val, max_val = effective_threshold
                        is_breach = not (min_val <= value <= max_val)
                        threshold_display = f" {min_val} - {max_val}"

                    # Case B: Threshold is a single number (assuming upper limit check: value > threshold)
                    elif isinstance(effective_threshold, (int, float)):
                        is_breach = value > effective_threshold
                        threshold_display = f"{effective_threshold}"

                    # Case C: Invalid effective threshold value
                    else:
                        print(
                            f"⚠️ Skipping {param}: Effective threshold value is invalid ({effective_threshold})."
                        )
                        continue

                    # Update breach status
                    if is_breach:
                        breach_detected = True

                    # Color-code values for email
                    value_color = "red" if is_breach else "green"
                    threshold_color = "blue"

                    # Build HTML table row
                    row = f"""
                        <tr>
                            <td><b>{param}</b></td>
                            <td style="color:{value_color};"><b>{value:.2f}</b></td>
                            <td style="color:{threshold_color};"><b>{threshold_display}</b></td>
                        </tr>
                    """

                    # Categorize parameters into two sections
                    if param in [
                        "Temperature",
                        "XaxisRMSVelocity",
                        "YaxisRMSVelocity",
                        "ZaxisRMSVelocity",
                        "XaxisHFRMSAcceleration",
                        "YaxisHFRMSAcceleration",
                        "ZaxisHFRMSAcceleration",
                        "Magnitude",
                    ]:
                        temp_vib_table += row
                    else:
                        curr_volt_table += row

                except Exception as inner_e:
                    print(f"❌ Error processing {param}: {inner_e}")
                    continue

            # CRITICAL FIX: Only proceed if a breach was detected
            if not breach_detected:
                print("✅ No thresholds exceeded. Alert email suppressed.")
                return  # Exit the function if no breach detected

            # Build sections if data exists
            temp_vib_section = ""
            curr_volt_section = ""

            # Check if we built any rows before creating the sections
            if temp_vib_table.strip():
                temp_vib_section = f"""
                <h3>🔴 Temperature & Vibration Parameters (Chiller: {device_Name})</h3>
                <table style="width:100%; border: 1px solid black; border-collapse: collapse;">
                    <tr>
                        <th>Parameter</th>
                        <th>Current Value</th>
                        <th>Threshold Limit</th>
                    </tr>
                    {temp_vib_table}
                </table>
                <br>
                """

            if curr_volt_table.strip():
                curr_volt_section = f"""
                <h3>⚡ Current & Voltage Parameters (Chiller: {device_Name})</h3>
                <table style="width:100%; border: 1px solid black; border-collapse: collapse;">
                    <tr >
                        <th>Parameter</th>
                        <th>Current Value</th>
                        <th>Threshold Limit</th>
                    </tr>
                    {curr_volt_table}
                </table>
                <br>
                """

            # Final HTML content
            html_content = f"""
            <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f4;
                }}
                .container {{
                    max-width: 700px;
                    margin: auto;
                    background-color: #ffffff;
                    padding: 20px;
                    border-radius: 5px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                }}
                h2 {{ color: #333; }}
                p {{ color: #555; }}
                .button {{
                    display: inline-block;
                    padding: 10px 20px;
                    background-color: #4CAF50;
                    color: white;
                    text-decoration: none;
                    border-radius: 3px;
                }}
                table, th, td {{
                    border: 1px solid black;
                    border-collapse: collapse;
                    text-align: center;
                    padding: 8px;
                    font-weight: bold;
                }}
                th {{
                    background-color: #f2f2f2;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>CBM Demo Alerts!</h2>
                <p>Dear User,</p>
                <p>Device Parameters have exceeded the set Limit (indicated in <span style="color:red; font-style: italic;">RED</span>).</p>

                {temp_vib_section}

                <br>

                {curr_volt_section}

                <br>
                <a href="http://localhost:8080/alarms" class="button">Visit Dashboard</a>
                <h2 style="color:red">Attention Required!!!</h2>
                <p>Thank you,</p>
            </div>
        </body>
        </html>
            """

            # Prepare and send email
            msg = MIMEMultipart()
            msg["From"] = FROM_EMAIL
            msg["To"] = ", ".join(TO_EMAILS)
            msg["Cc"] = ", ".join(CC_EMAILS)
            msg["Subject"] = SUBJECT + f" - Chiller: {device_Name}"  # Added token to subject
            msg.attach(MIMEText(html_content, "html"))

            try:
                # Use the assigned SMTP_CLASS (Mock or real smtplib)
                with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                    # Uncomment if SMTP requires TLS + login
                    server.starttls()
                    server.login(USERNAME, PASSWORD)

                    # Combine TO and CC lists for sending
                    recipients = TO_EMAILS + CC_EMAILS
                    if not recipients:
                        print(
                            "❌ Failed to send email: No recipients defined in TO_EMAILS or CC_EMAILS."
                        )
                        return

                    server.sendmail(FROM_EMAIL, recipients, msg.as_string())
                print("✅ Email sent successfully (or mock sent if using MockSMTP)!")
            except Exception as smtp_e:
                print(f"❌ Failed to send email via SMTP: {smtp_e}")

        except Exception as outer_e:
            # Catch any top-level issues (bad JSON, etc.)
            print(f"❌ mailSender crashed: {outer_e}")
