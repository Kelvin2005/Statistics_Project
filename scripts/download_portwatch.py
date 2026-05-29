"""
Download IMF PortWatch / PortStraitWatch daily chokepoint transit indicators.

The script collects the chokepoints most relevant to the Red Sea crisis:
- Suez Canal
- Bab el-Mandeb Strait
- Cape of Good Hope

Outputs:
- data/portwatch/portwatch_chokepoints_long.csv
- data/portwatch/portwatch_chokepoints_wide.csv
- data/portwatch/portwatch_red_sea_analysis.csv
- data/portwatch/download_metadata.json
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests


PROJECT_ROOT = Path(__file__).resolve().parent
if PROJECT_ROOT.name == "scripts":
    PROJECT_ROOT = PROJECT_ROOT.parent

OUTPUT_DIR = PROJECT_ROOT / "data" / "portwatch"
LONG_CSV = OUTPUT_DIR / "portwatch_chokepoints_long.csv"
WIDE_CSV = OUTPUT_DIR / "portwatch_chokepoints_wide.csv"
ANALYSIS_CSV = OUTPUT_DIR / "portwatch_red_sea_analysis.csv"
METADATA_JSON = OUTPUT_DIR / "download_metadata.json"

FEATURESERVER_QUERY_URL = (
    "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/"
    "Daily_Chokepoints_Data/FeatureServer/0/query"
)

DEFAULT_CHOKEPOINTS = {
    "chokepoint1": "Suez Canal",
    "chokepoint4": "Bab el-Mandeb Strait",
    "chokepoint7": "Cape of Good Hope",
}

DEFAULT_FIELDS = [
    "date",
    "year",
    "month",
    "day",
    "portid",
    "portname",
    "n_container",
    "n_dry_bulk",
    "n_general_cargo",
    "n_roro",
    "n_tanker",
    "n_cargo",
    "n_total",
    "capacity_container",
    "capacity_dry_bulk",
    "capacity_general_cargo",
    "capacity_roro",
    "capacity_tanker",
    "capacity_cargo",
    "capacity",
]

RENAME_FOR_WIDE = {
    "chokepoint1": "suez",
    "chokepoint4": "bab_el_mandeb",
    "chokepoint7": "cape_good_hope",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download daily PortWatch chokepoint transit indicators."
    )
    parser.add_argument(
        "--start-date",
        help="Optional inclusive start date, YYYY-MM-DD.",
    )
    parser.add_argument(
        "--end-date",
        help="Optional inclusive end date, YYYY-MM-DD.",
    )
    parser.add_argument(
        "--chokepoints",
        nargs="+",
        default=list(DEFAULT_CHOKEPOINTS),
        help="PortWatch chokepoint IDs to download.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="ArcGIS resultRecordCount per request.",
    )
    parser.add_argument(
        "--delay-seconds",
        type=float,
        default=1.0,
        help="Delay between paginated API requests.",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=8,
        help="Maximum retries for each ArcGIS request.",
    )
    return parser.parse_args()


def build_where(chokepoints: list[str], start_date: str | None, end_date: str | None) -> str:
    port_clauses = [f"portid='{portid}'" for portid in chokepoints]
    clauses = ["(" + " OR ".join(port_clauses) + ")"]

    if start_date:
        datetime.strptime(start_date, "%Y-%m-%d")
        clauses.append(f"date >= DATE '{start_date}'")
    if end_date:
        datetime.strptime(end_date, "%Y-%m-%d")
        clauses.append(f"date <= DATE '{end_date}'")

    return " AND ".join(clauses)


def fetch_page(
    where: str,
    fields: list[str],
    offset: int,
    batch_size: int,
    max_retries: int,
) -> dict[str, Any]:
    params = {
        "where": where,
        "outFields": ",".join(fields),
        "f": "json",
        "resultOffset": offset,
        "resultRecordCount": batch_size,
        "orderByFields": "date ASC, portid ASC",
    }

    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(FEATURESERVER_QUERY_URL, params=params, timeout=90)
            response.raise_for_status()
            payload = response.json()
            if "error" in payload:
                raise RuntimeError(payload["error"])
            return payload
        except Exception as exc:
            last_error = exc
            if attempt == max_retries:
                raise
            wait_seconds = attempt * 3
            print(f"Request offset {offset} failed ({exc}); retrying in {wait_seconds}s.")
            time.sleep(wait_seconds)

    raise RuntimeError("Unreachable fetch failure") from last_error


def download_records(
    chokepoints: list[str],
    start_date: str | None,
    end_date: str | None,
    batch_size: int,
    delay_seconds: float,
    max_retries: int,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    for chokepoint in chokepoints:
        where = build_where([chokepoint], start_date, end_date)
        offset = 0
        print(f"\nDownloading {chokepoint}: {DEFAULT_CHOKEPOINTS.get(chokepoint, chokepoint)}")

        while True:
            payload = fetch_page(where, DEFAULT_FIELDS, offset, batch_size, max_retries)
            features = payload.get("features", [])
            if not features:
                break

            rows.extend(feature["attributes"] for feature in features)
            print(
                f"{chokepoint}: downloaded {len(features)} rows at offset {offset}; "
                f"total {len(rows)}",
                flush=True,
            )

            if len(features) < batch_size:
                break

            offset += batch_size
            time.sleep(delay_seconds)
        time.sleep(delay_seconds)

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    if pd.api.types.is_numeric_dtype(df["date"]):
        df["date"] = pd.to_datetime(df["date"], unit="ms", utc=True).dt.date.astype(str)
    else:
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date.astype(str)
    numeric_columns = [column for column in df.columns if column.startswith("n_")]
    numeric_columns += [column for column in df.columns if column.startswith("capacity")]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    return df.sort_values(["date", "portid"]).reset_index(drop=True)


def make_wide_table(df: pd.DataFrame) -> pd.DataFrame:
    metric_columns = [column for column in df.columns if column.startswith("n_")]
    metric_columns += [column for column in df.columns if column.startswith("capacity")]

    pieces = []
    for _, row in df.iterrows():
        prefix = RENAME_FOR_WIDE.get(row["portid"], row["portid"])
        output = {"date": row["date"]}
        for metric in metric_columns:
            output[f"{prefix}_{metric}"] = row.get(metric)
        pieces.append(output)

    wide = pd.DataFrame(pieces)
    if wide.empty:
        return wide

    wide = wide.groupby("date", as_index=False).first().sort_values("date")
    return wide.reset_index(drop=True)


def add_analysis_metrics(wide: pd.DataFrame) -> pd.DataFrame:
    analysis = wide.copy()

    def ratio(numerator: str, denominator: str) -> pd.Series:
        if numerator not in analysis.columns or denominator not in analysis.columns:
            return pd.Series(pd.NA, index=analysis.index)
        return analysis[numerator] / analysis[denominator].replace({0: pd.NA})

    analysis["rerouting_index_total"] = ratio(
        "cape_good_hope_n_total", "suez_n_total"
    )
    analysis["rerouting_index_capacity"] = ratio(
        "cape_good_hope_capacity", "suez_capacity"
    )

    if {"suez_n_total", "cape_good_hope_n_total"}.issubset(analysis.columns):
        denominator = analysis["suez_n_total"] + analysis["cape_good_hope_n_total"]
        analysis["suez_share_total"] = analysis["suez_n_total"] / denominator.replace(
            {0: pd.NA}
        )

    if {"bab_el_mandeb_n_total", "suez_n_total"}.issubset(analysis.columns):
        analysis["bab_to_suez_total_ratio"] = ratio(
            "bab_el_mandeb_n_total", "suez_n_total"
        )

    return analysis


def write_metadata(args: argparse.Namespace, df: pd.DataFrame) -> None:
    metadata = {
        "downloaded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": FEATURESERVER_QUERY_URL,
        "chokepoints": {
            portid: DEFAULT_CHOKEPOINTS.get(portid, portid) for portid in args.chokepoints
        },
        "start_date": args.start_date,
        "end_date": args.end_date,
        "fields": DEFAULT_FIELDS,
        "row_count": int(len(df)),
        "date_min": None if df.empty else str(df["date"].min()),
        "date_max": None if df.empty else str(df["date"].max()),
        "outputs": {
            "long_csv": str(LONG_CSV.relative_to(PROJECT_ROOT)),
            "wide_csv": str(WIDE_CSV.relative_to(PROJECT_ROOT)),
            "analysis_csv": str(ANALYSIS_CSV.relative_to(PROJECT_ROOT)),
        },
    }
    METADATA_JSON.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main() -> int:
    args = parse_args()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = download_records(
        args.chokepoints,
        args.start_date,
        args.end_date,
        args.batch_size,
        args.delay_seconds,
        args.max_retries,
    )

    wide = make_wide_table(df)
    analysis = add_analysis_metrics(wide)

    df.to_csv(LONG_CSV, index=False, encoding="utf-8-sig")
    wide.to_csv(WIDE_CSV, index=False, encoding="utf-8-sig")
    analysis.to_csv(ANALYSIS_CSV, index=False, encoding="utf-8-sig")
    write_metadata(args, df)

    print("\nSaved:")
    print(f"- {LONG_CSV}")
    print(f"- {WIDE_CSV}")
    print(f"- {ANALYSIS_CSV}")
    print(f"- {METADATA_JSON}")

    if not df.empty:
        print("\nSummary:")
        print(f"Rows: {len(df)}")
        print(f"Dates: {df['date'].min()} to {df['date'].max()}")
        print(df["portname"].value_counts().to_string())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
