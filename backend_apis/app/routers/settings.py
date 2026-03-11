import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import MQTTSettings, TelemetrySettings, ThingsBoardDownloadSettings
from app.db import get_db
from app.models.db_models import SystemSettings


router = APIRouter(prefix="/settings", tags=["settings"])


class VerifyPinBody(BaseModel):
    pin: str = ""


def _get_configured_pin() -> Optional[str]:
    raw = os.getenv("SETTINGS_PIN")
    if not raw or not raw.strip():
        return None
    return raw.strip()


@router.post("/verify-pin")
def verify_settings_pin(body: VerifyPinBody) -> dict:
    """
    Verify the settings PIN. If SETTINGS_PIN is not set in .env, access is allowed.
    Returns 200 on success, 401 if PIN does not match.
    """
    configured = _get_configured_pin()
    if configured is None:
        return {"ok": True}
    if body.pin.strip() != configured:
        raise HTTPException(status_code=401, detail="Invalid PIN")
    return {"ok": True}


class SettingsPayload(BaseModel):
    mqtt: MQTTSettings
    telemetry: TelemetrySettings
    thingsboard_download: ThingsBoardDownloadSettings


def _system_settings_to_payload(row: SystemSettings) -> SettingsPayload:
    mqtt = MQTTSettings(
        host=row.mqtt_host,
        port=row.mqtt_port,
        username=row.mqtt_username or None,
        password=row.mqtt_password or None,
        client_id_prefix=row.mqtt_client_id_prefix,
        keepalive=row.mqtt_keepalive,
        topic_pattern=row.mqtt_topic_pattern,
        qos=row.mqtt_qos,
    )
    telemetry = TelemetrySettings(
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
    download = ThingsBoardDownloadSettings(
        base_url=row.tb_download_base_url or None,
        username=row.tb_username or None,
        password=row.tb_password or None,
        device_id=row.tb_device_id or None,
        device_ids=tb_ids,
        timeout_seconds=float(row.tb_download_timeout_seconds),
    )
    return SettingsPayload(
        mqtt=mqtt,
        telemetry=telemetry,
        thingsboard_download=download,
    )


@router.get("", response_model=SettingsPayload)
def get_settings_api(db: Session = Depends(get_db)) -> SettingsPayload:
    row: Optional[SystemSettings] = db.query(SystemSettings).first()
    if not row:
        # No DB row yet; return defaults from current env-based Settings
        from app.config import get_settings as get_env_settings

        env_settings = get_env_settings()
        return SettingsPayload(
            mqtt=env_settings.mqtt,
            telemetry=env_settings.telemetry,
            thingsboard_download=env_settings.thingsboard_download,
        )

    return _system_settings_to_payload(row)


@router.put("", response_model=SettingsPayload)
def upsert_settings_api(payload: SettingsPayload, db: Session = Depends(get_db)) -> SettingsPayload:
    row: Optional[SystemSettings] = db.query(SystemSettings).first()
    if not row:
        row = SystemSettings()
        db.add(row)

    # Update MQTT
    row.mqtt_host = payload.mqtt.host
    row.mqtt_port = payload.mqtt.port
    row.mqtt_username = payload.mqtt.username
    row.mqtt_password = payload.mqtt.password
    row.mqtt_client_id_prefix = payload.mqtt.client_id_prefix
    row.mqtt_keepalive = payload.mqtt.keepalive
    row.mqtt_topic_pattern = payload.mqtt.topic_pattern
    row.mqtt_qos = payload.mqtt.qos

    # Telemetry / ThingsBoard push
    row.tb_base_url = payload.telemetry.base_url
    row.tb_enable_push = payload.telemetry.enable_push
    row.tb_enable_auto_push = payload.telemetry.enable_auto_push
    row.tb_timeout_seconds = str(payload.telemetry.timeout_seconds)
    row.tb_device_token = payload.telemetry.device_token
    row.tb_token_from_topic_regex = payload.telemetry.token_from_topic_regex
    row.tb_one_device_per_meter = payload.telemetry.one_device_per_meter
    row.tb_push_interval_seconds = str(payload.telemetry.push_interval_seconds)
    row.tb_inactivity_minutes = str(payload.telemetry.inactivity_minutes)
    row.tb_inactivity_check_interval_seconds = str(
        payload.telemetry.inactivity_check_interval_seconds
    )
    row.tb_inactivity_timeout_seconds = str(
        payload.telemetry.inactivity_timeout_seconds
    )

    # ThingsBoard download / credentials
    row.tb_download_base_url = payload.thingsboard_download.base_url
    row.tb_username = payload.thingsboard_download.username
    row.tb_password = payload.thingsboard_download.password
    row.tb_device_id = payload.thingsboard_download.device_id
    row.tb_device_ids = (
        ",".join(payload.thingsboard_download.device_ids)
        if payload.thingsboard_download.device_ids
        else None
    )
    row.tb_download_timeout_seconds = str(
        payload.thingsboard_download.timeout_seconds
    )

    db.commit()
    db.refresh(row)

    # Clear cached Settings so future requests (e.g. reports/download)
    # see the latest DB-backed configuration without needing a restart.
    try:
        from app.config import get_settings as _cached_settings

        _cached_settings.cache_clear()
    except Exception:
        # Best-effort; if cache clearing fails, values will refresh on next restart.
        pass

    return _system_settings_to_payload(row)

