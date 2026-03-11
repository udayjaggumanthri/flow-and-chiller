import asyncio
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable, Optional, Tuple

import httpx

from app.config import get_settings
from app.models.schemas import GatewayData

logger = logging.getLogger(__name__)


@dataclass
class TelemetryResult:
    gateway_topic: str
    token: Optional[str]
    success: bool
    status_code: Optional[int] = None
    error: Optional[str] = None


def _extract_token_from_topic(topic: str) -> str:
    """
    Derive a ThingsBoard token.

    Priority:
    1) If a fixed THINGSBOARD_DEVICE_TOKEN is configured, always use that. This
       is the common case when a single ThingsBoard device represents many
       meters behind a gateway.
    2) Otherwise, try to extract a token from the MQTT topic using the
       configured regex.
    3) Finally, fall back to using the full topic as the token.

    This loosely mimics the legacy behavior where a suffix of the topic was
    interpreted as the token, but makes the actual pattern configurable.
    """
    settings = get_settings()

    # 1) Fixed device token for all telemetry.
    if settings.telemetry.device_token:
        return settings.telemetry.device_token

    # 2) Regex-based extraction from topic.
    pattern = settings.telemetry.token_from_topic_regex
    if pattern:
        match = re.match(pattern, topic)
        if not match:
            logger.warning(
                "token_from_topic_regex did not match topic '%s'; falling back to full topic as token",
                topic,
            )
            return topic

        token = match.groupdict().get("token")
        if not token:
            logger.warning(
                "token_from_topic_regex for topic '%s' did not expose a 'token' group; falling back to full topic",
                topic,
            )
            return topic
        return token

    # 3) Default: use the topic itself.
    return topic


def _sanitize_token(value: str) -> str:
    """ThingsBoard device token: alphanumeric only (e.g. 11A, 12B)."""
    cleaned = re.sub(r"[^0-9A-Za-z]+", "", value)
    return cleaned or "unknown"


def _build_meter_payload(meter, timestamp: datetime, connected: bool = True) -> Dict:
    """
    One row for Entity Table: meter | flow rate | Total consumption.
    Sent to ThingsBoard as telemetry keys: flow_rate, total_consumption, connected, timestamp.
    """
    payload: Dict = {
        "flow_rate": meter.flow_rate,
        "total_consumption": meter.total_consumption,
        "connected": connected,
        "timestamp": timestamp.isoformat(),
    }
    return payload


def _build_inactive_meter_payload(timestamp: datetime) -> Dict:
    """Payload to mark a meter as inactive (no recent MQTT)."""
    return {
        "connected": False,
        "timestamp": timestamp.isoformat(),
    }


def _build_thingsboard_payload(gateway: GatewayData) -> Dict:
    """
    Build a generic ThingsBoard-compatible telemetry payload from a GatewayData
    object (one device per gateway or single device with flattened keys).
    """
    def sanitize_key_part(value: str) -> str:
        cleaned = re.sub(r"[^0-9A-Za-z]+", "_", value).strip("_")
        return cleaned or "unknown"

    payload: Dict[str, object] = {
        "device_id": gateway.device_id,
        "rssi": gateway.rssi,
        "connected": True,
        "timestamp": gateway.timestamp.isoformat(),
    }

    for meter in gateway.meters:
        meter_id = sanitize_key_part(meter.meter_id)
        payload[f"m_{meter_id}_flow_rate"] = meter.flow_rate
        payload[f"m_{meter_id}_total_consumption"] = meter.total_consumption

    return payload


