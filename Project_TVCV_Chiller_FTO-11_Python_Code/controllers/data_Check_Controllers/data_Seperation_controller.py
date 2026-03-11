# Callback function to check the data in valid data or not
from ..Alarm_Controllers.alarm_Status_Controller import alarm_Status_Class


class data_Seperation_Class:
    @staticmethod
    def data_check(data, i):
        # print("data_check", data[i] is not None, data[i], "---", i)
        if data[i] is not None:
            try:
                return data[i]
            except IndexError:
                return None
        else:
            return None

    @staticmethod
    def data_check_float(data, i):
        # print("data_check_float", data[i] is not None, data[i], "---", i)
        if data[i] is not None:
            try:
                return data[i]
            except IndexError:
                return 0.0
        else:
            return None

    @staticmethod
    def avg_LL_Voltage_Cal(value1, value2, value3):
        if value1 > 0 and value2 > 0 and value3 > 0:
            avg = value1 + value2 + value3
            LL = avg / 3
            # print("LL: --------",LL)
            return LL
        else:
            return 0

    # def avg_LL_Voltage_Cal(value1, value2, value3):
    #     try:
    #         if value1 is not None and value2 is not None and value3 is not None:
    #             if value1 > 0 and value2 > 0 and value3 > 0:
    #                 avg = value1 + value2 + value3
    #                 LL = avg / 3
    #                 return LL
    #         return None
    #     except Exception as e:
    #         print(f"Error in avg_LL_Voltage_Cal: {e}")
    #         return None

    @staticmethod
    def safe_float(value):
        try:
            return float(value) if value is not None else None
        except Exception:
            return None

    @staticmethod
    def nested_Data_seperation(d, token, ACCESS_TOKEN_1):
        print("nested")
        statement = None
        nested = {}
        if (
            "CV" in d
            and isinstance(d["CV"], list)
            and len(d["CV"]) > 0
            and "TV" in d
            and isinstance(d["TV"], list)
            and len(d["TV"]) > 0
        ):
            val3 = data_Seperation_Class.data_check_float(d["CV"], 3)
            val4 = data_Seperation_Class.data_check_float(d["CV"], 4)
            val5 = data_Seperation_Class.data_check_float(d["CV"], 5)
            # If any is None → statement = None
            if val3 is None and val4 is None and val5 is None:
                statement = None
            else:
                conv_val3 = val3 if val3 is not None else 0.0
                conv_val4 = val4 if val4 is not None else 0.0
                conv_val5 = val5 if val5 is not None else 0.0
                print(
                    "conv_val3",
                )
                avg_current = (
                    float(conv_val3) + float(conv_val4) + float(conv_val5)
                ) / 3
                if avg_current >= 6.0:
                    statement = "ON"
                else:
                    statement = "OFF"
            # if (
            #     float(data_Seperation_Class.data_check(d["CV"], 3))
            #     + float(data_Seperation_Class.data_check(d["CV"], 4))
            #     + float(data_Seperation_Class.data_check(d["CV"], 5))
            # ) >= 0.5:
            #     statement = "ON"
            # else:
            #     statement = "OFF"

            nested = {
                "TVCVtopic": token,
                "RY_Voltage": int(data_Seperation_Class.data_check(d["CV"], 0)),
                "YB_Voltage": int(data_Seperation_Class.data_check(d["CV"], 1)),
                "BR_Voltage": int(data_Seperation_Class.data_check(d["CV"], 2)),
                "Avg_LL_Voltage": int(
                    data_Seperation_Class.avg_LL_Voltage_Cal(
                        data_Seperation_Class.data_check(d["CV"], 0),
                        data_Seperation_Class.data_check(d["CV"], 1),
                        data_Seperation_Class.data_check(d["CV"], 1),
                    )
                ),
                # "RY_Voltage": (
                #     int(data_Seperation_Class.data_check(d["CV"], 0))
                #     if data_Seperation_Class.data_check(d["CV"], 0)
                #     else None
                # ),
                # "YB_Voltage": (
                #     int(data_Seperation_Class.data_check(d["CV"], 1))
                #     if data_Seperation_Class.data_check(d["CV"], 1)
                #     else None
                # ),
                # "BR_Voltage": (
                #     int(data_Seperation_Class.data_check(d["CV"], 2))
                #     if data_Seperation_Class.data_check(d["CV"], 2)
                #     else None
                # ),
                # "Avg_LL_Voltage": (
                #     int(
                #         data_Seperation_Class.avg_LL_Voltage_Cal(
                #             data_Seperation_Class.data_check(d["CV"], 0),
                #             data_Seperation_Class.data_check(d["CV"], 1),
                #             data_Seperation_Class.data_check(d["CV"], 1),
                #         )
                #     )
                #     if data_Seperation_Class.avg_LL_Voltage_Cal(
                #         data_Seperation_Class.data_check(d["CV"], 0),
                #         data_Seperation_Class.data_check(d["CV"], 1),
                #         data_Seperation_Class.data_check(d["CV"], 1),
                #     )
                #     else None
                # ),
                "R_Phase_line_Current": (
                    float(val)
                    if (val := data_Seperation_Class.data_check(d["CV"], 3)) is not None
                    else None
                ),
                "Y_Phase_line_Current": data_Seperation_Class.safe_float(
                    data_Seperation_Class.data_check(d["CV"], 4)
                ),
                "B_Phase_line_Current": data_Seperation_Class.safe_float(
                    data_Seperation_Class.data_check(d["CV"], 5)
                ),
                "Rph_power_Factor": (
                    float(val)
                    if (val := data_Seperation_Class.data_check(d["CV"], 6)) is not None
                    else None
                ),
                "Yph_power_Factor": (
                    float(val)
                    if (val := data_Seperation_Class.data_check(d["CV"], 7)) is not None
                    else None
                ),
                "Bph_power_Factor": (
                    float(val)
                    if (val := data_Seperation_Class.data_check(d["CV"], 8)) is not None
                    else None
                ),
                "Frequency": data_Seperation_Class.data_check(d["CV"], 9),
                "Total_KW_wrt_line": data_Seperation_Class.data_check(d["CV"], 10),
                "Total_KWh_wrt_line": data_Seperation_Class.data_check(d["CV"], 11),
                "RN_Voltage": data_Seperation_Class.data_check(d["CV"], 12),
                "YN_Voltage": data_Seperation_Class.data_check(d["CV"], 13),
                "BN_Voltage": data_Seperation_Class.data_check(d["CV"], 14),
                "avg_Voltage": data_Seperation_Class.data_check(d["CV"], 15),
                "avg_Current": data_Seperation_Class.data_check(d["CV"], 16),
                "avg_Power_Factor": data_Seperation_Class.data_check(d["CV"], 17),
                "Temperature": (
                    data_Seperation_Class.data_check(d["TV"], 0) / 100
                    if data_Seperation_Class.data_check(d["TV"], 0) is not None
                    else None
                ),
                "XaxisRMSVelocity": (
                    data_Seperation_Class.data_check(d["TV"], 1) / 1000
                    if data_Seperation_Class.data_check(d["TV"], 1) is not None
                    else None
                ),
                 "YaxisRMSVelocity": (
                    data_Seperation_Class.data_check(d["TV"], 2) / 1000
                    if data_Seperation_Class.data_check(d["TV"], 2) is not None
                    else None
                ),
                "ZaxisRMSVelocity": (
                    data_Seperation_Class.data_check(d["TV"], 3) / 1000
                    if data_Seperation_Class.data_check(d["TV"], 2) is not None
                    else None
                ),
              
                "XaxisHFRMSAcceleration": (
                    data_Seperation_Class.data_check(d["TV"], 4) / 1000
                    if data_Seperation_Class.data_check(d["TV"], 5) is not None
                    else None
                ),
                 "YaxisHFRMSAcceleration": (
                    data_Seperation_Class.data_check(d["TV"], 5) / 1000
                    if data_Seperation_Class.data_check(d["TV"], 6) is not None
                    else None
                ),
                "ZaxisHFRMSAcceleration": (
                    data_Seperation_Class.data_check(d["TV"], 6) / 1000
                    if data_Seperation_Class.data_check(d["TV"], 6) is not None
                    else None
                ),
                "Magnitude": (
                    data_Seperation_Class.data_check(d["TV"], 7) /1000
                    if data_Seperation_Class.data_check(d["TV"], 7) is not None
                    else None
                ),
                # "Under_Voltage": data_Seperation_Class.data_check(d["ED"], 12),
                # "Over_Voltage": data_Seperation_Class.data_check(d["ED"], 13),
                # "Under_Current": data_Seperation_Class.data_check(d["ED"], 14),
                # "Over_Current": data_Seperation_Class.data_check(d["ED"], 15),
                # "RN_Voltage": data_Seperation_Class.data_check(d["ED"], 16),
                # "YN_Voltage": data_Seperation_Class.data_check(d["ED"], 17),
                # "BN_Voltage": data_Seperation_Class.data_check(d["ED"], 18),
                "status": statement,
                "Alarm_Status": alarm_Status_Class.alarm_status_function(
                    token, ACCESS_TOKEN_1
                ),
                # # "Motor_on_hrs": 14.00,
                # "Motor_on_hrs": Total_on_time,
                # "Motor_off_hrs": Total_off_time,
                # # "Motor_off_hrs": 10.00,
                # "timestamps": timestamp_dict,
            }
        elif "TV" in d and len(d["TV"]) > 0:
            print("TV data.")
            nested = {
                "Temperature": (
                    data_Seperation_Class.data_check(d["TV"], 0) / 100
                    if data_Seperation_Class.data_check(d["TV"], 0) is not None
                    else None
                ),
                "XaxisRMSVelocity": (
                    data_Seperation_Class.data_check(d["TV"], 1) / 1000
                    if data_Seperation_Class.data_check(d["TV"], 1) is not None
                    else None
                ),
                "YaxisRMSVelocity": (
                    data_Seperation_Class.data_check(d["TV"], 2) / 1000
                    if data_Seperation_Class.data_check(d["TV"], 2) is not None
                    else None
                ),
                "ZaxisRMSVelocity": (
                    data_Seperation_Class.data_check(d["TV"], 3) / 1000
                    if data_Seperation_Class.data_check(d["TV"], 2) is not None
                    else None
                ),
              
                "XaxisHFRMSAcceleration": (
                    data_Seperation_Class.data_check(d["TV"], 4) / 1000
                    if data_Seperation_Class.data_check(d["TV"], 5) is not None
                    else None
                ),
                 "YaxisHFRMSAcceleration": (
                    data_Seperation_Class.data_check(d["TV"], 5) / 1000
                    if data_Seperation_Class.data_check(d["TV"], 6) is not None
                    else None
                ),
                "ZaxisHFRMSAcceleration": (
                    data_Seperation_Class.data_check(d["TV"], 6) / 1000
                    if data_Seperation_Class.data_check(d["TV"], 6) is not None
                    else None
                ),
                "Magnitude": (
                    data_Seperation_Class.data_check(d["TV"], 7)/1000
                    if data_Seperation_Class.data_check(d["TV"], 7) is not None
                    else None
                ),
               
                "status": "OFF",
                "Alarm_Status": alarm_Status_Class.alarm_status_function(
                    token, ACCESS_TOKEN_1
                ),
                # # "Motor_on_hrs": 14.00,
                # "Motor_on_hrs": Total_on_time,
                # "Motor_off_hrs": Total_off_time,
                # # "Motor_off_hrs": 10.00,
                # "timestamps": timestamp_dict,
            }
        elif "CV" in d and len(d["CV"]) > 0:
            val3 = data_Seperation_Class.data_check_float(d["CV"], 3)
            val4 = data_Seperation_Class.data_check_float(d["CV"], 4)
            val5 = data_Seperation_Class.data_check_float(d["CV"], 5)
            # If any is None → statement = None
            if val3 is None and val4 is None and val5 is None:
                statement = None
            else:
                conv_val3 = val3 if val3 is not None else 0.0
                conv_val4 = val4 if val4 is not None else 0.0
                conv_val5 = val5 if val5 is not None else 0.0
                avg_current = (
                    float(conv_val3) + float(conv_val4) + float(conv_val5)
                ) / 3
                if avg_current >= 6.0:
                    statement = "ON"
                else:
                    statement = "OFF"
            # if (
            #     float(data_Seperation_Class.data_check(d["CV"], 3))
            #     + float(data_Seperation_Class.data_check(d["CV"], 4))
            #     + float(data_Seperation_Class.data_check(d["CV"], 5))
            # ) >= 0.5:
            #     statement = "ON"
            # else:
            #     statement = "OFF"

            nested = {
                "TVCVtopic": token,
                "RY_Voltage": (
                    int(data_Seperation_Class.data_check(d["CV"], 0))
                    if data_Seperation_Class.data_check(d["CV"], 0)
                    else None
                ),
                "YB_Voltage": (
                    int(data_Seperation_Class.data_check(d["CV"], 1))
                    if data_Seperation_Class.data_check(d["CV"], 1)
                    else None
                ),
                "BR_Voltage": (
                    int(data_Seperation_Class.data_check(d["CV"], 2))
                    if data_Seperation_Class.data_check(d["CV"], 2)
                    else None
                ),
                "Avg_LL_Voltage": (
                    int(
                        data_Seperation_Class.avg_LL_Voltage_Cal(
                            data_Seperation_Class.data_check(d["CV"], 0),
                            data_Seperation_Class.data_check(d["CV"], 1),
                            data_Seperation_Class.data_check(d["CV"], 1),
                        )
                    )
                    if data_Seperation_Class.avg_LL_Voltage_Cal(
                        data_Seperation_Class.data_check(d["CV"], 0),
                        data_Seperation_Class.data_check(d["CV"], 1),
                        data_Seperation_Class.data_check(d["CV"], 1),
                    )
                    else None
                ),
                "R_Phase_line_Current": (
                    float(val)
                    if (val := data_Seperation_Class.data_check(d["CV"], 3)) is not None
                    else None
                ),
                "Y_Phase_line_Current": data_Seperation_Class.safe_float(
                    data_Seperation_Class.data_check(d["CV"], 4)
                ),
                "B_Phase_line_Current": data_Seperation_Class.safe_float(
                    data_Seperation_Class.data_check(d["CV"], 5)
                ),
                "Rph_power_Factor": (
                    float(val)
                    if (val := data_Seperation_Class.data_check(d["CV"], 6)) is not None
                    else None
                ),
                "Yph_power_Factor": (
                    float(val)
                    if (val := data_Seperation_Class.data_check(d["CV"], 7)) is not None
                    else None
                ),
                "Bph_power_Factor": (
                    float(val)
                    if (val := data_Seperation_Class.data_check(d["CV"], 8)) is not None
                    else None
                ),
                "Frequency": data_Seperation_Class.data_check(d["CV"], 9),
                "Total_KW_wrt_line": data_Seperation_Class.data_check(d["CV"], 10),
                "Total_KWh_wrt_line": data_Seperation_Class.data_check(d["CV"], 11),
                "RN_Voltage": data_Seperation_Class.data_check(d["CV"], 12),
                "YN_Voltage": data_Seperation_Class.data_check(d["CV"], 13),
                "BN_Voltage": data_Seperation_Class.data_check(d["CV"], 14),
                "avg_Voltage": data_Seperation_Class.data_check(d["CV"], 15),
                "avg_Current": data_Seperation_Class.data_check(d["CV"], 16),
                "avg_Power_Factor": data_Seperation_Class.data_check(d["CV"], 17),
                "status": statement,
                "Alarm_Status": alarm_Status_Class.alarm_status_function(
                    token, ACCESS_TOKEN_1
                ),
                # # "Motor_on_hrs": 14.00,
                # "Motor_on_hrs": Total_on_time,
                # "Motor_off_hrs": Total_off_time,
                # # "Motor_off_hrs": 10.00,
                # "timestamps": timestamp_dict,
            }
        return nested
