# controllers/mqtt_controller.py

import paho.mqtt.client as mqtt
import json
import time
from .mqtt_Data_Dump_Controller import mqtt_Data_Controller
from config import MQTT_CLIENT

ACCESS_TOKEN_1 = None
class MQTTController:
    def __init__(self, broker_host, broker_port, username, password, topic,ACCESS_TOKEN):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.username = username
        self.password = password
        self.topic = topic
        self.client = mqtt.Client()

        # Set callbacks
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        # Set credentials
        self.client.username_pw_set(self.username, self.password)
        # Declaring Access Token Here 
        global ACCESS_TOKEN_1
        ACCESS_TOKEN_1 = ACCESS_TOKEN

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to broker.")
            self.client.subscribe(self.topic)
            print(f"Subscribed to: {self.topic}")
        else:
            print(f"Connection failed with code {rc}")

    def on_message(self, client, userdata, msg):
        MQTT_CLIENT = client
        # print(f"Message on {msg.topic}: {MQTT_CLIENT}")
        try:
            topic = msg.topic
            string = msg.payload.decode()
            converted_payload = json.loads(string)
            original_payload = json.dumps(converted_payload)
            start_time = time.time()
            mqtt_Data_Controller.topic_check(topic,converted_payload,original_payload,client,ACCESS_TOKEN_1)
            end_time = time.time()
            execution_time = end_time - start_time
            print(f"Execution time: {execution_time:.4f} seconds")
            
        except (UnicodeDecodeError, json.decoder.JSONDecodeError) as e:
            print("Failed to decode with any encoding. Handle this case accordingly.")
        

    def connect_and_listen(self):
        try:
            print(f"Connecting to {self.broker_host}:{self.broker_port}")
            self.client.connect(self.broker_host, self.broker_port)
            self.client.loop_forever()
        except Exception as e:
            print(f"MQTT connection error: {e}")