def publish_gateway_telemetry_sync(gateway: GatewayData) -> TelemetryResult:
    """
    Synchronous version of telemetry push for use from MQTT callback thread
    (no asyncio event loop available there). Same logic as async version.
    """
    settings = get_settings()
    if not settings.telemetry.enable_push:
        logger.debug(
            "Telemetry push is disabled; skipping gateway %s", gateway.gateway_topic
        )
        return TelemetryResult(
            gateway_topic=gateway.gateway_topic,
            token=None,
            success=False,
            error="Telemetry push disabled",
        )

    if not settings.telemetry.base_url:
        logger.error(
            "Telemetry base URL is not configured; cannot push telemetry for %s",
            gateway.gateway_topic,
        )
        return TelemetryResult(
            gateway_topic=gateway.gateway_topic,
            token=None,
            success=False,
            error="Telemetry base URL not configured",
        )

    base = settings.telemetry.base_url.rstrip("/")
    timeout = settings.telemetry.timeout_seconds

    if settings.telemetry.one_device_per_meter:
        # Push all meters in parallel so ThingsBoard updates with minimal delay (one round-trip instead of N)
        def _post_one_meter(
            meter, url: str, payload_dict: Dict
        ) -> Tuple[str, bool, Optional[int], Optional[str]]:
            try:
                with httpx.Client(timeout=timeout) as client:
                    response = client.post(url, json=payload_dict)
                if response.status_code == 200:
                    return (meter.meter_id, True, 200, None)
                return (
                    meter.meter_id,
                    False,
                    response.status_code,
                    response.text or f"HTTP {response.status_code}",
                )
            except Exception as exc:
                return (meter.meter_id, False, None, str(exc))

        tasks = []
        for meter in gateway.meters:
            token = _sanitize_token(meter.meter_id)
            url = f"{base}/api/v1/{token}/telemetry"
            payload_dict = _build_meter_payload(meter, gateway.timestamp)
            tasks.append((meter, url, payload_dict))

        max_workers = min(len(tasks), 20)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(_post_one_meter, m, u, p): (m, u, p)
                for m, u, p in tasks
            }
            for future in as_completed(futures):
                meter_id, ok, status_code, err = future.result()
                if not ok:
                    logger.error(
                        "Failed to send telemetry for meter %s (topic %s): %s",
                        meter_id,
                        gateway.gateway_topic,
                        err,
                    )
                    return TelemetryResult(
                        gateway_topic=gateway.gateway_topic,
                        token=meter_id,
                        success=False,
                        status_code=status_code,
                        error=err or "Request failed",
                    )
        logger.debug(
            "Successfully sent telemetry for %d meters (topic %s)",
            len(gateway.meters),
            gateway.gateway_topic,
        )
        last_token = _sanitize_token(gateway.meters[-1].meter_id) if gateway.meters else None
        return TelemetryResult(
            gateway_topic=gateway.gateway_topic,
            token=last_token,
            success=True,
            status_code=200,
        )
    else:
        token = _extract_token_from_topic(gateway.gateway_topic)
        url = f"{base}/api/v1/{token}/telemetry"
        payload_dict = _build_thingsboard_payload(gateway)
        with httpx.Client(timeout=timeout) as client:
            try:
                response = client.post(url, json=payload_dict)
            except httpx.RequestError as exc:
                logger.error(
                    "Error while sending telemetry for topic %s to %s: %s",
                    gateway.gateway_topic,
                    url,
                    exc,
                )
                return TelemetryResult(
                    gateway_topic=gateway.gateway_topic,
                    token=token,
                    success=False,
                    error=str(exc),
                )
        if response.status_code == 200:
            logger.info(
                "Successfully sent telemetry for topic %s to %s",
                gateway.gateway_topic,
                url,
            )
            return TelemetryResult(
                gateway_topic=gateway.gateway_topic,
                token=token,
                success=True,
                status_code=response.status_code,
            )
        logger.error(
            "Failed to send telemetry for topic %s to %s. Status code: %s, body: %s",
            gateway.gateway_topic,
            url,
            response.status_code,
            response.text,
        )
        return TelemetryResult(
            gateway_topic=gateway.gateway_topic,
            token=token,
            success=False,
            status_code=response.status_code,
            error=f"HTTP {response.status_code}",
        )


