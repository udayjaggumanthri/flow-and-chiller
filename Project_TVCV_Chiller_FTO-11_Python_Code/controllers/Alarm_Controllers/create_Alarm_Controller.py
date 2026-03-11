import time
import requests
from config import ANTAR_IIoT_IP_URL, ANTAR_IIoT_URL
from .get_Existing_Controller import get_Alarm_Class
from ..device_Name_Controllers.device_Name_Controller import device_Name_Class
from ..mail_Controllers.mail_Controller import mail_sender_Class
from ..access_Controllers.access_Controller import access_Token

# from TVCV_main_code import publish_data,publish_data_OFF


class create_Alarm_Class:
    @staticmethod
    def get_severity_from_message(message: str) -> str:
        """
        Determines the severity of the alarm from the message content.
        If any parameter has 'Alert: MAJOR', return 'MAJOR'.
        Else if any has 'Alert: MINOR', return 'MINOR'.
        """
        if "Alert: MAJOR" in message:
            return "MAJOR"
        elif "Alert: MINOR" in message:
            return "MINOR"
        else:
            return "WARNING"  # Default fallback or based on your use case

    @staticmethod
    def create_thingsboard_alarm(ACCESS_TOKEN, deviceID, message, data, token):
        """
        Creates or updates an alarm in ThingsBoard for a given device.
        """
        global TRIGGER
        ACCESS_TOKEN_G = access_Token.access_Token_Generator()
        # print("ACCESS_TOKEN_G", ACCESS_TOKEN_G)
        device_Name = device_Name_Class.device_Name_From_Thingsboard(
            deviceID, ACCESS_TOKEN_G
        )
        alarm_type = "Chiller Monitoring Alarm"  # Use consistent variable
        severity = create_Alarm_Class.get_severity_from_message(
            message
        )  # Set this as needed (dynamic if required)

        existing_alarm = get_Alarm_Class.get_existing_alarm(ACCESS_TOKEN, deviceID)

        # print("Existing_Alarm:", message,severity)

        headers = {
            "Content-Type": "application/json",
            "X-Authorization": f"Bearer {ACCESS_TOKEN_G}",
        }

        alarm_payload = {
            "type": alarm_type,
            "severity": severity,
            "originator": {"id": deviceID, "entityType": "DEVICE"},
            "status": "ACTIVE_UNACK",
            "details": {"Device": device_Name, "message": message},
            "propagate": True,
            "startTs": int(time.time() * 1000),
        }

        url = f"{ANTAR_IIoT_URL}/api/alarm"

        # Check for existing alarm and decide whether to update or create
        if existing_alarm and "id" in existing_alarm:
            print("Updating existing alarm...")
            alarm_id = existing_alarm["id"].get("id")
            if not alarm_id:
                print("Invalid alarm ID format.")
                return

            alarm_payload["id"] = {"id": alarm_id, "entityType": "ALARM"}

            response = requests.post(url, json=alarm_payload, headers=headers)
            action = "updated"
            # mail_sender_Class.mailSender(data,token)
        else:
            print("Creating new alarm...")
            response = requests.post(url, json=alarm_payload, headers=headers)
            action = "created"
            TRIGGER = True  # Optional: used elsewhere?
            try:
                print("data:", data)
                mail_sender_Class.mailSender(data, token,device_Name)
                print("✅ Mail sending process executed successfully.")
            except Exception as e:
                print(f"❌ Error while sending mail: {e}")
            return
        # Response check
        if response.status_code in [200, 201]:
            print(f"Alarm '{alarm_type}' {action} successfully.")
        else:
            print(f" Failed to {action} alarm '{alarm_type}': {response.status_code}")
            print("Response content:", response.text)


# class create_Alarm_Class:
#     def create_thingsboard_alarm(
#         ACCESS_TOKEN, deviceID, message, data
#     ):
#         """
#         Creates an alarm in ThingsBoard for a given device.
#         """
#         global TRIGGER
#         device_Name = device_Name_Class.device_Name_From_Thingsboard(deviceID,ACCESS_TOKEN)

