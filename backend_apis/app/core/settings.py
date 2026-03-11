"""
Centralized settings definition and loading.

This module is the new canonical location for application configuration.
`app.config` remains as a compatibility shim.
"""

import os
from functools import lru_cache
from typing import List, Optional

from pydantic import BaseModel, Field

from app.db import SessionLocal
from app.models.db_models import SystemSettings


class MQTTSettings(BaseModel):
    host: str = Field(default="localhost", description="MQTT broker hostname or IP")
    port: int = Field(default=1883, description="MQTT broker port")
    username: Optional[str] = Field(
        default=None, description="MQTT username, if authentication is enabled"
    )
    password: Optional[str] = Field(
        default=None, description="MQTT password, if authentication is enabled"
    )
    client_id_prefix: str = Field(
        default="gateway_service", description="Prefix for MQTT client IDs"
    )
    keepalive: int = Field(default=60, description="MQTT keepalive interval in seconds")
    topic_pattern: str = Field(
        default="#",
        description="MQTT subscription topic pattern (supports wildcards). "
        "Use '#' for all topics and filter by prefix in the application, "
        "or provide a valid filter such as 'fm/#'.",
    )
    qos: int = Field(default=1, description="MQTT QoS level for subscriptions")


class TelemetrySettings(BaseModel):
    base_url: Optional[str] = Field(
        default=None,
        description=(
            "Base URL of the ThingsBoard-style backend, "
            "e.g. https://thingsboard.example.com"
        ),
    )
    enable_push: bool = Field(
        default=False,
        description="If true, telemetry push to the external backend is enabled.",
    )
    enable_auto_push: bool = Field(
        default=False,
        description=(
            "If true, telemetry is pushed automatically from the MQTT ingestion "
            "flow whenever new gateway data is received."
        ),
    )
    timeout_seconds: float = Field(
        default=5.0,
        description="HTTP request timeout for telemetry pushes, in seconds.",
    )
    device_token: Optional[str] = Field(
        default=None,
        description=(
            "If set, this ThingsBoard device access token is used for ALL telemetry, "
            "regardless of MQTT topic. Use this when multiple meters belong to a "
            "single logical device in ThingsBoard."
        ),
    )
    token_from_topic_regex: Optional[str] = Field(
        default=None,
        description=(
            "Optional regex used to extract a ThingsBoard token from the MQTT "
            "topic. If provided, it should contain a named group 'token', e.g. "
            "'.*(?P<token>\\w{5})$'. If not set, the full topic is used as the token."
        ),
    )
    one_device_per_meter: bool = Field(
        default=False,
        description=(
            "If true, each meter (e.g. 11A, 11B, 11C) is pushed as a separate "
            "ThingsBoard device with token = meter_id. Use for Entity Table with "
            "one row per meter (meter | flow rate | power consumption). "
            "If false, one device per gateway or one single device with flattened keys."
        ),
    )
    push_interval_seconds: float = Field(
        default=0.0,
        description=(
            "If > 0, push latest snapshot to ThingsBoard every N seconds so dashboards "
            "get fresh points for 'Realtime - last 1 minute' and line charts. "
            "Use e.g. 15 when MQTT messages are infrequent."
        ),
    )
    inactivity_minutes: float = Field(
        default=0.0,
        description=(
            "If > 0, when a gateway has not sent MQTT for this many minutes, "
            "push connected=false to ThingsBoard so device status shows inactive. "
            "Use e.g. 5 for 5 minutes."
        ),
    )
    inactivity_check_interval_seconds: float = Field(
        default=60.0,
        description="How often to check for inactive gateways (seconds). Used when inactivity_minutes > 0.",
    )
    inactivity_timeout_seconds: float = Field(
        default=0.0,
        description=(
            "If > 0, set ThingsBoard device server attribute 'inactivityTimeout' (in ms) so "
            "devices show Inactive soon after MQTT stops. Uses download credentials and "
            "THINGSBOARD_DEVICE_ID / THINGSBOARD_DEVICE_IDS. E.g. 60 for realtime (1 min)."
        ),
    )


class ThingsBoardDownloadSettings(BaseModel):
    """
    Settings for downloading historical telemetry from ThingsBoard.
    Kept separate from TelemetrySettings (push) for loose coupling.
    """

    base_url: Optional[str] = Field(
        default=None,
        description="ThingsBoard base URL for API (e.g. http://host:8080).",
    )
    username: Optional[str] = Field(
        default=None,
        description="ThingsBoard login username (e.g. tenant@thingsboard.org).",
    )
    password: Optional[str] = Field(
        default=None,
        description="ThingsBoard login password.",
    )
    device_id: Optional[str] = Field(
        default=None,
        description=(
            "Single ThingsBoard device UUID for telemetry download. "
            "Ignored if device_ids is set."
        ),
    )
    device_ids: List[str] = Field(
        default_factory=list,
        description=(
            "Multiple device UUIDs for download (e.g. one per meter). "
            "Set via THINGSBOARD_DEVICE_IDS, comma-separated. Overrides device_id when non-empty."
        ),
    )
    timeout_seconds: float = Field(
        default=30.0,
        description="HTTP timeout for ThingsBoard API calls.",
    )


class AppSettings(BaseModel):
    app_name: str = Field(default="MQTT Gateway API", description="FastAPI app title")
    log_level: str = Field(
        default="INFO", description="Application log level (DEBUG, INFO, etc.)"
    )


class Settings(BaseModel):
    mqtt: MQTTSettings = MQTTSettings()
    app: AppSettings = AppSettings()
    telemetry: TelemetrySettings = TelemetrySettings()
    thingsboard_download: ThingsBoardDownloadSettings = ThingsBoardDownloadSettings()


