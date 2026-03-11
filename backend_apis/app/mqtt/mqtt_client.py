import json
import logging
import threading
from datetime import datetime, timezone
from typing import Dict, Optional
from uuid import uuid4

import paho.mqtt.client as mqtt

from app.config import get_settings
from app.models.schemas import GatewayData
from app.services.data_parser import parse_mqtt_payload
from app.services.telemetry_publisher import publish_gateway_telemetry_sync

logger = logging.getLogger(__name__)


_client: Optional[mqtt.Client] = None
_latest_data: Dict[str, GatewayData] = {}
_lock = threading.Lock()


def get_latest_data_snapshot() -> Dict[str, GatewayData]:
    """
    Return a shallow copy of the latest data dictionary for safe read access.
    """
    with _lock:
        return dict(_latest_data)


def _on_connect(client: mqtt.Client, userdata, flags, rc, properties=None) -> None:
    settings = get_settings()

    if rc == 0:
        logger.info("Connected to MQTT broker successfully")
        topic_pattern = settings.mqtt.topic_pattern
        qos = settings.mqtt.qos
        try:
            result, mid = client.subscribe(topic_pattern, qos=qos)
        except ValueError as exc:
            logger.error(
                "Invalid MQTT subscription filter '%s': %s. "
                "Please configure a valid MQTT_TOPIC_PATTERN (e.g. '#', 'fm/#', or 'some/prefix/#').",
                topic_pattern,
                exc,
            )
            return

        if result == mqtt.MQTT_ERR_SUCCESS:
            logger.info(
                "Subscribed to MQTT topic pattern '%s' with QoS %s",
                topic_pattern,
                qos,
            )
        else:
            logger.error(
                "Failed to subscribe to MQTT topic pattern '%s' (result: %s)",
                topic_pattern,
                result,
            )
    else:
        logger.error("Failed to connect to MQTT broker (rc=%s)", rc)


def _on_disconnect(client: mqtt.Client, userdata, rc) -> None:
    if rc != 0:
        logger.warning("Unexpected MQTT disconnection (rc=%s). Client will attempt to reconnect.", rc)
    else:
        logger.info("MQTT client disconnected cleanly.")


def _on_message(client: mqtt.Client, userdata, msg: mqtt.MQTTMessage) -> None:
    topic = msg.topic
    payload_bytes = msg.payload

    try:
        payload_str = payload_bytes.decode("utf-8")
        data = json.loads(payload_str)
    except UnicodeDecodeError:
        logger.exception("Failed to decode MQTT payload on topic %s as UTF-8", topic)
        return
    except json.JSONDecodeError:
        logger.exception("Failed to decode MQTT payload on topic %s as JSON", topic)
        return

    received_at = datetime.now(timezone.utc)
    gateway_data = parse_mqtt_payload(
        topic=topic, payload=data, received_at=received_at
    )

    if gateway_data is None:
        logger.warning("Parsed MQTT payload on topic %s resulted in no usable data", topic)
        return

    with _lock:
        _latest_data[topic] = gateway_data

    logger.debug("Updated latest data for topic %s", topic)

    settings = get_settings()
    if settings.telemetry.enable_push and settings.telemetry.enable_auto_push:
        # Use sync HTTP from MQTT thread (no asyncio loop here).
        try:
            publish_gateway_telemetry_sync(gateway_data)
        except Exception:
            logger.exception(
                "Auto-push telemetry failed for topic %s",
                topic,
            )


def start_mqtt() -> None:
    """
    Initialize and start the MQTT client in a background network loop.
    Intended to be called from FastAPI startup.
    """
    global _client

    if _client is not None:
        logger.info("MQTT client already started; skipping initialization.")
        return

    settings = get_settings()

    client_id = f"{settings.mqtt.client_id_prefix}-{uuid4().hex[:8]}"
    client = mqtt.Client(client_id=client_id, clean_session=True)

    if settings.mqtt.username:
        client.username_pw_set(settings.mqtt.username, settings.mqtt.password)

    client.on_connect = _on_connect
    client.on_disconnect = _on_disconnect
    client.on_message = _on_message

    # Configure automatic reconnect delays
    client.reconnect_delay_set(min_delay=1, max_delay=120)

    try:
        client.connect_async(settings.mqtt.host, settings.mqtt.port, keepalive=settings.mqtt.keepalive)
    except Exception:
        logger.exception(
            "Error while initiating connection to MQTT broker at %s:%s",
            settings.mqtt.host,
            settings.mqtt.port,
        )
        return

    client.loop_start()
    _client = client
    logger.info(
        "MQTT client started with client_id=%s, connecting to %s:%s",
        client_id,
        settings.mqtt.host,
        settings.mqtt.port,
    )


def stop_mqtt() -> None:
    """
    Stop the MQTT client background loop and disconnect from the broker.
    Intended to be called from FastAPI shutdown.
    """
    global _client

    if _client is None:
        logger.info("MQTT client is not running; nothing to stop.")
        return

    try:
        _client.loop_stop()
        _client.disconnect()
        logger.info("MQTT client loop stopped and disconnected.")
    except Exception:
        logger.exception("Error while stopping MQTT client.")
    finally:
        _client = None