#         alarm_type = "Major Alarm"
#         existing_alarm = get_Alarm_Class.get_existing_alarm(ACCESS_TOKEN, deviceID)
#         print("Existing_Alarm:",existing_alarm,device_Name)

#         headers = {
#             "Content-Type": "application/json",
#             "X-Authorization": f"Bearer {ACCESS_TOKEN}",
#         }

#         alarm_url = f"{ANTAR_IIoT_URL}/api/alarm"


#         # print(deviceID, type, severity, message)
#         if existing_alarm and "id" in existing_alarm:
#             print(existing_alarm["id"])
#             # ✅ Corrected: PUT request with alarm ID
#             alarm_id = existing_alarm["id"]["id"]  # Extract alarm ID
#             payloadU = {
#                 "id": {"id": alarm_id, "entityType": "ALARM"},
#                 "type": type,  # Alarm category (e.g., "Overheat", "Low Battery")
#                 "severity": "MAJOR",  # Alarm severity (CRITICAL, MAJOR, MINOR, WARNING, INDETERMINATE)
#                 "originator": {
#                     "id": deviceID,  # Unique ID of the device that generated the alarm
#                     "entityType": "DEVICE",  # Type of entity (e.g., DEVICE, ASSET, etc.)
#                 },
#                 "status": "ACTIVE_UNACK",  # Initial status of the alarm (unacknowledged and active)
#                 "details": {
#                     "sensor": device_Name,  # Name of the sensor that triggered the alarm
#                     "message": message,  # Description of the alarm

#                     # "threshold": 80,  # Threshold value for the alarm condition
#                     # "current_value": 85,  # Current sensor value that caused the alarm
#                 },
#                 "propagate": True,  # If True, the alarm is passed to higher-level entities (e.g., customer, tenant)
#                 "startTs": int(time.time() * 1000),  # Current timestamp in milliseconds
#             }

#             update_url = f"{ANTAR_IIoT_URL}/api/alarm"
#             response = requests.post(update_url, json=payloadU, headers=headers)
#             action = "updated"
#             # mailSender(data)
#         else:
#             # ✅ Corrected: POST request for new alarms
#             print("Creating New Alarm:")
#             payloadC = {
#             "type": type,  # Alarm category (e.g., "Overheat", "Low Battery")
#             "severity": "MAJOR",  # Alarm severity (CRITICAL, MAJOR, MINOR, WARNING, INDETERMINATE)
#             "originator": {
#                 "id": deviceID,  # Unique ID of the device that generated the alarm
#                 "entityType": "DEVICE",  # Type of entity (e.g., DEVICE, ASSET, etc.)
#             },
#             "status": "ACTIVE_UNACK",  # Initial status of the alarm (unacknowledged and active)
#             "details": {
#                 "Device": device_Name,  # Name of the sensor that triggered the alarm
#                 "message": message,  # Description of the alarm

#                 # "threshold": 80,  # Threshold value for the alarm condition
#                 # "current_value": 85,  # Current sensor value that caused the alarm
#             },
#             "propagate": True,  # If True, the alarm is passed to higher-level entities (e.g., customer, tenant)
#             "startTs": int(time.time() * 1000),  # Current timestamp in milliseconds
#         }
#             alarm_url = f"{ANTAR_IIoT_URL}/api/alarm"
#             response = requests.post(alarm_url, json=payloadC, headers=headers)
#             # data_to_publish = {"ID": "2XN6B4474", "CT": "PORTS", "portA": 1}
#             action = "created"
#             TRIGGER = True
#             # publish_data(client)
#             # time.sleep(10)
#             # publish_data_OFF(client)

#         if response.status_code in [200, 201]:
#             print(f"Alarm '{alarm_type}' {action} successfully!")
#         else:
#             print(f"Failed to {action} alarm '{alarm_type}': {response.content}")
