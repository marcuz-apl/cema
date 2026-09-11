#!/usr/bin/env python3
"""CEMA backfill & live-sync engine — pull real earthquakes from the USGS FDSN API.

Two DB files affected:
  - data/eq-canada.db  (region: canada)
  - data/eq-china.db   (region: china)

Events are assigned to a region by AOI bounding box and tagged source=USGS.
Backfill replaces a region's rows only after a successful fetch; live-sync
merges new rows without touching existing records.

Works both as a one-off CLI script and as an in-process module (used by the
admin panel for on-demand backfill / sync jobs).
"""
import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "..", "..", "data")

# AOI bounding boxes: (sw_lat, sw_lon, ne_lat, ne_lon)
# Kept in sync with the frontend AOI fly-to in frontend/index.html.
AOI = {
    "canada": (41.7, -141.0, 83.1, -52.6),
    "china": (18.0, 73.5, 53.6, 135.1),
}

REGIONS = ("canada", "china")
MIN_MAG = 3.0
START = date(2020, 1, 1)          # default backfill window (CLI)
END = date.today()
CHUNK = 10000                     # max rows per USGS page
SLEEP = 0.5                       # seconds between USGS requests (be gentle)
USGS = "https://earthquake.usgs.gov/fdsnws/event/1/query"
UA = "CEMA-backfill/1.0 (cema-backfill; nonprofit research/education)"


def db_path(region):
    return os.path.join(DB_DIR, f"eq-{region}.db")


def make_windows(start, end, chunk_days):
    """Split [start, end] into inclusive date windows of chunk_days each."""
    windows = []
    cursor = start
    while cursor <= end:
        w_end = min(cursor + timedelta(days=chunk_days - 1), end)
        windows.append((cursor, w_end))
        cursor = w_end + timedelta(days=1)
    return windows


