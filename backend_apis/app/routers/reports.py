import logging
import os
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any

import csv
import io

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models.db_models import DevicePreset
from app.services.thingsboard_client import get_auth_token, get_device_name, get_timeseries

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["reports"])

# IST = UTC+5:30 (no DST). Use fixed offset so Windows works without tzdata.
IST = timezone(timedelta(hours=5, minutes=30))

# Optional max counter value for wrap-around meters.
# If set (e.g. TOTAL_CONSUMPTION_MAX=1000), daily consumption will treat any
# drop in the total_consumption counter as a wrap:
#   usage_segment = (max_counter - prev) + current
#
# If not set, drops are still flagged via reset_detected but daily_consumption
# falls back to 0 for safety (legacy behavior).
try:
    _MAX_COUNTER_RAW = os.getenv("TOTAL_CONSUMPTION_MAX")
    MAX_COUNTER: Optional[float] = (
        float(_MAX_COUNTER_RAW) if _MAX_COUNTER_RAW and float(_MAX_COUNTER_RAW) > 0 else None
    )
except Exception:
    MAX_COUNTER = None


def _utc_iso_to_ist_iso(utc_iso: Optional[str]) -> str:
    """Convert UTC ISO timestamp to IST (UTC+5:30) ISO string for CSV."""
    if not utc_iso or not utc_iso.strip():
        return ""
    try:
        s = utc_iso.strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        ist = dt.astimezone(IST)
        return ist.isoformat()
    except Exception:
        return utc_iso


def _parse_date_to_ts(date_str: str, end_of_day: bool = False) -> int:
    """Parse YYYY-MM-DD to epoch milliseconds (UTC)."""
    dt = datetime.strptime(date_str.strip(), "%Y-%m-%d").replace(tzinfo=timezone.utc)
    if end_of_day:
        dt = dt.replace(hour=23, minute=59, second=59, microsecond=999_999)
    return int(dt.timestamp() * 1000)


class DailyConsumptionRow(BaseModel):
    device_id: str
    device_name: str
    date: str  # YYYY-MM-DD (UTC)
    key: str
    start_ts: Optional[int] = None
    end_ts: Optional[int] = None
    start_ts_iso: Optional[str] = None
    end_ts_iso: Optional[str] = None
    start_value: Optional[float] = None
    end_value: Optional[float] = None
    daily_consumption: Optional[float] = None
    points: int
    missing: bool
    reset_detected: bool