def _get_bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@lru_cache
def get_settings() -> Settings:
    """
    Return application settings.

    Priority:
    1. If a row exists in Postgres (system_settings), use it.
    2. Otherwise, fall back to environment variables.
    """
    # Try DB first
    try:
        db = SessionLocal()
        row = db.query(SystemSettings).first()
    except Exception:
        row = None
    finally:
        try:
            db.close()
        except Exception:
            pass

    if row:
        mqtt_settings = MQTTSettings(
            host=row.mqtt_host,
            port=row.mqtt_port,
            username=row.mqtt_username or None,
            password=row.mqtt_password or None,
            client_id_prefix=row.mqtt_client_id_prefix,
            keepalive=row.mqtt_keepalive,
            topic_pattern=row.mqtt_topic_pattern,
            qos=row.mqtt_qos,
        )

        app_settings = AppSettings(
            app_name=os.getenv("APP_NAME", "MQTT Gateway API"),
            log_level=os.getenv("APP_LOG_LEVEL", "INFO"),
        )

        telemetry_settings = TelemetrySettings(
            base_url=row.tb_base_url or None,
            enable_push=row.tb_enable_push,
            enable_auto_push=row.tb_enable_auto_push,
            timeout_seconds=float(row.tb_timeout_seconds),
            device_token=row.tb_device_token or None,
            token_from_topic_regex=row.tb_token_from_topic_regex or None,
            one_device_per_meter=row.tb_one_device_per_meter,
            push_interval_seconds=float(row.tb_push_interval_seconds),
            inactivity_minutes=float(row.tb_inactivity_minutes),
            inactivity_check_interval_seconds=float(
                row.tb_inactivity_check_interval_seconds
            ),
            inactivity_timeout_seconds=float(row.tb_inactivity_timeout_seconds),
        )

        tb_ids = []
        if row.tb_device_ids:
            tb_ids = [x.strip() for x in row.tb_device_ids.split(",") if x.strip()]
        tb_download = ThingsBoardDownloadSettings(
            base_url=row.tb_download_base_url or None,
            username=row.tb_username or None,
            password=row.tb_password or None,
            device_id=row.tb_device_id or None,
            device_ids=tb_ids,
            timeout_seconds=float(row.tb_download_timeout_seconds),
        )

        return Settings(
            mqtt=mqtt_settings,
            app=app_settings,
            telemetry=telemetry_settings,
            thingsboard_download=tb_download,
        )

    # Fallback: environment variables
    mqtt_settings = MQTTSettings(
        host=os.getenv("MQTT_HOST", "localhost"),
        port=int(os.getenv("MQTT_PORT", "1883")),
        username=os.getenv("MQTT_USERNAME") or None,
        password=os.getenv("MQTT_PASSWORD") or None,
        client_id_prefix=os.getenv("MQTT_CLIENT_ID_PREFIX", "gateway_service"),
        keepalive=int(os.getenv("MQTT_KEEPALIVE", "60")),
        topic_pattern=os.getenv("MQTT_TOPIC_PATTERN", "#"),
        qos=int(os.getenv("MQTT_QOS", "1")),
    )

    app_settings = AppSettings(
        app_name=os.getenv("APP_NAME", "MQTT Gateway API"),
        log_level=os.getenv("APP_LOG_LEVEL", "INFO"),
    )

    telemetry_settings = TelemetrySettings(
        base_url=os.getenv("THINGSBOARD_BASE_URL") or None,
        enable_push=_get_bool_env("ENABLE_TELEMETRY_PUSH", False),
        enable_auto_push=_get_bool_env("ENABLE_AUTO_TELEMETRY_PUSH", False),
        timeout_seconds=float(os.getenv("TELEMETRY_TIMEOUT_SECONDS", "5.0")),
        device_token=os.getenv("THINGSBOARD_DEVICE_TOKEN") or None,
        token_from_topic_regex=os.getenv("THINGSBOARD_TOKEN_FROM_TOPIC_REGEX") or None,
        one_device_per_meter=_get_bool_env("ONE_DEVICE_PER_METER", False),
        push_interval_seconds=float(os.getenv("TELEMETRY_PUSH_INTERVAL_SECONDS", "0")),
        inactivity_minutes=float(os.getenv("TELEMETRY_INACTIVITY_MINUTES", "0")),
        inactivity_check_interval_seconds=float(
            os.getenv("TELEMETRY_INACTIVITY_CHECK_INTERVAL_SECONDS", "60")
        ),
        inactivity_timeout_seconds=float(
            os.getenv("TELEMETRY_INACTIVITY_TIMEOUT_SECONDS", "0")
        ),
    )

    _device_ids_raw = os.getenv("THINGSBOARD_DEVICE_IDS") or ""
    _device_ids = [x.strip() for x in _device_ids_raw.split(",") if x.strip()]
    tb_download = ThingsBoardDownloadSettings(
        base_url=os.getenv("THINGSBOARD_BASE_URL") or None,
        username=os.getenv("THINGSBOARD_USERNAME") or None,
        password=os.getenv("THINGSBOARD_PASSWORD") or None,
        device_id=os.getenv("THINGSBOARD_DEVICE_ID") or None,
        device_ids=_device_ids,
        timeout_seconds=float(os.getenv("THINGSBOARD_DOWNLOAD_TIMEOUT_SECONDS", "30.0")),
    )

    return Settings(
        mqtt=mqtt_settings,
        app=app_settings,
        telemetry=telemetry_settings,
        thingsboard_download=tb_download,
    )

