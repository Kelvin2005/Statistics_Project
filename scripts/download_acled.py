"""
Download ACLED data for Yemen, the Red Sea/Gulf of Aden area, and Houthi-related
events.

The script intentionally separates two scopes:
1. API scope: date range + candidate countries/maritime areas.
2. Local scope: keyword filtering across actor, location, notes, and tag fields.

Credentials:
- Prefer an existing data/acled_API.json access token if it is still valid.
- Otherwise set ACLED_EMAIL and ACLED_PASSWORD environment variables.
"""

from __future__ import annotations

import base64
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests


PROJECT_ROOT = Path(__file__).resolve().parent
if PROJECT_ROOT.name in {"scripts", "code"}:
    PROJECT_ROOT = PROJECT_ROOT.parent

DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = DATA_DIR / "acled_data"
RAW_OUTPUT_FILE = OUTPUT_DIR / "red_sea_yemen_candidate_2025-05-28_to_present.csv"
FILTERED_OUTPUT_FILE = OUTPUT_DIR / "red_sea_yemen_houthi_related_2025-05-28_to_present.csv"
METADATA_FILE = OUTPUT_DIR / "download_scope_metadata_2025-05-28_to_present.json"
TOKEN_CACHE_FILE = DATA_DIR / "acled_API.json"

TOKEN_URL = "https://acleddata.com/oauth/token"
API_BASE = "https://acleddata.com/api/acled/read"

START_DATE = "2025-05-28"
END_DATE = datetime.now().strftime("%Y-%m-%d")
PAGE_SIZE = 30000
REQUEST_DELAY_SECONDS = 0.5
REQUEST_TIMEOUT_SECONDS = 180
MAX_RETRIES = 3

# ACLED's API filters are exact field filters. This is a deliberately broad
# candidate scope; the narrower Houthi/Red Sea/Gulf of Aden scope is applied
# after download via keyword matching.
API_COUNTRIES = [
    "Yemen",
    "Saudi Arabia",
    "Oman",
    "Djibouti",
    "Eritrea",
    "Somalia",
    "Indian Ocean",
    "Red Sea",
    "Gulf of Aden",
]

HOUTHI_KEYWORDS = [
    "Houthi",
    "Houthis",
    "Ansar Allah",
    "Ansarallah",
    "Red Sea",
    "Gulf of Aden",
    "Aden Gulf",
    "Bab el-Mandeb",
    "Bab al-Mandab",
    "al-Hudaydah",
    "Hodeidah",
    "Hudaydah",
    "Sa'dah",
    "Saada",
    "Sanaa",
    "Sana'a",
    "Marib",
    "Ma'rib",
]

FILTER_TEXT_COLUMNS = [
    "actor1",
    "actor2",
    "assoc_actor_1",
    "assoc_actor_2",
    "location",
    "admin1",
    "admin2",
    "admin3",
    "notes",
    "tags",
]


def _decode_jwt_payload(token: str) -> dict[str, Any]:
    payload = token.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    return json.loads(base64.urlsafe_b64decode(payload))


def cached_access_token() -> str | None:
    if not TOKEN_CACHE_FILE.exists():
        return None

    token_data = json.loads(TOKEN_CACHE_FILE.read_text(encoding="utf-8-sig"))
    access_token = token_data.get("access_token")
    if not access_token:
        return None

    try:
        payload = _decode_jwt_payload(access_token)
    except Exception:
        return None

    # Keep a two-minute margin so a token cannot expire mid-request.
    if float(payload.get("exp", 0)) > time.time() + 120:
        return access_token
    return None


