"""
Download endpoints: in-memory snapshot (JSON/CSV) and ThingsBoard historical telemetry.
"""
import csv
import io
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query, Response

from app.models.schemas import GatewayData, LatestDataResponse
from app.mqtt.mqtt_client import get_latest_data_snapshot
from app.config import get_settings
from app.services.thingsboard_client import fetch_telemetry_for_download, get_device_names
from app.services.thingsboard_download_formatter import (
    multi_device_timeseries_to_csv,
    multi_device_timeseries_to_json,
    pivot_multi_device_timeseries_to_csv,
    timeseries_to_csv,
    timeseries_to_json,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/download", tags=["download"])


# Time range presets (milliseconds)
MS_PER_HOUR = 3600 * 1000
MS_PER_DAY = 86400 * 1000
RANGE_PRESETS = {
    "1h": 1 * MS_PER_HOUR,
    "6h": 6 * MS_PER_HOUR,
    "12h": 12 * MS_PER_HOUR,
    "1d": 1 * MS_PER_DAY,
    "7d": 7 * MS_PER_DAY,
    "30d": 30 * MS_PER_DAY,
}


def _parse_date_to_ts(date_str: str, end_of_day: bool = False) -> int:
    """Parse YYYY-MM-DD to epoch milliseconds (UTC)."""
    dt = datetime.strptime(date_str.strip(), "%Y-%m-%d").replace(tzinfo=timezone.utc)
    if end_of_day:
        dt = dt.replace(hour=23, minute=59, second=59, microsecond=999_999)
    return int(dt.timestamp() * 1000)


@router.get("/latest-json")
async def download_latest_json() -> Response:
    """
    Download the latest in-memory gateway data snapshot as a JSON file.
    """
    snapshot: Dict[str, GatewayData] = get_latest_data_snapshot()
    payload = LatestDataResponse(gateways=snapshot).model_dump()
    content = json.dumps(payload, default=str)
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="latest_gateways.json"'},
    )


@router.get("/latest-csv")
async def download_latest_csv() -> Response:
    """
    Download the latest in-memory gateway data snapshot as a CSV file.
    Each row is one meter reading.
    """
    snapshot: Dict[str, GatewayData] = get_latest_data_snapshot()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "gateway_topic",
            "device_id",
            "rssi",
            "meter_id",
            "flow_rate",
            "total_consumption",
            "timestamp",
        ]
    )
    for gateway in snapshot.values():
        for meter in gateway.meters:
            writer.writerow(
                [
                    gateway.gateway_topic,
                    gateway.device_id,
                    gateway.rssi,
                    meter.meter_id,
                    meter.flow_rate,
                    meter.total_consumption,
                    gateway.timestamp.isoformat(),
                ]
            )
    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="latest_meters.csv"'},
    )


@router.get("/thingsboard")
async def download_thingsboard(
    format: str = Query("csv", description="Output format: csv or json"),
    layout: str = Query(
        "long",
        description=(
            "CSV layout: long (default) or pivot (timestamp + per-meter columns like spreadsheet). "
            "pivot is only supported for csv output."
        ),
    ),
    device_ids: Optional[str] = Query(
        None,
        description=(
            "Optional comma-separated ThingsBoard device UUIDs to download. "
            "If set, overrides THINGSBOARD_DEVICE_ID/THINGSBOARD_DEVICE_IDS for this request."
        ),
    ),
    start_date: str = Query(
        ...,
        description="Start date (YYYY-MM-DD).",
    ),
    end_date: str = Query(
        ...,
        description="End date (YYYY-MM-DD).",
    ),
    keys: Optional[str] = Query(
        None,
        description="Comma-separated telemetry keys to fetch (e.g. flow_rate, total_consumption). Omit for all keys.",
    ),
    limit: int = Query(100_000, ge=1, le=1_000_000, description="Max number of points per key."),
) -> Response:
    """
    Download historical telemetry from ThingsBoard REST API.

    Time range is always expressed as whole days via **start_date** and
    **end_date** (YYYY-MM-DD). The start of the day is used for start_date and
    the end of the day for end_date.
    """
    try:
        start_ts_resolved = _parse_date_to_ts(start_date, end_of_day=False)
        end_ts_resolved = _parse_date_to_ts(end_date, end_of_day=True)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format; use YYYY-MM-DD. {e!s}",
        )

    if start_ts_resolved >= end_ts_resolved:
        raise HTTPException(status_code=400, detail="start must be before end")

    key_list: Optional[List[str]] = None
    if keys:
        key_list = [k.strip() for k in keys.split(",") if k.strip()]

    device_id_list: Optional[List[str]] = None
    if device_ids:
        device_id_list = [x.strip() for x in device_ids.split(",") if x.strip()]

    try:
        data = fetch_telemetry_for_download(
            device_ids=device_id_list,
            keys=key_list,
            start_ts=start_ts_resolved,
            end_ts=end_ts_resolved,
            interval_ms=0,
            limit=limit,
        )
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except httpx.HTTPStatusError as e:
        logger.exception("ThingsBoard telemetry fetch failed: %s", e)
        hint = ""
        if e.response.status_code == 400:
            hint = " Check that THINGSBOARD_DEVICE_ID or THINGSBOARD_DEVICE_IDS in .env are valid device UUIDs from ThingsBoard (Device details → copy ID), not placeholders like 'uuid-11A'."
        raise HTTPException(
            status_code=502,
            detail=f"ThingsBoard request failed: {e!s}.{hint}",
        )
    except Exception as e:
        logger.exception("ThingsBoard telemetry fetch failed: %s", e)
        raise HTTPException(
            status_code=502,
            detail=f"ThingsBoard request failed: {e!s}",
        )

    fmt = format.strip().lower()
    if fmt not in ("csv", "json"):
        raise HTTPException(status_code=400, detail="format must be csv or json")
    lay = layout.strip().lower()
    if lay not in ("long", "pivot"):
        raise HTTPException(status_code=400, detail="layout must be long or pivot")
    if lay == "pivot" and fmt != "csv":
        raise HTTPException(status_code=400, detail="layout=pivot is only supported for format=csv")

    is_multi = isinstance(data, list)

    # Use download date in filenames so users can easily identify when a report was generated.
    # Format: YYYY-MM-DD (local server date).
    download_date = datetime.now().strftime("%Y-%m-%d")
    if fmt == "csv":
        if lay == "pivot":
            # Pivot layout requires multi-device data. For single device, wrap to reuse pivot formatter.
            devices_data = data if is_multi else [("device", data)]
            settings = get_settings()
            tb = settings.thingsboard_download
            # Prefer resolving UUID->device name via ThingsBoard API for headers like 11A/11B/11C
            labels = {}
            if is_multi:
                try:
                    labels = get_device_names(
                        tb.base_url or "",
                        tb.username or "",
                        tb.password or "",
                        [did for did, _ in devices_data],
                        timeout=tb.timeout_seconds,
                    )
                except Exception:
                    labels = {}
            content = pivot_multi_device_timeseries_to_csv(
                devices_data,
                device_labels=labels if labels else None,
                keys=key_list,
            )
            filename = f"AntarIoT_Flow_Meter_report_{download_date}_pivot.csv"
        else:
            content = multi_device_timeseries_to_csv(data) if is_multi else timeseries_to_csv(data)
            filename = f"AntarIoT_Flow_Meter_report_{download_date}.csv"
        media_type = "text/csv"
    else:
        content = multi_device_timeseries_to_json(data) if is_multi else timeseries_to_json(data)
        filename = f"AntarIoT_Flow_Meter_report_{download_date}.json"
        media_type = "application/json"

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
