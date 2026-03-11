import datetime
import json
from Thresholds.Thresholds_controller import THRESHOLDS
from device_Details.device_details_Controller import DeviceManager
from .create_Alarm_Controller import create_Alarm_Class


class parameter_Class:
    @staticmethod
    def epoch_time_function(date):
        try:
            datetime_obj = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
            epoch_time = int(datetime_obj.timestamp())
            ts = int(str(epoch_time) + "000")
            return ts
        except ValueError:
            print(
                "Invalid input format. Please enter time in the format YYYY-MM-DD HH:MM:SS."
            )

    @staticmethod
    def parameterCheckFuction(deviceID, data, token, ACCESS_TOKEN_1):
        # print("parameterCheckFuction",deviceID,"\n",data,"\n",token)
        converted = json.loads(data)
        """
        Checks if any parameters in the data exceed their respective thresholds
        and creates an alarm if they do.
        """
        exceeded_params = []

        device_thresholds = THRESHOLDS.get(token)

        if device_thresholds is None:
            print(f"No thresholds defined for device ID: {deviceID}")
        else:
            # print("converted:", converted)
            # print("device_thresholds:", device_thresholds)
            # print("Converted:",converted)

            for param, value in converted.items():
                threshold = device_thresholds.get(param)
                if threshold is None:
                    continue

                # ✅ Case: Threshold is a dict with severities
                if isinstance(threshold, dict):
                    # print("Threshold is a dict with severities")
                    for severity in [
                        "critical",
                        "major",
                        "minor",
                    ]:  # Order: most severe first
                        th_val = threshold.get(severity)
                        if th_val is None:
                            continue

                        # Case 1: Range check (min, max)
                        if isinstance(th_val, tuple) and len(th_val) == 2:
                            # print("Case 1: Range check (min, max)")
                            min_val, max_val = th_val
                            if not (min_val <= value <= max_val):
                                exceeded_params.append(
                                    {
                                        "Parameter": param,
                                        "Value": value,
                                        "Alert": severity.upper(),
                                        "Threshold": f"< {min_val} - {max_val} >",
                                    }
                                )
                                break  # Alert only once with highest severity

                        # Case 2: Single upper bound
                        elif isinstance(th_val, (int, float)):
                            # print("Case 2: Single upper bound",th_val,value)
                            if value > th_val:
                                exceeded_params.append(
                                    {
                                        "Parameter": param,
                                        "Value": value,
                                        "Alert": severity.upper(),
                                        "Threshold": f"> {th_val}",
                                    }
                                )
                                break  # Alert only once with highest severity

                # ✅ Case: Flat range (min, max) outside severity dict
                elif isinstance(threshold, tuple) and len(threshold) == 2:
                    # print("Flat range (min, max) outside severity dict")
                    min_val, max_val = threshold
                    if not (min_val <= value <= max_val):
                        exceeded_params.append(
                            {
                                "Parameter": param,
                                "Value": value,
                                "Alert": "MINOR",
                                "Threshold": f"< {min_val} - {max_val} >",
                            }
                        )

                # ✅ Case: Flat max value
                elif isinstance(threshold, (int, float)):
                    # print("Flat max value")
                    if value > threshold:
                        exceeded_params.append(
                            {
                                "Parameter": param,
                                "Value": value,
                                "Alert": "MINOR",
                                "Threshold": f"< {threshold}",
                            }
                        )

        # print(" Exceeded Parameters:", exceeded_params)

        # Generate an alarm based on the exceeded parameters
        if exceeded_params:
            alarm_message = "Following parameters exceeded threshold:\n" + "\n".join(
                f"{list(item.keys())[0]}: {item[list(item.keys())[0]]} | Value:{item['Value']} | Alert: {item['Alert']} | Threshold: {item['Threshold']}"
                for item in exceeded_params
            )
            print(alarm_message)

            create_Alarm_Class.create_thingsboard_alarm(
                ACCESS_TOKEN_1, deviceID, alarm_message, data, token
            )
