import requests
import json
import datetime
from config import ANTAR_IIoT_IP_URL, ANTAR_IIoT_URL
from device_Details.device_details_Controller import DeviceManager
from .pdf_Download_Controller import pdf_Download_Class
from .excel_Download_Controller import excel_Download_Class

from config import FILE_PATH_EXCEL, FILE_PATH_PDF


class download_Class:
    @staticmethod
    def device_Name_From_AntarIIoT(item, token):
        url = f"{ANTAR_IIoT_URL}/api/device/{item}"
        headers = {"X-Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data["name"]
        else:
            print("Request failed with status code:", response.status_code)

    @staticmethod
    def AntarIIoT_data_check(data, i):
        try:
            return data[i]["value"]
        except (KeyError, IndexError, TypeError):
            return 0

    @staticmethod
    # This function dowloads data with yesterday date.
    def download_function():
        token = None
        today = datetime.date.today()
        port = 8080
        TVCVattributes = "RY_Voltage%2CYB_Voltage%2CBR_Voltage%2CR_Phase_line_Current%2CY_Phase_line_Current%2CB_Phase_line_Current%2CRph_power_Factor%2CYph_power_Factor%2CBph_power_Factor%2CFrequency%2CTotal_KW_wrt_line%2CTotal_KWh_wrt_line%2CUnder_Voltage%2COver_Voltage%2CUnder_Current%2COver_Current%2CRN_Voltage%2CYN_Voltage%2CBN_Voltage%2Cstatus%2Cavg_Current%2Cavg_Voltage%2CTemperature%2CXaxisRMSVelocity%2CYaxisRMSVelocity%2CZaxisRMSVelocity%2CXaxisHFRMSAcceleration%2CYaxisHFRMSAcceleration%2CZaxisHFRMSAcceleration%2CMagnitude"
        # human_time1 = input("Enter Start time (YYYY-MM-DD HH:MM:SS): ")
        today_date = datetime.date.today()
        yesterday_start_date = today_date - datetime.timedelta(days=1)
        # human_time1 = f"{yesterday_start_date} 00:00:00"
        human_time1 = f"2025-12-23 00:00:00"
        try:
            datetime_obj1 = datetime.datetime.strptime(human_time1, "%Y-%m-%d %H:%M:%S")
            epoch_time1 = int(datetime_obj1.timestamp())
            startTs = int(str(epoch_time1) + "000")
            # print("Start time: ",startTs)
        except ValueError:
            print(
                "Invalid input format. Please enter time in the format YYYY-MM-DD HH:MM:SS."
            )
            # human_time2 = input("Enter End time (YYYY-MM-DD HH:MM:SS): ")
        yesterday_end_date = today_date - datetime.timedelta(days=1)
        # human_time2 = f"{yesterday_end_date} 23:59:59"
        human_time2 = f"2025-12-23 23:59:59"
        try:
            datetime_obj2 = datetime.datetime.strptime(human_time2, "%Y-%m-%d %H:%M:%S")
            epoch_time2 = int(datetime_obj2.timestamp())
            endTs = int(str(epoch_time2) + "000")
            # print("End time:", endTs)
        except ValueError:
            print(
                "Invalid input format. Please enter time in the format YYYY-MM-DD HH:MM:SS."
            )

        url = f"{ANTAR_IIoT_URL}/api/auth/login"

        # Define the request headers
        headers = {"accept": "application/json", "Content-Type": "application/json"}

        # Define the request body (login credentials)
        # data = {"username": "tenant@antariiot.com", "password": "tenant"}
        data = {"username": "tenant@thingsboard.org", "password": "tenant"}

        # Send a POST request to the endpoint with the headers and data
        response = requests.post(url, headers=headers, data=json.dumps(data))

        # Check if the token was successfully generated
        if response.status_code == 200:
            token = response.json().get("token")
            print("Login was Successfull.",token)
        else:
            print("Login was Not SucCessfull in download functionality.")

        for item in DeviceManager.get_device_ids():
            print("DeviceID: ------", item)
            minute = 60000
            hour = 3600000
            day = 86400000
            week = 604800000
            month = 2592000000
            interval = {
                1: minute,
                2: hour,
                3: day,
                4: week,
                5: month,
            }
            # limit = 2000000000
            device_name = download_Class.device_Name_From_AntarIIoT(item, token)
            url = f"{ANTAR_IIoT_URL}/api/plugins/telemetry/DEVICE/{item}/values/timeseries?keys={TVCVattributes}&startTs={startTs}&endTs={endTs}&interval={day}&limit=2000000000&agg=NONE&orderBy=ASC"
            # keys=Temperature%2CXaxisRMSVelocity%2CZaxisRMSVelocity%2CXaxisPeakVelocity%2CZaxisPeakVelocity%2CXaxisRMSAcceleration%2CZaxisRMSAcceleration%2CXaxisPeakAccleration%2CZaxisPeakAccleration&startTs=1696986061000&endTs=1697106000000&interval=60000&limit=15&agg=NONE
            headers1 = {"X-Authorization": f"Bearer {token}"}
            response = requests.get(url, headers=headers1)
            # while True:
            # Process the response
            if response.status_code == 200:
                data = response.json()

                status_len = len(data.get("status", []))
                temperature_len = len(data.get("Temperature", []))

                print("status length:", status_len)
                print("temperature length:", temperature_len)
                excel_Download_Class.excel_download_function(data, FILE_PATH_EXCEL, device_name)
                # print("device_name", device_name)
                # pdf_Download_Class.pdf_download_function(
                #     data, FILE_PATH_PDF, device_name
                # )

            else:
                print("Request failed with status code:", response.status_code)
