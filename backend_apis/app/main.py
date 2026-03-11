import asyncio
import logging
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

try:
    # Ensure backend_apis/.env is loaded even when shell doesn't auto-load it.
    from dotenv import load_dotenv  # type: ignore

    _env_path = Path(__file__).resolve().parents[1] / ".env"
    load_dotenv(dotenv_path=_env_path, override=False)
except Exception:
    # Best-effort: if python-dotenv isn't installed, os.environ must be set externally.
    pass

from app.api.v1.api import api_router
from app.core.logging import configure_logging
from app.core.settings import get_settings
from app.models.schemas import GatewayData, LatestDataResponse
from app.mqtt.mqtt_client import get_latest_data_snapshot, start_mqtt, stop_mqtt
from app.services.telemetry_publisher import (
    TelemetryResult,
    publish_gateway_telemetry,
    publish_multiple_gateways_telemetry,
)
from app.services.thingsboard_client import set_devices_inactivity_timeout

_periodic_push_task: Optional[asyncio.Task] = None
_inactivity_check_task: Optional[asyncio.Task] = None


configure_logging()
logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(title=settings.app.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev: allow all origins (frontend on 5173)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


async def _periodic_push_loop() -> None:
    """Push latest snapshot to ThingsBoard at a fixed interval so dashboards get fresh points."""
    settings = get_settings()
    interval = settings.telemetry.push_interval_seconds
    if interval <= 0:
        return
    while True:
        await asyncio.sleep(interval)
        snapshot = get_latest_data_snapshot()
        if not snapshot or not settings.telemetry.enable_push:
            continue
        now = datetime.now(timezone.utc)
        gateways = list(snapshot.values())
        # If inactivity threshold is set, do not push gateways that are past it,
        # so ThingsBoard can mark them Inactive (no activity = inactive state).
        if settings.telemetry.inactivity_minutes > 0:
            threshold = timedelta(minutes=settings.telemetry.inactivity_minutes)
            gateways = [g for g in gateways if (now - g.timestamp) <= threshold]
        gateways_with_now = [
            g.model_copy(update={"timestamp": now}) for g in gateways
        ]
        if not gateways_with_now:
            continue
        try:
            await publish_multiple_gateways_telemetry(gateways_with_now)
        except Exception:
            logger.exception("Periodic telemetry push failed")


async def _inactivity_check_loop() -> None:
    """
    When gateways have had no MQTT for inactivity_minutes, we do NOT push any
    telemetry to ThingsBoard. Sending even { connected: false } counts as
    activity and keeps the device State = Active. By not pushing, ThingsBoard
    sees no new activity and marks the device Inactive after its device-profile
    inactivity timeout (e.g. default 10 min in thingsboard.yml).
    This loop only ensures we don't accidentally push (e.g. from a periodic
    push): we skip gateways that are past the threshold. See also periodic push.
    """
    settings = get_settings()
    interval = settings.telemetry.inactivity_check_interval_seconds
    threshold_minutes = settings.telemetry.inactivity_minutes
    if threshold_minutes <= 0 or interval <= 0 or not settings.telemetry.enable_push:
        return
    while True:
        await asyncio.sleep(interval)
        snapshot = get_latest_data_snapshot()
        if not snapshot:
            continue
        now = datetime.now(timezone.utc)
        threshold = timedelta(minutes=threshold_minutes)
        inactive = [
            g for g in snapshot.values()
            if (now - g.timestamp) > threshold
        ]
        for gateway in inactive:
            logger.debug(
                "Gateway %s inactive (no MQTT for > %.1f min); not pushing (so ThingsBoard can mark device Inactive)",
                gateway.gateway_topic,
                threshold_minutes,
            )


@app.on_event("startup")
async def on_startup() -> None:
    global _periodic_push_task, _inactivity_check_task
    settings = get_settings()
    logger.info("FastAPI application startup: initializing MQTT client.")
    logger.info(
        "Telemetry settings: enabled=%s auto=%s base_url=%s token_regex=%s",
        settings.telemetry.enable_push,
        settings.telemetry.enable_auto_push,
        settings.telemetry.base_url,
        settings.telemetry.token_from_topic_regex,
    )
    start_mqtt()
    # Set ThingsBoard device inactivity timeout so State flips to Inactive soon after MQTT stops
    if settings.telemetry.inactivity_timeout_seconds > 0:
        tb = settings.thingsboard_download
        device_ids = list(tb.device_ids) if tb.device_ids else ([tb.device_id] if tb.device_id else [])
        if tb.base_url and tb.username and tb.password and device_ids:
            try:
                await asyncio.to_thread(
                    set_devices_inactivity_timeout,
                    tb.base_url,
                    tb.username,
                    tb.password,
                    device_ids,
                    settings.telemetry.inactivity_timeout_seconds,
                    tb.timeout_seconds,
                )
                logger.info(
                    "ThingsBoard inactivity timeout set to %.1f s for %d device(s) (realtime Inactive when MQTT stops)",
                    settings.telemetry.inactivity_timeout_seconds,
                    len(device_ids),
                )
            except Exception:
                logger.exception("Failed to set ThingsBoard device inactivity timeout")
        else:
            logger.warning(
                "TELEMETRY_INACTIVITY_TIMEOUT_SECONDS=%s but ThingsBoard download credentials or device IDs missing; skipping.",
                settings.telemetry.inactivity_timeout_seconds,
            )
    if (
        settings.telemetry.enable_push
        and settings.telemetry.push_interval_seconds > 0
    ):
        _periodic_push_task = asyncio.create_task(_periodic_push_loop())
        logger.info(
            "Periodic telemetry push started every %.1f s",
            settings.telemetry.push_interval_seconds,
        )
    if (
        settings.telemetry.enable_push
        and settings.telemetry.inactivity_minutes > 0
        and settings.telemetry.inactivity_check_interval_seconds > 0
    ):
        _inactivity_check_task = asyncio.create_task(_inactivity_check_loop())
        logger.info(
            "Inactivity check started: mark devices inactive after %.1f min, check every %.1f s",
            settings.telemetry.inactivity_minutes,
            settings.telemetry.inactivity_check_interval_seconds,
        )


@app.on_event("shutdown")
async def on_shutdown() -> None:
    global _periodic_push_task, _inactivity_check_task
    if _periodic_push_task is not None:
        _periodic_push_task.cancel()
        try:
            await _periodic_push_task
        except asyncio.CancelledError:
            pass
        _periodic_push_task = None
    if _inactivity_check_task is not None:
        _inactivity_check_task.cancel()
        try:
            await _inactivity_check_task
        except asyncio.CancelledError:
            pass
        _inactivity_check_task = None
    logger.info("FastAPI application shutdown: stopping MQTT client.")
    stop_mqtt()


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/latest-data", response_model=LatestDataResponse)
async def get_latest_data() -> LatestDataResponse:
    snapshot: Dict[str, GatewayData] = get_latest_data_snapshot()
    return LatestDataResponse(gateways=snapshot)


@app.post("/telemetry/push-latest")
async def push_latest_telemetry(
    gateway_topics: Optional[List[str]] = Body(
        default=None,
        embed=True,
        description="Optional list of gateway topics to push. If omitted, all gateways are pushed.",
    ),
) -> Dict[str, TelemetryResult]:
    """
    Manually trigger telemetry push for the latest data of one or more gateways.
    Uses the same telemetry publisher as the automatic MQTT-based flow.
    """
    settings = get_settings()
    if not settings.telemetry.enable_push:
        raise HTTPException(
            status_code=400,
            detail="Telemetry push is disabled. Enable it via ENABLE_TELEMETRY_PUSH.",
        )

    snapshot = get_latest_data_snapshot()
    if not snapshot:
        raise HTTPException(status_code=404, detail="No gateway data available.")

    if gateway_topics:
        missing = [t for t in gateway_topics if t not in snapshot]
        if missing:
            raise HTTPException(
                status_code=404,
                detail=f"Gateways not found for topics: {', '.join(missing)}",
            )
        gateways = [snapshot[t] for t in gateway_topics]
    else:
        gateways = list(snapshot.values())

    results = await publish_multiple_gateways_telemetry(gateways)
    return results


@app.post("/gateways/{gateway_topic}/push-telemetry")
async def push_single_gateway_telemetry(gateway_topic: str) -> TelemetryResult:
    """
    Manually trigger telemetry push for a single gateway topic.
    """
    settings = get_settings()
    if not settings.telemetry.enable_push:
        raise HTTPException(
            status_code=400,
            detail="Telemetry push is disabled. Enable it via ENABLE_TELEMETRY_PUSH.",
        )

    snapshot = get_latest_data_snapshot()
    gateway = snapshot.get(gateway_topic)
    if not gateway:
        raise HTTPException(
            status_code=404,
            detail=f"No data available for gateway topic '{gateway_topic}'.",
        )

    result = await publish_gateway_telemetry(gateway)
    return result


