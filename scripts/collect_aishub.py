"""
Collect near-real-time AIS snapshots from AISHub.

Default scope: Red Sea, Bab el-Mandeb, Gulf of Aden, and nearby approaches.

Credentials:
- Set AISHUB_USERNAME in the environment, or pass --username.
- Do not hard-code the username in this file if the repository is public.

Outputs:
- Raw JSON snapshots: data/aishub/raw/YYYY-MM-DD/*.json
- Appended CSV table: data/aishub/processed/aishub_positions.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


AISHUB_URL = "https://data.aishub.net/ws.php"
MIN_POLL_SECONDS = 60
REQUEST_TIMEOUT_SECONDS = 90

PROJECT_ROOT = Path(__file__).resolve().parent
if PROJECT_ROOT.name == "scripts":
    PROJECT_ROOT = PROJECT_ROOT.parent

OUTPUT_ROOT = PROJECT_ROOT / "data" / "aishub"
RAW_DIR = OUTPUT_ROOT / "raw"
PROCESSED_DIR = OUTPUT_ROOT / "processed"
POSITIONS_CSV = PROCESSED_DIR / "aishub_positions.csv"

DEFAULT_BBOX = {
    "latmin": 10.0,
    "latmax": 30.0,
    "lonmin": 32.0,
    "lonmax": 65.0,
}

BBOX_PRESETS = {
    "red-sea-gulf-aden": DEFAULT_BBOX,
    "red-sea": {"latmin": 12.0, "latmax": 30.0, "lonmin": 32.0, "lonmax": 44.0},
    "bab-el-mandeb": {"latmin": 11.0, "latmax": 14.0, "lonmin": 41.0, "lonmax": 45.0},
    "gulf-aden": {"latmin": 10.0, "latmax": 16.0, "lonmin": 43.0, "lonmax": 54.0},
}

CSV_FIELDS = [
    "collected_at_utc",
    "mmsi",
    "time",
    "latitude",
    "longitude",
    "sog",
    "cog",
    "heading",
    "navstat",
    "imo",
    "name",
    "callsign",
    "type",
    "a",
    "b",
    "c",
    "d",
    "draught",
    "dest",
    "eta",
    "raw_json",
]

FIELD_ALIASES = {
    "mmsi": ["MMSI", "mmsi"],
    "time": ["TIME", "TSTAMP", "timestamp", "time"],
    "latitude": ["LATITUDE", "LAT", "lat", "latitude"],
    "longitude": ["LONGITUDE", "LON", "lon", "longitude"],
    "sog": ["SOG", "speed", "sog"],
    "cog": ["COG", "course", "cog"],
    "heading": ["HEADING", "heading"],
    "navstat": ["NAVSTAT", "navstat"],
    "imo": ["IMO", "imo"],
    "name": ["NAME", "SHIPNAME", "name"],
    "callsign": ["CALLSIGN", "callsign"],
    "type": ["TYPE", "SHIPTYPE", "type"],
    "a": ["A", "dim_a"],
    "b": ["B", "dim_b"],
    "c": ["C", "dim_c"],
    "d": ["D", "dim_d"],
    "draught": ["DRAUGHT", "draught"],
    "dest": ["DEST", "DESTINATION", "dest"],
    "eta": ["ETA", "eta"],
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect near-real-time AIS data from AISHub."
    )
    parser.add_argument(
        "--username",
        default=os.getenv("AISHUB_USERNAME"),
        help="AISHub username. Defaults to AISHUB_USERNAME environment variable.",
    )
    parser.add_argument(
        "--preset",
        choices=sorted(BBOX_PRESETS),
        default="red-sea-gulf-aden",
        help="Named bounding box preset.",
    )
    parser.add_argument("--latmin", type=float, help="Override minimum latitude.")
    parser.add_argument("--latmax", type=float, help="Override maximum latitude.")
    parser.add_argument("--lonmin", type=float, help="Override minimum longitude.")
    parser.add_argument("--lonmax", type=float, help="Override maximum longitude.")
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="AISHub interval parameter; returns positions reported within this recent window.",
    )
    parser.add_argument(
        "--poll-seconds",
        type=int,
        default=MIN_POLL_SECONDS,
        help="Seconds between API calls in loop mode. AISHub should not be polled more than once per minute.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run one API request and exit. Without this flag, the script loops until interrupted.",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=POSITIONS_CSV,
        help="Processed CSV output path.",
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=RAW_DIR,
        help="Directory for raw JSON snapshots.",
    )
    return parser.parse_args()


def bbox_from_args(args: argparse.Namespace) -> dict[str, float]:
    bbox = dict(BBOX_PRESETS[args.preset])
    for key in ["latmin", "latmax", "lonmin", "lonmax"]:
        value = getattr(args, key)
        if value is not None:
            bbox[key] = value
    if bbox["latmin"] >= bbox["latmax"]:
        raise ValueError("latmin must be smaller than latmax.")
    if bbox["lonmin"] >= bbox["lonmax"]:
        raise ValueError("lonmin must be smaller than lonmax.")
    return bbox


def fetch_snapshot(username: str, bbox: dict[str, float], interval: int) -> dict[str, Any]:
    params = {
        "username": username,
        "format": 1,
        "output": "json",
        "compress": 0,
        "latmin": bbox["latmin"],
        "latmax": bbox["latmax"],
        "lonmin": bbox["lonmin"],
        "lonmax": bbox["lonmax"],
        "interval": interval,
    }
    response = requests.get(AISHUB_URL, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


def extract_records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]

    if not isinstance(payload, dict):
        raise ValueError(f"Unexpected AISHub response type: {type(payload).__name__}")

    if payload.get("ERROR") not in (None, False, "false", "FALSE", 0, "0"):
        raise RuntimeError(f"AISHub returned an error: {payload}")

    for key in ["DATA", "data", "AIS", "ais", "RESULT", "result"]:
        value = payload.get(key)
        if isinstance(value, list):
            return [row for row in value if isinstance(row, dict)]

    # Some API modes can return an empty object for no matching traffic.
    return []


def value_from_aliases(record: dict[str, Any], aliases: list[str]) -> Any:
    for alias in aliases:
        if alias in record:
            return record[alias]
    return ""


def normalize_record(record: dict[str, Any], collected_at: datetime) -> dict[str, Any]:
    row = {"collected_at_utc": collected_at.isoformat(timespec="seconds")}
    for field, aliases in FIELD_ALIASES.items():
        row[field] = value_from_aliases(record, aliases)
    row["raw_json"] = json.dumps(record, ensure_ascii=False, sort_keys=True)
    return row


def existing_keys(csv_path: Path) -> set[tuple[str, str]]:
    if not csv_path.exists():
        return set()

    keys: set[tuple[str, str]] = set()
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            mmsi = row.get("mmsi", "")
            timestamp = row.get("time", "")
            if mmsi and timestamp:
                keys.add((mmsi, timestamp))
    return keys


def append_rows(csv_path: Path, rows: list[dict[str, Any]]) -> int:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    seen = existing_keys(csv_path)
    write_header = not csv_path.exists()

    written = 0
    with csv_path.open("a", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        for row in rows:
            key = (str(row.get("mmsi", "")), str(row.get("time", "")))
            if key[0] and key[1] and key in seen:
                continue
            writer.writerow(row)
            if key[0] and key[1]:
                seen.add(key)
            written += 1
    return written


def save_raw_snapshot(raw_dir: Path, payload: dict[str, Any], collected_at: datetime) -> Path:
    day_dir = raw_dir / collected_at.strftime("%Y-%m-%d")
    day_dir.mkdir(parents=True, exist_ok=True)
    path = day_dir / f"aishub_{collected_at.strftime('%Y%m%dT%H%M%SZ')}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def collect_once(args: argparse.Namespace, bbox: dict[str, float]) -> tuple[int, int, Path]:
    collected_at = utc_now()
    payload = fetch_snapshot(args.username, bbox, args.interval)
    raw_path = save_raw_snapshot(args.raw_dir, payload, collected_at)
    records = extract_records(payload)
    rows = [normalize_record(record, collected_at) for record in records]
    written = append_rows(args.output_csv, rows)
    return len(records), written, raw_path


def main() -> int:
    args = parse_args()
    if not args.username:
        print(
            "Missing AISHub username. Set AISHUB_USERNAME or pass --username.",
            file=sys.stderr,
        )
        return 2

    if args.poll_seconds < MIN_POLL_SECONDS:
        print(
            f"poll-seconds raised from {args.poll_seconds} to {MIN_POLL_SECONDS} "
            "to respect AISHub's one-request-per-minute guidance.",
            file=sys.stderr,
        )
        args.poll_seconds = MIN_POLL_SECONDS

    bbox = bbox_from_args(args)
    print(f"AISHub bbox: {bbox}")
    print(f"Processed CSV: {args.output_csv}")
    print(f"Raw snapshot directory: {args.raw_dir}")

    while True:
        try:
            total, written, raw_path = collect_once(args, bbox)
            print(
                f"{utc_now().isoformat(timespec='seconds')}: "
                f"received {total}, appended {written}, raw={raw_path}",
                flush=True,
            )
        except KeyboardInterrupt:
            print("Interrupted.")
            return 130
        except Exception as exc:
            print(f"Collection failed: {exc}", file=sys.stderr, flush=True)

        if args.once:
            return 0
        time.sleep(args.poll_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