def refresh_cached_token() -> str | None:
    if not TOKEN_CACHE_FILE.exists():
        return None

    token_data = json.loads(TOKEN_CACHE_FILE.read_text(encoding="utf-8-sig"))
    refresh_token = token_data.get("refresh_token")
    if not refresh_token:
        return None

    response = requests.post(
        TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
            "client_id": "acled",
            "scope": "authenticated",
        },
        timeout=60,
    )
    if response.status_code != 200:
        return None

    refreshed_data = response.json()
    TOKEN_CACHE_FILE.write_text(
        json.dumps(refreshed_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Refreshed ACLED token, valid for {refreshed_data.get('expires_in')} seconds.")
    return refreshed_data["access_token"]


def get_access_token() -> str:
    cached = cached_access_token()
    if cached:
        print("Using cached ACLED access token.")
        return cached

    refreshed = refresh_cached_token()
    if refreshed:
        return refreshed

    username = os.getenv("ACLED_EMAIL")
    password = os.getenv("ACLED_PASSWORD")
    if not username or not password:
        raise RuntimeError(
            "No valid cached token found. Set ACLED_EMAIL and ACLED_PASSWORD, "
            f"or refresh {TOKEN_CACHE_FILE}."
        )

    response = requests.post(
        TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "username": username,
            "password": password,
            "grant_type": "password",
            "client_id": "acled",
            "scope": "authenticated",
        },
        timeout=60,
    )
    response.raise_for_status()
    token_data = response.json()
    TOKEN_CACHE_FILE.write_text(
        json.dumps(token_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Fetched new ACLED token, valid for {token_data.get('expires_in')} seconds.")
    return token_data["access_token"]


def country_or_filter(countries: list[str]) -> str:
    first, *rest = countries
    return first + "".join(f":OR:country={country}" for country in rest)


def fetch_acled_page(
    access_token: str, country: str, page: int
) -> tuple[list[dict[str, Any]], int | None]:
    params = {
        "_format": "json",
        "country": country,
        "event_date": f"{START_DATE}|{END_DATE}",
        "event_date_where": "BETWEEN",
        "limit": PAGE_SIZE,
        "page": page,
    }
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(
                API_BASE, params=params, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS
            )
            response.raise_for_status()
            payload = response.json()
            break
        except requests.RequestException as exc:
            last_error = exc
            if attempt == MAX_RETRIES:
                raise
            wait_seconds = attempt * 5
            print(f"Page {page} request failed ({exc}); retrying in {wait_seconds}s.")
            time.sleep(wait_seconds)
    else:
        raise RuntimeError(f"Page {page} failed") from last_error

    if payload.get("status") != 200:
        raise RuntimeError(f"ACLED API returned status {payload.get('status')}: {payload}")

    total = payload.get("total_count")
    return payload.get("data", []), int(total) if total is not None else None


def download_country_data(access_token: str, country: str) -> list[dict[str, Any]]:
    all_data: list[dict[str, Any]] = []
    page = 1
    total_count: int | None = None

    print(f"\nDownloading country/area: {country}", flush=True)

    while True:
        data, total_count = fetch_acled_page(access_token, country, page)
        if not data:
            break

        all_data.extend(data)
        total_label = total_count if total_count is not None else "unknown"
        print(
            f"{country} page {page}: {len(data)} rows; accumulated {len(all_data)}/{total_label}",
            flush=True,
        )

        if len(data) < PAGE_SIZE:
            break

        page += 1
        time.sleep(REQUEST_DELAY_SECONDS)

    return all_data


def download_all_data(access_token: str) -> pd.DataFrame:
    all_data: list[dict[str, Any]] = []

    print(f"Downloading ACLED data from {START_DATE} to {END_DATE}.", flush=True)
    print(f"API country scope: {', '.join(API_COUNTRIES)}", flush=True)
    print(f"Page size: {PAGE_SIZE}", flush=True)

    for country in API_COUNTRIES:
        all_data.extend(download_country_data(access_token, country))
        time.sleep(REQUEST_DELAY_SECONDS)

    df = pd.DataFrame(all_data)
    if "event_id_cnty" in df.columns:
        df = df.drop_duplicates(subset=["event_id_cnty"])
    return df


def filter_houthi_related(df: pd.DataFrame) -> pd.DataFrame:
    available_columns = [column for column in FILTER_TEXT_COLUMNS if column in df.columns]
    if not available_columns:
        raise RuntimeError("None of the expected text fields were returned by ACLED.")

    pattern = "|".join(re.escape(keyword) for keyword in HOUTHI_KEYWORDS)
    search_text = df[available_columns].fillna("").astype(str).agg(" ".join, axis=1)
    return df[search_text.str.contains(pattern, case=False, na=False, regex=True)].copy()


def write_metadata(raw_df: pd.DataFrame, filtered_df: pd.DataFrame) -> None:
    metadata = {
        "downloaded_at": datetime.now().isoformat(timespec="seconds"),
        "api_base": API_BASE,
        "api_scope": {
            "format": "json",
            "countries": API_COUNTRIES,
            "event_date": f"{START_DATE}|{END_DATE}",
            "event_date_where": "BETWEEN",
            "limit": PAGE_SIZE,
            "page_start": 1,
            "with_total": False,
        },
        "local_filter_scope": {
            "keywords": HOUTHI_KEYWORDS,
            "searched_columns": [column for column in FILTER_TEXT_COLUMNS if column in raw_df.columns],
        },
        "outputs": {
            "raw_candidate_file": str(RAW_OUTPUT_FILE),
            "filtered_file": str(FILTERED_OUTPUT_FILE),
        },
        "row_counts": {
            "raw_candidate_rows": int(len(raw_df)),
            "filtered_rows": int(len(filtered_df)),
        },
    }
    METADATA_FILE.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")


def print_summary(raw_df: pd.DataFrame, filtered_df: pd.DataFrame) -> None:
    print("\nSummary")
    print("=" * 60)
    print(f"Raw candidate rows: {len(raw_df)}")
    print(f"Filtered rows: {len(filtered_df)}")

    for label, frame in [("Raw", raw_df), ("Filtered", filtered_df)]:
        if frame.empty:
            print(f"\n{label}: empty")
            continue

        print(f"\n{label} date range: {frame['event_date'].min()} to {frame['event_date'].max()}")
        if "country" in frame.columns:
            print(f"{label} countries:")
            print(frame["country"].value_counts().head(20).to_string())
        if "event_type" in frame.columns:
            print(f"\n{label} event types:")
            print(frame["event_type"].value_counts().head(10).to_string())


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    access_token = get_access_token()
    try:
        raw_df = download_all_data(access_token)
    except requests.HTTPError as exc:
        if exc.response is None or exc.response.status_code != 401:
            raise
        print("Cached ACLED token was rejected; trying refresh_token once.")
        refreshed_token = refresh_cached_token()
        if not refreshed_token:
            raise
        raw_df = download_all_data(refreshed_token)

    if raw_df.empty:
        raise RuntimeError("ACLED returned no rows for the configured API scope.")

    filtered_df = filter_houthi_related(raw_df)

    raw_df.to_csv(RAW_OUTPUT_FILE, index=False, encoding="utf-8-sig")
    filtered_df.to_csv(FILTERED_OUTPUT_FILE, index=False, encoding="utf-8-sig")
    write_metadata(raw_df, filtered_df)
    print_summary(raw_df, filtered_df)

    print("\nSaved files:")
    print(f"- {RAW_OUTPUT_FILE}")
    print(f"- {FILTERED_OUTPUT_FILE}")
    print(f"- {METADATA_FILE}")


if __name__ == "__main__":
    main()