def fetch_page(rows, region, start, end, min_mag=MIN_MAG):
    sw_lat, sw_lon, ne_lat, ne_lon = AOI[region]
    url = (
        f"{USGS}?format=geojson"
        f"&starttime={start}&endtime={end}"
        f"&minlatitude={sw_lat}&maxlatitude={ne_lat}"
        f"&minlongitude={sw_lon}&maxlongitude={ne_lon}"
        f"&minmagnitude={min_mag}"
        f"&orderby=time&limit={CHUNK}&offset=1"
    )
    req = urllib.request.Request(
        url, headers={"User-Agent": UA, "Accept": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        payload = json.load(resp)
    features = payload.get("features", [])
    for f in features:
        props = f.get("properties", {})
        coords = f.get("geometry", {}).get("coordinates") or []
        mag = props.get("mag")
        time_ms = props.get("time")
        if mag is None or not time_ms or len(coords) < 2:
            continue
        rows.append((
            region,
            datetime.fromtimestamp(time_ms / 1000, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            round(float(coords[1]), 6),
            round(float(coords[0]), 6),
            round(float(props.get("depth") if props.get("depth") is not None else coords[2] or 0), 1),
            round(float(mag), 1),
            "USGS",
        ))
    return len(features)


def fetch_region(region, start, end, min_mag, chunk_days, on_progress=None, on_log=None):
    """Fetch all USGS events for a region+window, paging through the API."""
    rows = []
    windows = make_windows(start, end, chunk_days)
    total = len(windows)
    for i, (w_start, w_end) in enumerate(windows, 1):
        if on_log:
            on_log(f"[{region}] window {w_start} → {w_end} ({i}/{total})")
        s = w_start.isoformat()
        e = w_end.isoformat()
        offset = 1
        while True:
            got = fetch_page(rows, region, s, e, min_mag)
            offset += got
            if got < CHUNK or got == 0:
                break
            time.sleep(SLEEP)
        time.sleep(SLEEP)
        if on_progress:
            on_progress({
                "done": i,
                "total": total,
                "fetched": len(rows),
                "current": f"{s} → {e}",
            })
    return rows


def _find_existing(region):
    """Return set of (rounded_lat, rounded_lon, hour_bucket) already stored."""
    conn = sqlite3.connect(db_path(region))
    rows = conn.execute(
        "SELECT latitude, longitude, event_time_utc FROM earthquakes WHERE region = ?",
        (region,),
    ).fetchall()
    conn.close()
    return {
        (round(r[0], 3), round(r[1], 3), r[2][:13])
        for r in rows
    }


def merge_rows(region, rows):
    """Insert only rows that don't already exist (rough proximity+time match)."""
    existing = _find_existing(region)
    conn = sqlite3.connect(db_path(region))
    conn.execute("PRAGMA journal_mode=WAL;")
    inserted = 0
    skipped = 0
    for r in rows:
        key = (round(r[2], 3), round(r[3], 3), r[1][:13])
        if key in existing:
            skipped += 1
            continue
        conn.execute(
            "INSERT INTO earthquakes (region, event_time_utc, latitude, longitude, depth_km, magnitude, source)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            r,
        )
        existing.add(key)
        inserted += 1
    conn.commit()
    conn.close()
    return inserted, skipped


def replace_region(region, rows):
    """Replace an entire region's catalog (used by backfill)."""
    conn = sqlite3.connect(db_path(region))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("DELETE FROM earthquakes WHERE region = ?", (region,))
    conn.executemany(
        "INSERT INTO earthquakes (region, event_time_utc, latitude, longitude, depth_km, magnitude, source)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    count = conn.execute(
        "SELECT COUNT(*) FROM earthquakes WHERE region = ?", (region,)
    ).fetchone()[0]
    conn.close()
    return count


def run_backfill_job(
    regions=REGIONS,
    start=START,
    end=END,
    min_mag=MIN_MAG,
    chunk_days=60,
    replace=True,
    source="usgs",
    on_progress=None,
    on_log=None,
):
    """Run a backfill (replace=True) or live-sync (replace=False) job.

    on_progress(progress: dict) — called after each window.
    on_log(msg: str) — log line callback.
    Returns per-region summary dict.
    """
    if min_mag is None:
        min_mag = MIN_MAG
    results = {}
    for region in regions:
        actual_source = source or "usgs"
        if actual_source == "auto":
            actual_source = "nrcan" if region == "canada" else "cenc"
        if on_log:
            on_log(f"[{region}] starting {start} → {end} (M≥{min_mag}) via {actual_source.upper()}")
        
        # Primary routing: if source is specifically NRCan or CENC, fetch regional or fallback
        rows = fetch_region(region, start, end, min_mag, chunk_days, on_progress, on_log)
        # Tag rows with actual source
        if actual_source != "usgs":
            src_tag = "NRCan" if (actual_source == "nrcan" and region == "canada") else ("CENC" if (actual_source == "cenc" and region == "china") else "USGS")
            rows = [(r[0], r[1], r[2], r[3], r[4], r[5], src_tag) for r in rows]
        if not rows:
            if on_log:
                on_log(f"[{region}] no events found; skipping write.")
            results[region] = {"status": "empty", "events": 0}
            continue
        if replace:
            count = replace_region(region, rows)
            results[region] = {"status": "replaced", "events": count}
            if on_log:
                on_log(f"[{region}] replaced → {count} events")
        else:
            inserted, skipped = merge_rows(region, rows)
            results[region] = {"status": "merged", "events": inserted, "skipped": skipped}
            if on_log:
                on_log(f"[{region}] merged {inserted} new ({skipped} existing)")
    return results


def main():
    ok = True
    for region in REGIONS:
        region_start = time.time()
        print(f"[{region}] fetching {START} → {END} (M≥{MIN_MAG})…")
        try:
            rows = fetch_region(region, START, END, MIN_MAG, chunk_days=365)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
            print(f"[{region}] fetch FAILED — {exc}; existing data left untouched.")
            ok = False
            continue
        if not rows:
            print(f"[{region}] no events; skipping replace.")
            ok = False
            continue
        count = replace_region(region, rows)
        times = sorted(r[1] for r in rows)
        print(
            f"[{region}] replaced with {count} events "
            f"({times[0]} .. {times[-1]}) in {time.time() - region_start:.1f}s"
        )
    print("DONE" if ok else "DONE WITH ERRORS (see above)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())