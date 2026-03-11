"""
ThingsBoard REST API client for telemetry download.

This module is decoupled from FastAPI: it only performs HTTP calls and returns
raw data. Used by the download router to fetch historical telemetry.
"""
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


def get_auth_token(
    base_url: str,
    username: str,
    password: str,
    timeout: float = 30.0,
) -> str:
    """
    Authenticate with ThingsBoard and return the JWT token.
    """
    url = f"{base_url.rstrip('/')}/api/auth/login"
    payload = {"username": username, "password": password}
    with httpx.Client(timeout=timeout) as client:
        response = client.post(url, json=payload)
    response.raise_for_status()
    data = response.json()
    token = data.get("token")
    if not token:
        raise ValueError("ThingsBoard login response did not contain token")
    return token


def get_timeseries(
    base_url: str,
    token: str,
    device_id: str,
    keys: Optional[List[str]] = None,
    start_ts: Optional[int] = None,
    end_ts: Optional[int] = None,
    interval_ms: int = 0,
    limit: int = 100_000,
    timeout: float = 30.0,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Fetch telemetry time series for a device from ThingsBoard.

    Returns the raw API response: { "key1": [{"ts": ms, "value": v}, ...], ... }.
    """
    base = base_url.rstrip("/")
    url = (
        f"{base}/api/plugins/telemetry/DEVICE/{device_id}/values/timeseries"
    )
    params: Dict[str, Any] = {
        "startTs": start_ts,
        "endTs": end_ts,
        "interval": interval_ms,
        "limit": limit,
        "agg": "NONE",
        "orderBy": "ASC",
    }
    if keys:
        params["keys"] = ",".join(keys)
    headers = {"X-Authorization": f"Bearer {token}"}
    with httpx.Client(timeout=timeout) as client:
        response = client.get(url, params=params, headers=headers)
    response.raise_for_status()
    return response.json()


def get_device_name(
    base_url: str,
    token: str,
    device_id: str,
    timeout: float = 30.0,
) -> str:
    """
    Resolve ThingsBoard device UUID -> device name.
    GET /api/device/{deviceId}
    """
    base = base_url.rstrip("/")
    url = f"{base}/api/device/{device_id}"
    headers = {"X-Authorization": f"Bearer {token}"}
    with httpx.Client(timeout=timeout) as client:
        response = client.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    name = data.get("name")
    if not name:
        raise ValueError(f"ThingsBoard device {device_id} response missing 'name'")
    return str(name)


def get_device_names(
    base_url: str,
    username: str,
    password: str,
    device_ids: List[str],
    timeout: float = 30.0,
) -> Dict[str, str]:
    """
    Resolve multiple device UUIDs to names using login credentials.
    Returns mapping {device_id: device_name}.
    """
    if not device_ids:
        return {}
    jwt_token = get_auth_token(base_url, username, password, timeout)
    out: Dict[str, str] = {}
    for did in device_ids:
        try:
            out[did] = get_device_name(base_url, jwt_token, did, timeout=timeout)
        except Exception as e:
            logger.warning("Failed to resolve device name for %s: %s", did[:8] + "...", e)
            out[did] = did
    return out


def set_device_server_attributes(
    base_url: str,
    token: str,
    device_id: str,
    attributes: Dict[str, Any],
    timeout: float = 30.0,
) -> None:
    """
    Set server-side attributes on a device (e.g. inactivityTimeout in milliseconds).
    POST /api/plugins/telemetry/DEVICE/{deviceId}/attributes/SERVER_SCOPE
    """
    base = base_url.rstrip("/")
    url = f"{base}/api/plugins/telemetry/DEVICE/{device_id}/attributes/SERVER_SCOPE"
    headers = {"X-Authorization": f"Bearer {token}"}
    with httpx.Client(timeout=timeout) as client:
        response = client.post(url, json=attributes, headers=headers)
    response.raise_for_status()


def set_devices_inactivity_timeout(
    base_url: str,
    username: str,
    password: str,
    device_ids: List[str],
    timeout_seconds: float,
    timeout: float = 30.0,
) -> List[Tuple[str, Optional[str]]]:
    """
    Set inactivityTimeout (in ms) on each device so ThingsBoard marks them
    Inactive after timeout_seconds with no telemetry. Returns list of
    (device_id, error_message); empty error means success.
    """
    if not device_ids or timeout_seconds <= 0:
        return []
    jwt_token = get_auth_token(base_url, username, password, timeout)
    inactivity_ms = int(timeout_seconds * 1000)
    results: List[Tuple[str, Optional[str]]] = []
    for device_id in device_ids:
        try:
            set_device_server_attributes(
                base_url=base_url,
                token=jwt_token,
                device_id=device_id,
                attributes={"inactivityTimeout": inactivity_ms},
                timeout=timeout,
            )
            results.append((device_id, None))
            logger.info(
                "Set device %s inactivityTimeout=%s ms (%.1f s)",
                device_id[:8] + "...",
                inactivity_ms,
                timeout_seconds,
            )
        except Exception as e:
            msg = str(e)
            results.append((device_id, msg))
            logger.warning(
                "Failed to set inactivityTimeout for device %s: %s",
                device_id[:8] + "...",
                msg,
            )
    return results


def fetch_telemetry_for_download(
    device_ids: Optional[List[str]] = None,
    keys: Optional[List[str]] = None,
    start_ts: Optional[int] = None,
    end_ts: Optional[int] = None,
    interval_ms: int = 0,
    limit: int = 100_000,
) -> Union[Dict[str, List[Dict[str, Any]]], List[Tuple[str, Dict[str, List[Dict[str, Any]]]]]]:
    """
    Use app settings to authenticate and fetch timeseries.
    Returns single-device dict, or list of (device_id, data) when device_ids is provided
    or when THINGSBOARD_DEVICE_IDS is set.
    Raises ValueError if download is not configured.
    """
    settings = get_settings()
    cfg = settings.thingsboard_download
    if not cfg.base_url or not cfg.username or not cfg.password:
        raise ValueError(
            "ThingsBoard download not configured: set THINGSBOARD_BASE_URL, "
            "THINGSBOARD_USERNAME, THINGSBOARD_PASSWORD."
        )
    token = get_auth_token(
        cfg.base_url, cfg.username, cfg.password, cfg.timeout_seconds
    )

    effective_device_ids = device_ids if device_ids is not None else cfg.device_ids
    if effective_device_ids:
        result: List[Tuple[str, Dict[str, List[Dict[str, Any]]]]] = []
        for did in effective_device_ids:
            data = get_timeseries(
                base_url=cfg.base_url,
                token=token,
                device_id=did,
                keys=keys,
                start_ts=start_ts,
                end_ts=end_ts,
                interval_ms=interval_ms,
                limit=limit,
                timeout=cfg.timeout_seconds,
            )
            result.append((did, data))
        return result
    if not cfg.device_id:
        raise ValueError(
            "ThingsBoard download needs THINGSBOARD_DEVICE_ID or THINGSBOARD_DEVICE_IDS."
        )
    return get_timeseries(
        base_url=cfg.base_url,
        token=token,
        device_id=cfg.device_id,
        keys=keys,
        start_ts=start_ts,
        end_ts=end_ts,
        interval_ms=interval_ms,
        limit=limit,
        timeout=cfg.timeout_seconds,
    )
