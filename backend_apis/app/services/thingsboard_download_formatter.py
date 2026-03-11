"""
Format ThingsBoard timeseries API response for download (CSV or JSON).

Accepts the raw response shape: { "key1": [{"ts": ms, "value": v}, ...], ... }
and produces either CSV rows or a list of row dicts for JSON.
"""
import csv
import io
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple, Optional


def _timeseries_to_rows(
    data: Dict[str, List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """
    Merge per-key timeseries into rows keyed by timestamp (ms).
    Each row: {"ts": ms, "ts_iso": "...", "key1": v1, "key2": v2, ...}.
    """
    if not data:
        return []

    # Collect all timestamps
    all_ts: set[int] = set()
    for series in data.values():
        for point in series:
            all_ts.add(point["ts"])

    sorted_ts = sorted(all_ts)
    keys_order = sorted(data.keys())

    # Build value lookup: (ts, key) -> value
    value_at: Dict[int, Dict[str, Any]] = {}
    for ts in sorted_ts:
        value_at[ts] = {}
    for key, series in data.items():
        for point in series:
            ts = point["ts"]
            if ts in value_at:
                value_at[ts][key] = point.get("value")

    rows: List[Dict[str, Any]] = []
    for ts in sorted_ts:
        row: Dict[str, Any] = {
            "ts": ts,
            "ts_iso": datetime.fromtimestamp(ts / 1000.0, tz=timezone.utc).isoformat(),
        }
        for k in keys_order:
            row[k] = value_at[ts].get(k, "")
        rows.append(row)
    return rows


def timeseries_to_csv(data: Dict[str, List[Dict[str, Any]]]) -> str:
    """Produce a CSV string from ThingsBoard timeseries response."""
    rows = _timeseries_to_rows(data)
    if not rows:
        return ""

    output = io.StringIO()
    # Header: ts, ts_iso, then all data keys in stable order
    data_keys = sorted(k for k in rows[0].keys() if k not in ("ts", "ts_iso"))
    headers = ["ts", "ts_iso"] + data_keys
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in rows:
        writer.writerow([row.get(h, "") for h in headers])
    return output.getvalue()


def timeseries_to_json(data: Dict[str, List[Dict[str, Any]]]) -> str:
    """Produce a JSON string (array of row objects) from ThingsBoard timeseries response."""
    rows = _timeseries_to_rows(data)
    return json.dumps(rows, default=str)


def multi_device_timeseries_to_csv(
    devices_data: List[Tuple[str, Dict[str, List[Dict[str, Any]]]]],
) -> str:
    """Produce CSV with device_id column from multiple devices' timeseries."""
    all_rows: List[Dict[str, Any]] = []
    for device_id, data in devices_data:
        rows = _timeseries_to_rows(data)
        for row in rows:
            row_with_id = {"device_id": device_id, **row}
            all_rows.append(row_with_id)
    if not all_rows:
        return ""
    data_keys = sorted(k for k in all_rows[0].keys() if k not in ("device_id", "ts", "ts_iso"))
    headers = ["device_id", "ts", "ts_iso"] + data_keys
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in all_rows:
        writer.writerow([row.get(h, "") for h in headers])
    return output.getvalue()


def multi_device_timeseries_to_json(
    devices_data: List[Tuple[str, Dict[str, List[Dict[str, Any]]]]],
) -> str:
    """Produce JSON array with device_id in each row from multiple devices."""
    all_rows: List[Dict[str, Any]] = []
    for device_id, data in devices_data:
        rows = _timeseries_to_rows(data)
        for row in rows:
            all_rows.append({"device_id": device_id, **row})
    return json.dumps(all_rows, default=str)


def pivot_multi_device_timeseries_to_csv(
    devices_data: List[Tuple[str, Dict[str, List[Dict[str, Any]]]]],
    *,
    device_labels: Optional[Dict[str, str]] = None,
    keys: Optional[List[str]] = None,
) -> str:
    """
    Produce a "wide/pivot" CSV like:
      Row 1: meter, 11A, , 11B, , 11C,
      Row 2: timestamp, flow rate, total consumption, flow rate, total consumption, ...
      Rows : timestamp values + per-device per-key values

    devices_data: list of (device_id, timeseries_dict)
    device_labels: optional mapping device_id -> display name (e.g. "11A")
    keys: optional fixed key order; if omitted, uses sorted union of keys from data
    """
    if not devices_data:
        return ""

    # Stable device order: as passed in
    device_ids = [device_id for device_id, _ in devices_data]

    # Determine keys (columns under each device)
    if keys is None:
        key_set: set[str] = set()
        for _, data in devices_data:
            key_set.update(data.keys())
        keys_order = sorted(key_set)
    else:
        keys_order = list(keys)

    # Build value lookup: values[device_id][ts][key] = value
    all_ts: set[int] = set()
    values: Dict[str, Dict[int, Dict[str, Any]]] = {}
    for device_id, data in devices_data:
        ts_map: Dict[int, Dict[str, Any]] = {}
        for key, series in data.items():
            for point in series:
                ts = point["ts"]
                all_ts.add(ts)
                if ts not in ts_map:
                    ts_map[ts] = {}
                ts_map[ts][key] = point.get("value")
        values[device_id] = ts_map

    sorted_ts = sorted(all_ts)
    output = io.StringIO()
    writer = csv.writer(output)

    # Header row 1 (meter groups)
    header1: List[str] = ["meter"]
    for device_id in device_ids:
        label = (
            device_labels.get(device_id)
            if device_labels and device_id in device_labels
            else device_id
        )
        header1.append(label)
        header1.extend([""] * (len(keys_order) - 1 if len(keys_order) > 0 else 0))
    writer.writerow(header1)

    # Header row 2 (sub-columns)
    header2: List[str] = ["timestamp"]
    for _device_id in device_ids:
        for k in keys_order:
            header2.append(k.replace("_", " "))
    writer.writerow(header2)

    # Data rows
    for ts in sorted_ts:
        ts_iso = datetime.fromtimestamp(ts / 1000.0, tz=timezone.utc).isoformat()
        row: List[Any] = [ts_iso]
        for device_id in device_ids:
            ts_map = values.get(device_id, {})
            point = ts_map.get(ts, {})
            for k in keys_order:
                row.append(point.get(k, ""))
        writer.writerow(row)

    return output.getvalue()
