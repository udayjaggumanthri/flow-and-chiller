import datetime
import requests
import json
from device_Details.device_details_Controller import DeviceManager
from .param_Check_Controller import parameter_Class
from config import ANTAR_IIoT_URL
class alarm_Status_Class:
    @staticmethod
    def alarm_status_function(token,ACCESS_TOKEN_1):
        try:
            today_date = datetime.date.today()
            start_date = f"{today_date} 00:00:00"
            start_ts = parameter_Class.epoch_time_function(start_date)
            end_date = f"{today_date} 23:59:59"
            end_ts = parameter_Class.epoch_time_function(end_date)
            # print("Alarm status function",start_date)
            # print("Alarm status function",end_date)
            # url = f"{ANTAR_IIoT_URL}/api/auth/login"

            # # Define the request headers
            # headers = {"accept": "application/json", "Content-Type": "application/json"}

            # # Define the request body (login credentials)
            # data = {"username": "tenant@antariiot.com", "password": "tenant"}
            # # Send a POST request to the endpoint with the headers and data
            # response = requests.post(url, headers=headers, data=json.dumps(data))

            # # Check if the token was successfully generated
            # if response.status_code == 200:
            #     ACCESS_TOKEN = response.json().get("token")
            # else:
            #     print("Token generation failed.")
            deviceID = DeviceManager.get_device_id_by_token(token)
            total = 0

            # print("Device", item)
            url = f"{ANTAR_IIoT_URL}/api/alarm/DEVICE/{deviceID}?searchStatus=ACTIVE&pageSize=30&page=30&sortProperty=status&sortOrder=ASC&startTime={start_ts}&endTime={end_ts}"
            # url = f"http://172.28.80.53:8080/api/alarm/DEVICE/152a16d0-9d92-11ee-bc95-31299a51ef6f?searchStatus=ACTIVE&pageSize=30&page=30&sortProperty=status&sortOrder=ASC&startTime=1705017600000&endTime=1705103999000"
            headers = {"X-Authorization": f"Bearer {ACCESS_TOKEN_1}"}
            response = requests.get(url, headers=headers)
            # print(response.status_code)
            if response.status_code == 200:
                data = response.json()
                # print("Response",data.get('data'))
                total = data.get("totalElements")
                # print("totalElements",total)
            if total > 0:
                return total
            else:
                return total
        except Exception as e:
            print("Error in alarm_status_function:", str(e))
            return 0
