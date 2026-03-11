import datetime
import requests
import time


class get_Alarm_Class:
    @staticmethod
    def get_existing_alarm(ACCESS_TOKEN, deviceID):
        from config import ANTAR_IIoT_URL
        """
        Checks if an active alarm of a given type exists for the device.
        
        """
        from .param_Check_Controller import parameter_Class
        today = datetime.date.today()
        today_date = today - datetime.timedelta(days=2)
        start_date = f"{today_date} 00:00:00"
        start_ts = parameter_Class.epoch_time_function(start_date)
        end_date = f"{today} 23:59:59"
        end_ts = parameter_Class.epoch_time_function(end_date)
        headers = {
            "Content-Type": "application/json",
            "X-Authorization": f"Bearer {ACCESS_TOKEN}",
        }
        # print(deviceID)

        # url = f"http://172.28.80.53:8080/api/alarm?originator={deviceID}&status=ACTIVE_UNACK"
        url = f"{ANTAR_IIoT_URL}/api/alarms?entityId={deviceID}&entityType=DEVICE&pageSize=10&page=0&sortProperty=startTs&sortOrder=DESC&startTs={start_ts}&endTs={end_ts}&searchStatus=ACTIVE"

        response = requests.get(url, headers=headers)
        # print("response.status_code", deviceID)
        if response.status_code == 200:
            alarms = response.json().get("data", [])
            # print(len(alarms))
            for alarm in alarms:

                # if alarm["type"] == alarm_type:
                if (
                    alarm["originator"]["id"] == deviceID
                    and alarm["type"] == "Chiller Monitoring Alarm"
                    and alarm["status"] == "ACTIVE_UNACK"
                ):
                    print("Alarm:", alarm["originator"]["id"])
                    print("alarm already exist")
                    return alarm
            time.sleep(1)

            # return alarm  # Return existing alarm details
        return None  # No active alarm found
