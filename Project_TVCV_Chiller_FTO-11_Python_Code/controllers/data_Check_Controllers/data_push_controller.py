import datetime
import requests
import json
from device_Details.device_details_Controller import DeviceManager
from .data_Seperation_controller import data_Seperation_Class
from ..Alarm_Controllers.param_Check_Controller import parameter_Class

# from controllers.data_Check_Controllers.data_Seperation_controller import nested_Data_seperation
# from ..Access_controller import accessTokenGenerator
from config import ANTAR_IIoT_URL, ANTAR_IIoT_IP_URL, MQTT_CLIENT

last_time = 0
last_state = "OFF"
Total_on_time = 0
# Total_on_time = f"2024-02-19 15:00:58.984775"
Total_off_time = 0
last_off_time_update = datetime.datetime.now()
timestamp_dict = {}


class data_push_class:

    @staticmethod
    def contains_none(obj):
        if obj is None:
            return True
        if isinstance(obj, dict):
            return any(data_push_class.contains_none(v) for v in obj.values())
        if isinstance(obj, list):
            return any(data_push_class.contains_none(i) for i in obj)
        return False

    @staticmethod
    # Callback function to check the data in valid data or not
    def data_check(data, i):

        if data[i] is not None:
            try:
                return data[i]
            except IndexError:
                return None
        else:
            return None

    @staticmethod
    def calculate_total_times(x, y):
        # print("total no.of seconds elapsed: {}".format(abs(x - y).total_seconds()))
        return abs(x - y).total_seconds() / 3600

    @staticmethod
    def check_for_CV_TV(
        token, converted_payload, original_payload, client, ACCESS_TOKEN_1
    ):
        # print("check_for_CV_TV:",token,converted_payload)
        now = datetime.datetime.now()
        global last_state, last_off_time_update, last_time, Total_off_time, Total_on_time, timestamp_dict, t_on, t_off
        deviceID = DeviceManager.get_device_id_by_token(token)
        # try:
        # if data_push_class.contains_none(converted_payload):
        #     print("Null (None) found in payload.")
        # else:
        # print("No null (None) in payload.")
        if (
            "CV" in converted_payload
            and isinstance(converted_payload["CV"], list)
            and len(converted_payload["CV"]) > 0
            and "TV" in converted_payload
            and isinstance(converted_payload["TV"], list)
            and len(converted_payload["TV"]) > 0
        ):
            print("Both TV and CV")
            # if (
            #     (float(data_push_class.data_check(converted_payload["CV"], 3))
            #     + float(data_push_class.data_check(converted_payload["CV"], 4))
            #     + float(data_push_class.data_check(converted_payload["CV"], 5)))/3
            # ) >= 1:
            #     statement = "ON"
            #     t_on = datetime.datetime.now()
            # else:
            #     statement = "OFF"
            #     t_off = datetime.datetime.now()

            # if last_state == "ON" and statement == "ON":
            #     print(
            #         "if condition:",
            #         last_time == 0,
            #         format(Total_on_time + data_push_class.calculate_total_times(last_time, t_on)),
            #     )
            #     if last_time == 0:
            #         last_time = t_on
            #     else:
            #         Total_on_time = Total_on_time + data_push_class.calculate_total_times(
            #             last_time, t_on
            #         )
            #     last_state = "ON"
            #     timestamp_dict["ON"] = (
            #         last_time.strftime("%I:%M %p"),
            #         t_on.strftime("%I:%M %p"),
            #     )
            #     last_time = t_on

            # elif last_state == "OFF" and statement == "ON":
            #     if last_time == 0:
            #         last_time = t_on
            #     else:
            #         Total_off_time = Total_off_time + data_push_class.calculate_total_times(
            #             last_time, t_on
            #         )
            #     timestamp_dict["ON"] = (
            #         last_time.strftime("%I:%M %p"),
            #         t_on.strftime("%I:%M %p"),
            #     )
            #     last_state = "ON"
            #     last_time = t_on

            # elif last_state == "OFF" and statement == "OFF":
            #     if last_time == 0:
            #         last_time = t_off
            #     else:
            #         Total_off_time = Total_off_time + data_push_class.calculate_total_times(
            #             last_time, t_off
            #         )
            #     last_state = "OFF"
            #     timestamp_dict["OFF"] = (
            #         last_time.strftime("%I:%M %p"),
            #         t_off.strftime("%I:%M %p"),
            #     )
            #     last_time = t_off

            # elif last_state == "ON" and statement == "OFF":
            #     if last_time == 0:
            #         last_time = t_off
            #     else:
            #         Total_on_time = Total_on_time + data_push_class.calculate_total_times(
            #             last_time, t_off
            #         )

            #     timestamp_dict["OFF"] = (
            #         last_time.strftime("%I:%M %p"),
            #         t_off.strftime("%I:%M %p"),
            #     )
            #     last_state = "OFF"
            #     last_time = t_off

            # current_time = datetime.datetime.now()

            # if (
            #     current_time - last_off_time_update
            # ).total_seconds() >= 10 * 60 * 60:
            #     print("THE 24 HOURS COMPLETE")
            #     last_off_time_update = current_time
            #     Total_off_time = 0
            #     Total_on_time = 0

            # alarmstatus = alarm_status_function(token)
            # print(statement)
            nested_dict = data_Seperation_Class.nested_Data_seperation(
                converted_payload, token, ACCESS_TOKEN_1
            )
            # print("nested_dict---------", nested_dict)
            payload = json.dumps(nested_dict)
            url = rf"{ANTAR_IIoT_URL}/api/v1/{token}/telemetry"
            # Send POST request to ThingsBoard
            try:
                response = requests.post(url, data=payload)
                if response.status_code == 200:
                    print("Successfully TVCV Data send to API", token)
                    parameter_Class.parameterCheckFuction(
                        deviceID, payload, token, ACCESS_TOKEN_1
                    )
                else:
                    print("Failed to send data. Status code:", response.status_code)
            except requests.exceptions.RequestException as e:
                print("An error occurred: in if condition", str(e))
        elif "CV" in converted_payload and len(converted_payload["CV"]) > 0:
            nested_dict = data_Seperation_Class.nested_Data_seperation(
                converted_payload, token, ACCESS_TOKEN_1
            )
            print("Nested dict CV")

            payload = json.dumps(nested_dict)

            url = rf"{ANTAR_IIoT_URL}/api/v1/{token}/telemetry"
            # Send POST request to ThingsBoard
            try:
                response = requests.post(url, data=payload)
                if response.status_code == 200:
                    print("Successfully CV Data send to API", token)
                    parameter_Class.parameterCheckFuction(
                        deviceID, payload, token, ACCESS_TOKEN_1
                    )
                else:
                    print("Failed to send data. Status code:", response.status_code)
            except requests.exceptions.RequestException as e:
                print("An error occurred: in else condition", str(e))
        elif "TV" in converted_payload and len(converted_payload["TV"]) > 0:
            nested_dict = data_Seperation_Class.nested_Data_seperation(
                converted_payload, token,ACCESS_TOKEN_1
            )
            print("Nested dict TV")

            payload = json.dumps(nested_dict)
            print(token)
            # url = f"{host_address}/api/v1/HRb2BPDvrCdu6RJ67reg/telemetry"
            url = rf"{ANTAR_IIoT_URL}/api/v1/{token}/telemetry"
            # Send POST request to ThingsBoard
            try:
                response = requests.post(url, data=payload)
                if response.status_code == 200:
                    print("Successfully TV Data send to TV API", token)
                    # parameter_Class.parameterCheckFuction(
                    #     deviceID, payload, token, ACCESS_TOKEN_1
                    # )
                else:
                    print("Failed to send data. Status code:", response.status_code)
            except requests.exceptions.RequestException as e:
                print("An error occurred inside the check_for_CV_TV :", str(e))
        else:
            print("Payload was not in Right formate.")
        # except Exception as main_exception:
        #     print(token, " An error occurred in the check_for_CV_TV block:", str(main_exception))
