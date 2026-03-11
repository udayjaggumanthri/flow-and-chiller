### mqtt_Controller.py

Location: TVCV_Demo_Code/controllers/mqtt_Controllers/mqtt_Controller.py

Purpose:
Implements the MQTT connection, subscription, and message-handling logic for the TVCV Demo application.  
This controller connects to the broker, authenticates, subscribes to the configured MQTT topic, receives incoming payloads, and forwards them to the data-processing module for further handling.

Key Responsibilities:

- Establish TCP/MQTT connection with broker using host, port, and credentials.
- Subscribe to the configured topic upon successful connection.
- Decode incoming MQTT payloads, validate JSON, and forward them to mqtt_Data_Controller.
- Measure message processing time for monitoring the system’s performance.

Class: MQTTController

Constructor (**init**):

- Initializes MQTT client instance.
- Sets callback functions:
  - on_connect → executed when broker connection is established.
  - on_message → executed whenever a new MQTT message arrives.
- Applies username/password authentication.
- Stores the access token into a global variable (ACCESS_TOKEN_1) for downstream use.
- Accepts the following parameters:
  - broker_host
  - broker_port
  - username
  - password
  - topic
  - ACCESS_TOKEN

Callback: on_connect(client, userdata, flags, rc)

- rc == 0 indicates successful connection.
- Automatically subscribes to the configured topic.
- Prints connection and subscription status to console.

Callback: on_message(client, userdata, msg)

- Receives MQTT message object.
- Extracts:
  - msg.topic → Topic name.
  - msg.payload → Raw payload (decoded & parsed into JSON).
- Converts payload into JSON and original string format.
- Calls:
  mqtt_Data_Controller.topic_check(
  topic,
  converted_payload,
  original_payload,
  client,
  ACCESS_TOKEN_1
  )
- Wraps processing with execution time measurement for performance profiling.
- Handles JSON decode errors gracefully.

Method: connect_and_listen()

- Initiates connection to broker using configured parameters.
- Starts a blocking loop (loop_forever) to continuously listen for messages.
- Prints errors if connection fails.

Dependencies:

- paho.mqtt.client → MQTT communication library.
- mqtt_Data_Controller → downstream controller responsible for validating and processing incoming MQTT data.
- config.MQTT_CLIENT → shared global reference for MQTT interactions.

Notes:

- ACCESS_TOKEN_1 is assigned at initialization time. If tokens change dynamically, the architecture may require an update to pass refreshed tokens.
- loop_forever() blocks the thread; the main application runs this controller inside a dedicated thread to prevent blocking.
- Error handling for malformed payloads ensures system stability even if devices send corrupted data.

### mqtt_Data_Dump_Controller.py

Location: TVCV_Demo_Code/controllers/mqtt_Controllers/mqtt_Data_Dump_Controller.py

Purpose:
Acts as an intermediate router/controller for incoming MQTT messages.  
This module determines which payloads should be processed based on the MQTT topic and forwards valid data to the data_push_controller for further analysis and storage.

Class: mqtt_Data_Controller

1. Static Method: topic_check(topic, converted_payload, original_payload, client, ACCESS_TOKEN_1)

- Inspects the MQTT topic to determine the type of payload.
- Processing rules:
  - If the topic ends with "tvcv":
    - Extracts token ("tvcv") and routes the message to send_dump().
  - If the topic contains "buzzer":
    - Prints a placeholder message indicating buzzer-related communication.
- Designed to support additional topic patterns in the future.

2. Static Method: send_dump(token, converted_payload, original_payload, client, ACCESS_TOKEN_1)

- Validates the payload before sending it further.
- Required field: "deviceID"
- If valid:
  - Calls data_push_class.check_for_CV_TV() from data_push_controller.
  - Passes token, parsed JSON payload, raw payload string, MQTT client instance, and access token.
- If invalid:
  - Prints “Payload formate was NOT right.”
- Wraps logic in a try/except block to prevent crashes from unexpected input.

Dependencies:

- data_push_controller.data_push_class → This module performs deeper validation, categorization, and handling of telemetry data.
- Receives resources from mqtt_Controller such as:
  - converted_payload (JSON)
  - original_payload (string)
  - client (MQTT client reference)
  - ACCESS_TOKEN_1 (authentication token)

Notes:

- The logic is lightweight by design: only routing, minor validation, and handoff to the next processing layer.
- Topic patterns can be extended easily (e.g., multi-device support, new groups like “alerts”, “status”, etc.).
- Helps maintain separation of concerns by keeping message routing independent of payload-processing logic.