def publish_gateway_inactive_sync(gateway: GatewayData) -> TelemetryResult:
    """
    Push connected=False (and timestamp) to ThingsBoard for a gateway that has
    been silent past the inactivity threshold. Call from the inactivity check task.
    """
    settings = get_settings()
    if not settings.telemetry.enable_push or not settings.telemetry.base_url:
        return TelemetryResult(
            gateway_topic=gateway.gateway_topic,
            token=None,
            success=True,
            error="Push disabled or no base URL",
        )
    base = settings.telemetry.base_url.rstrip("/")
    timeout = settings.telemetry.timeout_seconds
    now = datetime.now(timezone.utc)

    if settings.telemetry.one_device_per_meter:
        def _post_inactive(meter, url: str, payload_dict: Dict) -> Tuple[str, bool, Optional[int], Optional[str]]:
            try:
                with httpx.Client(timeout=timeout) as client:
                    response = client.post(url, json=payload_dict)
                if response.status_code == 200:
                    return (meter.meter_id, True, 200, None)
                return (meter.meter_id, False, response.status_code, response.text or f"HTTP {response.status_code}")
            except Exception as exc:
                return (meter.meter_id, False, None, str(exc))

        tasks = []
        for meter in gateway.meters:
            token = _sanitize_token(meter.meter_id)
            url = f"{base}/api/v1/{token}/telemetry"
            payload_dict = _build_inactive_meter_payload(now)
            tasks.append((meter, url, payload_dict))

        with ThreadPoolExecutor(max_workers=min(len(tasks), 20)) as executor:
            futures = {executor.submit(_post_inactive, m, u, p): m for m, u, p in tasks}
            for future in as_completed(futures):
                meter_id, ok, status_code, err = future.result()
                if not ok:
                    logger.warning(
                        "Failed to send inactive for meter %s (topic %s): %s",
                        meter_id, gateway.gateway_topic, err,
                    )
                    return TelemetryResult(
                        gateway_topic=gateway.gateway_topic,
                        token=meter_id,
                        success=False,
                        status_code=status_code,
                        error=err or "Request failed",
                    )
        logger.debug(
            "Sent inactive for %d meters (topic %s)",
            len(gateway.meters), gateway.gateway_topic,
        )
        last_token = _sanitize_token(gateway.meters[-1].meter_id) if gateway.meters else None
        return TelemetryResult(
            gateway_topic=gateway.gateway_topic,
            token=last_token,
            success=True,
            status_code=200,
        )
    else:
        token = _extract_token_from_topic(gateway.gateway_topic)
        url = f"{base}/api/v1/{token}/telemetry"
        payload_dict = _build_inactive_meter_payload(now)
        with httpx.Client(timeout=timeout) as client:
            try:
                response = client.post(url, json=payload_dict)
            except httpx.RequestError as exc:
                logger.warning(
                    "Error sending inactive for topic %s: %s",
                    gateway.gateway_topic, exc,
                )
                return TelemetryResult(
                    gateway_topic=gateway.gateway_topic,
                    token=token,
                    success=False,
                    error=str(exc),
                )
        if response.status_code == 200:
            logger.debug("Sent inactive for topic %s", gateway.gateway_topic)
            return TelemetryResult(
                gateway_topic=gateway.gateway_topic,
                token=token,
                success=True,
                status_code=response.status_code,
            )
        return TelemetryResult(
            gateway_topic=gateway.gateway_topic,
            token=token,
            success=False,
            status_code=response.status_code,
            error=f"HTTP {response.status_code}",
        )