@router.get("/daily-consumption", response_model=List[DailyConsumptionRow])
def daily_consumption(
    date: str = Query(..., description="Base day (YYYY-MM-DD) used for grouping."),
    # Optional ISO8601 start/end timestamps (UTC). We intentionally do NOT wrap
    # these in fastapi.Query so that internal calls (e.g. from the CSV endpoint)
    # receive `None` as the default instead of a Query object.
    start_iso: Optional[str] = None,
    end_iso: Optional[str] = None,
    preset_id: Optional[int] = Query(
        None, description="Optional device preset id to use for device_ids/keys."
    ),
    device_ids: Optional[str] = Query(
        None, description="Optional comma-separated ThingsBoard device UUIDs."
    ),
    key: str = Query(
        "total_consumption",
        description="Telemetry key to compute daily delta from (default total_consumption).",
    ),
    db: Session = Depends(get_db),
) -> List[DailyConsumptionRow]:
    """
    Compute per-device daily consumption from ThingsBoard timeseries:
      daily = last(value in day) - first(value in day)

    This endpoint DOES NOT write back to ThingsBoard.
    """
    settings = get_settings()
    tb = settings.thingsboard_download
    if not tb.base_url or not tb.username or not tb.password:
        raise HTTPException(
            status_code=503,
            detail=(
                "ThingsBoard download not configured: set base_url/username/password "
                "in Settings."
            ),
        )

    # Resolve device IDs: query override > single preset > all presets > settings
    resolved_ids: List[str] = []
    if device_ids:
        resolved_ids = [x.strip() for x in device_ids.split(",") if x.strip()]
    elif preset_id is not None:
        preset = db.query(DevicePreset).filter(DevicePreset.id == preset_id).first()
        if not preset:
            raise HTTPException(status_code=404, detail="Preset not found.")
        resolved_ids = [x.strip() for x in (preset.device_ids or "").split(",") if x.strip()]
        if preset.keys:
            # If preset stores keys, prefer it when user didn't pass key explicitly
            # (keep current default behavior if key is already set by query param)
            pass
    else:
        # No explicit preset_id: use all presets (if any) as default pool
        all_presets = db.query(DevicePreset).all()
        for p in all_presets:
            resolved_ids.extend(
                [x.strip() for x in (p.device_ids or "").split(",") if x.strip()]
            )
        # Fallback: settings-based device IDs
        if not resolved_ids:
            if tb.device_ids:
                resolved_ids = list(tb.device_ids)
            elif tb.device_id:
                resolved_ids = [tb.device_id]

    if not resolved_ids:
        raise HTTPException(
            status_code=400,
            detail="No device IDs provided. Use device_ids query param, preset_id, or configure THINGSBOARD_DEVICE_IDS in Settings.",
        )

    # Determine time window [start_ts, end_ts]
    if start_iso or end_iso:
        if not (start_iso and end_iso):
            raise HTTPException(
                status_code=400,
                detail="Both start_iso and end_iso must be provided together.",
            )
        try:
            s = start_iso.strip().replace("Z", "+00:00")
            e = end_iso.strip().replace("Z", "+00:00")
            s_dt = datetime.fromisoformat(s)
            e_dt = datetime.fromisoformat(e)
            if s_dt.tzinfo is None:
                s_dt = s_dt.replace(tzinfo=timezone.utc)
            if e_dt.tzinfo is None:
                e_dt = e_dt.replace(tzinfo=timezone.utc)
            start_ts = int(s_dt.timestamp() * 1000)
            end_ts = int(e_dt.timestamp() * 1000)
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid start_iso/end_iso format: {exc!s}",
            )
        if start_ts >= end_ts:
            raise HTTPException(
                status_code=400, detail="start_iso must be before end_iso"
            )
    else:
        try:
            start_ts = _parse_date_to_ts(date, end_of_day=False)
            end_ts = _parse_date_to_ts(date, end_of_day=True)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid date format. {e!s}")

    # Login once
    try:
        jwt = get_auth_token(tb.base_url, tb.username, tb.password, tb.timeout_seconds)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ThingsBoard login failed: {e!s}")

    rows: List[DailyConsumptionRow] = []
    for did in resolved_ids:
        # Resolve name (fallback to UUID)
        try:
            name = get_device_name(tb.base_url, jwt, did, timeout=tb.timeout_seconds)
        except Exception:
            name = did

        try:
            data: Dict[str, List[Dict[str, Any]]] = get_timeseries(
                base_url=tb.base_url,
                token=jwt,
                device_id=did,
                keys=[key],
                start_ts=start_ts,
                end_ts=end_ts,
                limit=100_000,
                timeout=tb.timeout_seconds,
            )
        except httpx.HTTPStatusError as e:
            logger.exception("ThingsBoard timeseries fetch failed: %s", e)
            raise HTTPException(status_code=502, detail=f"ThingsBoard request failed: {e!s}")
        except Exception as e:
            logger.exception("ThingsBoard timeseries fetch failed: %s", e)
            raise HTTPException(status_code=502, detail=f"ThingsBoard request failed: {e!s}")

        series = data.get(key) or []
        if not series:
            rows.append(
                DailyConsumptionRow(
                    device_id=did,
                    device_name=name,
                    date=date,
                    key=key,
                    points=0,
                    missing=True,
                    reset_detected=False,
                )
            )
            continue

        # Build list of (ts, value) for all valid numeric points in the day.
        points: List[tuple[int, float]] = []
        for p in series:
            try:
                val = float(p.get("value"))
            except Exception:
                continue
            ts = p.get("ts")
            if isinstance(ts, (int, float)):
                points.append((int(ts), val))

        if not points:
            rows.append(
                DailyConsumptionRow(
                    device_id=did,
                    device_name=name,
                    date=date,
                    key=key,
                    points=len(series),
                    missing=True,
                    reset_detected=False,
                )
            )
            continue

        # Start/end values from first/last valid point in the day.
        start_ts, start_val = points[0]
        end_ts, end_val = points[-1]

        # Determine an effective max counter for wrap-around segments.
        # Priority:
        # 1) Explicit TOTAL_CONSUMPTION_MAX from env (if provided)
        # 2) Auto-detected power-of-10 above the largest observed value
        max_observed = max(v for _, v in points)
        # Avoid log math; just use power of 10 >= integer digits of max_observed
        try:
            digits = max(1, len(str(int(abs(max_observed)))))
        except Exception:
            digits = 6  # sane fallback
        auto_max_counter = float(10 ** digits)
        effective_max = (
            MAX_COUNTER if MAX_COUNTER is not None and MAX_COUNTER > 0 else auto_max_counter
        )

        # Walk through all consecutive points in the day to compute usage,
        # correctly handling wrap-around counters.
        total_delta = 0.0
        reset = False
        for i in range(1, len(points)):
            prev_ts, prev_val = points[i - 1]
            curr_ts, curr_val = points[i]
            if curr_val >= prev_val:
                total_delta += curr_val - prev_val
            else:
                # Counter dropped: treat as wrap-around.
                reset = True
                total_delta += (effective_max - prev_val) + curr_val

        # Round to 2 decimal places to avoid long floating tails.
        delta = round(total_delta, 2) if total_delta > 0 else 0.0
        start_ts_iso: Optional[str] = None
        end_ts_iso: Optional[str] = None
        if isinstance(start_ts, (int, float)):
            start_ts_iso = datetime.fromtimestamp(start_ts / 1000.0, tz=timezone.utc).isoformat()
        if isinstance(end_ts, (int, float)):
            end_ts_iso = datetime.fromtimestamp(end_ts / 1000.0, tz=timezone.utc).isoformat()

        rows.append(
            DailyConsumptionRow(
                device_id=did,
                device_name=name,
                date=date,
                key=key,
                start_ts=start_ts,
                end_ts=end_ts,
                start_ts_iso=start_ts_iso,
                end_ts_iso=end_ts_iso,
                start_value=start_val,
                end_value=end_val,
                daily_consumption=delta,
                points=len(series),
                missing=False,
                reset_detected=reset,
            )
        )

    return rows


