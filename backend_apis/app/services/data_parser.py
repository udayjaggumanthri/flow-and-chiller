import logging
from datetime import datetime
from typing import Any, Dict, Optional

from app.models.schemas import GatewayData, MeterReading

logger = logging.getLogger(__name__)


RESERVED_KEYS = {"deviceID", "RSSI"}


def _is_numeric(value: Any) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def parse_mqtt_payload(
    topic: str, payload: Dict[str, Any], received_at: datetime
) -> Optional[GatewayData]:
    """
    Normalize a raw MQTT payload from a gateway into a GatewayData model.

    Expected payload structure example:
    {
      "deviceID": "AKZ6016E0",
      "RSSI": -77,
      "1A": [421.79, 420.06],
      "1B": [3892, 975],
      ...
    }
    """
    device_id = payload.get("deviceID")
    rssi = payload.get("RSSI")

    if device_id is None:
        logger.warning("Received payload on topic %s without deviceID", topic)
        return None

    if rssi is None:
        logger.warning("Received payload on topic %s without RSSI", topic)
        return None

    meters: list[MeterReading] = []

    for key, value in payload.items():
        if key in RESERVED_KEYS:
            continue

        if not isinstance(value, (list, tuple)) or len(value) < 2:
            logger.debug(
                "Skipping key %s on topic %s: expected list/tuple with at least 2 items",
                key,
                topic,
            )
            continue

        flow_rate_raw, total_consumption_raw = value[0], value[1]

        if not (_is_numeric(flow_rate_raw) and _is_numeric(total_consumption_raw)):
            logger.debug(
                "Skipping key %s on topic %s: non-numeric readings %r",
                key,
                topic,
                value,
            )
            continue

        meter = MeterReading(
            meter_id=str(key),
            flow_rate=float(flow_rate_raw),
            total_consumption=float(total_consumption_raw),
        )
        meters.append(meter)

    if not meters:
        logger.info(
            "No valid meters found in payload on topic %s for device %s",
            topic,
            device_id,
        )

    gateway_data = GatewayData(
        gateway_topic=topic,
        device_id=str(device_id),
        rssi=int(rssi),
        meters=meters,
        timestamp=received_at,
    )

    return gateway_data

