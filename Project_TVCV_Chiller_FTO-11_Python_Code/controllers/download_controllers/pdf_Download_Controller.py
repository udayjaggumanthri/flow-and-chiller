import datetime
import os
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Image,
    Spacer,
    Paragraph,
    Frame,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.units import inch
# from .download_func_caller import data_formator_2,data_formator_3,AntarIIoT_data_check
# Define a custom color with RGB values
cornflower_Blue = colors.Color(100 / 255, 149 / 255, 237 / 255)
pastel_bule = colors.Color(167 / 255, 199 / 255, 231 / 255)

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
icon_path = os.path.join(base_dir, 'assets', 'reddy_icon.png')

class pdf_Download_Class:
    @staticmethod
    def data_formator_3(data1, data2, data3):
        temp = f"{data1}: {data2}: {data3}"
        return temp

    @staticmethod
    def data_formator_2(data1, data2):
        temp = f"{data1}: {data2}"
        return temp

    @staticmethod
    def AntarIIoT_data_check(data, i):
        try:
            return data[i]["value"]
        except (KeyError, IndexError, TypeError):
            return 0
    def AntarIIOT_String_Data_Check(data,i):
        try:
            return data[i]["value"]
        except (KeyError, IndexError, TypeError):
            return "NAN"
            

    @staticmethod
    def pdf_download_function(data, file_path_pdf, device_name):
        final_data = [
            [
                "TimeStamp",
                "RY_Voltage\nYB_Voltage\nBR_Voltage",
                "R_Phase_Current\nY_Phase_Current\nB_Phase_Current",
                "Rph_PF\nYph_PF\nBph_PF",
                "Frequency",
                "KW\nKWh",
                "RN_Voltage\nYN_Voltage\nBN_Voltage",
                "Status",
                "Surface\nTemperature",
                "X_RMS_Vel\nZ_RMS_Vel",
            ]
        ]
        pdf_data = []
        if bool(data):
            # print("lenght:", len(data["Frequency"]))
            for i in range(len(data["Frequency"])):
                # print(thingboard_data_check(data["Frequency"], i))
                timestamp = data["Frequency"][i]["ts"]
                datetime_value = datetime.datetime.fromtimestamp(timestamp / 1000)
                pdf_data.append((datetime_value.strftime("%Y-%m-%d %H:%M:%S")))
                pdf_data.append(
                    pdf_Download_Class.data_formator_3(
                        (pdf_Download_Class.AntarIIoT_data_check(data["RY_Voltage"], i)),
                        (pdf_Download_Class.AntarIIoT_data_check(data["YB_Voltage"], i)),
                        (pdf_Download_Class.AntarIIoT_data_check(data["BR_Voltage"], i)),
                    )
                ),
                pdf_data.append(
                    pdf_Download_Class.data_formator_3(
                        (pdf_Download_Class.AntarIIoT_data_check(data["R_Phase_line_Current"], i)),
                        (pdf_Download_Class.AntarIIoT_data_check(data["Y_Phase_line_Current"], i)),
                        (pdf_Download_Class.AntarIIoT_data_check(data["B_Phase_line_Current"], i)),
                    )
                )
                pdf_data.append(
                    pdf_Download_Class.data_formator_3(
                        (pdf_Download_Class.AntarIIoT_data_check(data["Rph_power_Factor"], i)),
                        (pdf_Download_Class.AntarIIoT_data_check(data["Yph_power_Factor"], i)),
                        (pdf_Download_Class.AntarIIoT_data_check(data["Bph_power_Factor"], i)),
                    )
                )

                pdf_data.append((pdf_Download_Class.AntarIIoT_data_check(data["Frequency"], i))),
                pdf_data.append(
                    pdf_Download_Class.data_formator_2(
                        (pdf_Download_Class.AntarIIoT_data_check(data["Total_KW_wrt_line"], i)),
                        (pdf_Download_Class.AntarIIoT_data_check(data["Total_KWh_wrt_line"], i)),
                    )
                ),
                pdf_data.append(
                    pdf_Download_Class.data_formator_3(
                        (pdf_Download_Class.AntarIIoT_data_check(data["RN_Voltage"], i)),
                        (pdf_Download_Class.AntarIIoT_data_check(data["YN_Voltage"], i)),
                        (pdf_Download_Class.AntarIIoT_data_check(data["BN_Voltage"], i)),
                    )
                )
                pdf_data.append((pdf_Download_Class.AntarIIOT_String_Data_Check(data.get("status",[]), i))),
                pdf_data.append(pdf_Download_Class.AntarIIoT_data_check(data.get("Temperature",[]), i)),
                pdf_data.append(
                    pdf_Download_Class.data_formator_2(
                        (pdf_Download_Class.AntarIIoT_data_check(data.get("XaxisRMSVelocity",[]), i)),
                        (pdf_Download_Class.AntarIIoT_data_check(data.get("ZaxisRMSVelocity",[]), i)),
                    )
                ),
                final_data.append(pdf_data),
                pdf_data = []

            # print("Final_data", final_data)
            today = datetime.date.today()
            year = today.strftime("%Y")
            month_string = today.strftime("%B")
            final_path = f"{file_path_pdf}\\{year}\\{month_string}\\device-{device_name}"
            # print(final_path)
            if not os.path.exists(final_path):
                os.makedirs(final_path)

            yesterday = today - datetime.timedelta(days=1)
            date_string = yesterday.strftime("%d_%Y_%A_%B_")

            doc = SimpleDocTemplate(
                f"{file_path_pdf}\\{year}\\{month_string}\\device-{device_name}\\{date_string}{device_name}.pdf",
                pagesize=landscape(letter),
                leftMargin=10,
                rightMargin=10,
                topMargin=30,
                bottomMargin=10,
            )

            # this logo code
            elements = []
            
            logo_path = "download_controllers/reddy_icon.png"
            logo = Image(icon_path, width=2 * inch, height=0.6 * inch)
            logo.x = 25
            logo.y = 400
            elements.append(logo)
            elements.append(Spacer(1, 12))

            # # Add company address in the header
            # address = "123 Company St, City, Country"
            # address_style = ParagraphStyle(name="HeaderAddress", fontSize=10, alignment=1)
            # address_paragraph = Paragraph(address, address_style)
            # elements.append(address_paragraph)

            # # Add a line break
            # elements.append(Paragraph(" ", getSampleStyleSheet()["Normal"]))

            table = Table(final_data)
            style = TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), cornflower_Blue),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), pastel_bule),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
            table.setStyle(style)
            elements.append(table)
            doc.build(elements)
            print("PDF data1 created successfully.")
