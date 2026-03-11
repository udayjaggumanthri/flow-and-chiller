import os
import datetime
import pandas as pd


class excel_Download_Class:

    @staticmethod
    def safe_get(data_list, index):
        try:
            value = data_list[index].get("value")
            return value if value is not None else None
        except Exception:
            return None

    @staticmethod
    def excel_download_function(data, file_path, device_name):

        columns = {}

        # -------------------------------------------------
        # TIMESTAMP BASE (Temperature → RY_Voltage)
        # -------------------------------------------------
        timestamps = []

        if data.get("Temperature"):
            base_data = data["Temperature"]
            base_source = "Temperature"
        elif data.get("RY_Voltage"):
            base_data = data["RY_Voltage"]
            base_source = "RY_Voltage"
        else:
            base_data = []
            base_source = None

        if not base_data:
            print("No base telemetry found for timestamp.")
        else:
            for item in base_data:
                ts = item.get("ts")
                if ts:
                    dt = datetime.datetime.fromtimestamp(ts / 1000)
                    timestamps.append(dt.strftime("%Y-%m-%d %H:%M:%S"))
                else:
                    timestamps.append(None)

        columns["TimeStamp"] = timestamps
        row_count = len(timestamps)

        # -------------------------------------------------
        # ELECTRICAL PARAMETERS
        # -------------------------------------------------
        electrical_map = {
            "RY_Voltage": "RY_Voltage",
            "YB_Voltage": "YB_Voltage",
            "BR_Voltage": "BR_Voltage",
            "R_Phase_line_Current": "R_Phase_line_Current",
            "Y_Phase_line_Current": "Y_Phase_line_Current",
            "B_Phase_line_Current": "B_Phase_line_Current",
            "Rph_power_Factor": "Rph_power_Factor",
            "Yph_power_Factor": "Yph_power_Factor",
            "Bph_power_Factor": "Bph_power_Factor",
            "Frequency": "Frequency",
            "Total_KW_wrt_line": "Total_KW_wrt_line",
            "Total_KWh_wrt_line": "Total_KWh_wrt_line",
            "RN_Voltage": "RN_Voltage",
            "YN_Voltage": "YN_Voltage",
            "BN_Voltage": "BN_Voltage",
            "avg_Current": "Avg_Current",
            "avg_Voltage": "Avg_Voltage"
        }

        for key, col_name in electrical_map.items():
            if key in data:
                values = [
                    excel_Download_Class.safe_get(data[key], i)
                    for i in range(row_count)
                ]
                if any(v is not None for v in values):
                    columns[col_name] = values

        # -------------------------------------------------
        # VIBRATION / CONDITION MONITORING PARAMETERS
        # -------------------------------------------------
        vibration_map = {
            "Temperature": "Temperature",
            "XaxisRMSVelocity": "XaxisRMSVelocity",
            "YaxisRMSVelocity": "YaxisRMSVelocity",
            "ZaxisRMSVelocity": "ZaxisRMSVelocity",
            "XaxisHFRMSAcceleration": "XaxisHFRMSAcceleration",
            "YaxisHFRMSAcceleration": "YaxisHFRMSAcceleration",
            "ZaxisHFRMSAcceleration": "ZaxisHFRMSAcceleration",
            "Magnitude": "Magnitude",
            
        }

        for key, col_name in vibration_map.items():
            if key in data:
                values = [
                    excel_Download_Class.safe_get(data[key], i)
                    for i in range(row_count)
                ]
                if any(v is not None for v in values):
                    columns[col_name] = values

        # -------------------------------------------------
        # CREATE DATAFRAME
        # -------------------------------------------------
        df = pd.DataFrame(columns)

        # -------------------------------------------------
        # FOLDER & FILE STRUCTURE (UNCHANGED)
        # -------------------------------------------------
        today = datetime.date.today()
        year = today.strftime("%Y")
        month_string = today.strftime("%B")

        final_path = os.path.join(
            file_path, year, month_string, f"device-{device_name}"
        )
        os.makedirs(final_path, exist_ok=True)

        yesterday = today - datetime.timedelta(days=1)
        date_string = yesterday.strftime("%d_%Y_%A_%B_")

        output_path = os.path.join(
            final_path, f"{date_string}{device_name}.xlsx"
        )

        df.to_excel(output_path, index=False)

        print(f"Excel file created successfully using {base_source} as timestamp base:")
        print(output_path)
