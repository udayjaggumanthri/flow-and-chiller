# main_Code.py

import threading
import datetime
import time

from controllers.mqtt_Controllers.mqtt_Controller import MQTTController
from controllers.download_controllers.download_func_caller import download_Class
from controllers.access_Controllers.access_Controller import access_Token
from config import (
    BROKER_IP,
    BROKER_USERNAME,
    BROKER_PORT,
    BROKER_PASSWORD,
    BROKER_TOPIC,
    ANTAR_IIoT_URL,
)

ACCESS_TOKEN = None


def mqtt_Function():
    """MQTT Listener Thread"""
    time.sleep(1)
    print("Starting MQTT service...")

    mqtt_client = MQTTController(
        BROKER_IP,
        BROKER_PORT,
        BROKER_USERNAME,
        BROKER_PASSWORD,
        BROKER_TOPIC,
        ACCESS_TOKEN,
    )

    mqtt_client.connect_and_listen()


def excelAndPdf_function():
    """Excel and PDF Scheduler Thread"""
    print("excelAndPdf_function started")

    while True:
        now = datetime.datetime.now()
        date_string = now.strftime("%H:%M")

        if date_string == "00:01":
            print("Excel/PDF job started")
            try:
                download_Class.download_function()
            except Exception as e:
                print("Excel/PDF error:", e)

            time.sleep(60)

        time.sleep(30)


def access_Token_Generator_Caller():
    """Backend Token Generator Thread (SAFE MODE)"""
    global ACCESS_TOKEN

    print("Access Token thread started")

    while True:
        try:
            ACCESS_TOKEN = access_Token.access_Token_Generator()
            print("Access token refreshed successfully")
            time.sleep(840)  # 14 minutes

        except Exception as e:
            print("Backend not reachable, retrying in 2 minutes...")
            print("Error:", e)
            time.sleep(120)


if __name__ == "__main__":

    print("Application starting...")

    # Create threads
    thread_access = threading.Thread(target=access_Token_Generator_Caller, daemon=True)

    thread_mqtt = threading.Thread(target=mqtt_Function, daemon=True)

    thread_download = threading.Thread(target=excelAndPdf_function, daemon=True)

    # Start threads
    thread_access.start()
    thread_mqtt.start()
    thread_download.start()

    # Keep main thread alive
    while True:
        time.sleep(1)