@router.get("/daily-consumption-csv")
def daily_consumption_csv(
    start_date: str = Query(..., description="Start day (YYYY-MM-DD), UTC day boundary."),
    end_date: str = Query(..., description="End day (YYYY-MM-DD), UTC day boundary."),
    preset_id: Optional[int] = Query(
        None, description="Optional device preset id to use for device_ids/keys."
    ),
    device_ids: Optional[str] = Query(
        None, description="Optional comma-separated ThingsBoard device UUIDs."
    ),
    key: str = Query(
        "total_consumption",
        description="Telemetry key to compute daily delta from (default total_consumption).",
    ),
    db: Session = Depends(get_db),
) -> Response:
    """
    Download daily consumption for a date range as CSV.

    Each row corresponds to one device on one day.
    """
    try:
        start_dt = datetime.strptime(start_date.strip(), "%Y-%m-%d")
        end_dt = datetime.strptime(end_date.strip(), "%Y-%m-%d")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format. {e!s}")

    if end_dt < start_dt:
        raise HTTPException(status_code=400, detail="end_date must be >= start_date")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "device_name",
            "device_id",
            "date",
            "start_time_ist",
            "end_time_ist",
            "start_value",
            "end_value",
            "daily_consumption",
            "status",
        ]
    )

    current = start_dt
    while current <= end_dt:
        day_str = current.strftime("%Y-%m-%d")
        # Reuse the JSON endpoint logic to keep computation consistent.
        rows = daily_consumption(
            date=day_str,
            preset_id=preset_id,
            device_ids=device_ids,
            key=key,
            db=db,
        )
        for r in rows:
            status = "Missing" if r.missing else "Reset" if r.reset_detected else "OK"
            writer.writerow(
                [
                    r.device_name,
                    r.device_id,
                    r.date,
                    _utc_iso_to_ist_iso(r.start_ts_iso),
                    _utc_iso_to_ist_iso(r.end_ts_iso),
                    r.start_value if r.start_value is not None else "",
                    r.end_value if r.end_value is not None else "",
                    r.daily_consumption if r.daily_consumption is not None else "",
                    status,
                ]
            )
        current += timedelta(days=1)

    csv_text = output.getvalue()
    filename = f"daily_consumption_{start_date}_to_{end_date}.csv"
    headers = {
        "Content-Type": "text/csv; charset=utf-8",
        "Content-Disposition": f'attachment; filename="{filename}"',
    }
    return Response(content=csv_text, headers=headers)