async def publish_gateway_telemetry(gateway: GatewayData) -> TelemetryResult:
    """
    Publish telemetry for a single gateway to the configured ThingsBoard-style
    backend. Returns a TelemetryResult describing the outcome.
    """
    settings = get_settings()
    if not settings.telemetry.enable_push:
        logger.debug(
            "Telemetry push is disabled; skipping gateway %s", gateway.gateway_topic
        )
        return TelemetryResult(
            gateway_topic=gateway.gateway_topic,
            token=None,
            success=False,
            error="Telemetry push disabled",
        )

    if not settings.telemetry.base_url:
        logger.error(
            "Telemetry base URL is not configured; cannot push telemetry for %s",
            gateway.gateway_topic,
        )
        return TelemetryResult(
            gateway_topic=gateway.gateway_topic,
            token=None,
            success=False,
            error="Telemetry base URL not configured",
        )

    base = settings.telemetry.base_url.rstrip("/")
    timeout = settings.telemetry.timeout_seconds

    if settings.telemetry.one_device_per_meter:
        urls_payloads = [
            (
                meter.meter_id,
                f"{base}/api/v1/{_sanitize_token(meter.meter_id)}/telemetry",
                _build_meter_payload(meter, gateway.timestamp),
            )
            for meter in gateway.meters
        ]
        async with httpx.AsyncClient(timeout=timeout) as client:
            tasks = [client.post(url, json=payload) for _, url, payload in urls_payloads]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        for (meter_id, _, _), r in zip(urls_payloads, results):
            if isinstance(r, Exception):
                logger.exception(
                    "Error sending telemetry for meter %s (topic %s): %s",
                    meter_id,
                    gateway.gateway_topic,
                    r,
                )
                return TelemetryResult(
                    gateway_topic=gateway.gateway_topic,
                    token=meter_id,
                    success=False,
                    error=str(r),
                )
            if r.status_code != 200:
                logger.error(
                    "Failed to send telemetry for meter %s. Status: %s, body: %s",
                    meter_id,
                    r.status_code,
                    r.text,
                )
                return TelemetryResult(
                    gateway_topic=gateway.gateway_topic,
                    token=meter_id,
                    success=False,
                    status_code=r.status_code,
                    error=f"HTTP {r.status_code}",
                )
        logger.debug(
            "Successfully sent telemetry for %d meters (topic %s)",
            len(gateway.meters),
            gateway.gateway_topic,
        )
        last_token = _sanitize_token(gateway.meters[-1].meter_id) if gateway.meters else None
        return TelemetryResult(
            gateway_topic=gateway.gateway_topic,
            token=last_token,
            success=True,
            status_code=200,
        )
    else:
        token = _extract_token_from_topic(gateway.gateway_topic)
        url = f"{base}/api/v1/{token}/telemetry"
        payload_dict = _build_thingsboard_payload(gateway)
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.post(url, json=payload_dict)
            except httpx.RequestError as exc:
                logger.error(
                    "Error while sending telemetry for topic %s to %s: %s",
                    gateway.gateway_topic,
                    url,
                    exc,
                )
                return TelemetryResult(
                    gateway_topic=gateway.gateway_topic,
                    token=token,
                    success=False,
                    error=str(exc),
                )
        if response.status_code == 200:
            logger.info(
                "Successfully sent telemetry for topic %s to %s",
                gateway.gateway_topic,
                url,
            )
            return TelemetryResult(
                gateway_topic=gateway.gateway_topic,
                token=token,
                success=True,
                status_code=response.status_code,
            )
        logger.error(
            "Failed to send telemetry for topic %s to %s. Status code: %s, body: %s",
            gateway.gateway_topic,
            url,
            response.status_code,
            response.text,
        )
        return TelemetryResult(
            gateway_topic=gateway.gateway_topic,
            token=token,
            success=False,
            status_code=response.status_code,
            error=f"HTTP {response.status_code}",
        )


async def publish_multiple_gateways_telemetry(
    gateways: Iterable[GatewayData],
) -> Dict[str, TelemetryResult]:
    """
    Publish telemetry for multiple gateways. Returns a mapping from gateway
    topic to TelemetryResult.
    """
    tasks = [publish_gateway_telemetry(g) for g in gateways]
    results_list = await asyncio.gather(*tasks, return_exceptions=False)
    return {r.gateway_topic: r for r in results_list}

