"""CEMA Admin Panel — authenticated operations, telemetry, backfill engine, event moderation.

Auth is a single master passkey stored in data/cema-admin.db (key/value table).
All /api/admin/* routes require an `X-Admin-Key` header (or `Authorization: Bearer <key>`).
"""
import asyncio
import io
import json
import os
from backend.ingestion.country_assigner import assign_location
import sqlite3
import threading
import time
import urllib.request
import zipfile
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .ingestion import backfill
from .ingestion.dedup import deduplicate, find_duplicates

DB_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
ADMIN_DB = os.path.join(DB_DIR, "cema-admin.db")
REGIONS = ("canada", "china")
DEFAULT_ADMIN_KEY = "cema2026"

router = APIRouter(prefix="/api/admin", tags=["admin"])

MAG_BINS = [
    (7.0, 99.0, "M7.0+"),
    (6.0, 7.0, "M6.0-6.9"),
    (4.5, 6.0, "M4.5-5.9"),
    (3.0, 4.5, "M3.0-4.4"),
    (0.0, 3.0, "M<3.0"),
]


# ---------------------------------------------------------------
# Admin config store (single meta DB for operator state)
# ---------------------------------------------------------------
def _connect_admin():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(ADMIN_DB)
    conn.row_factory = sqlite3.Row
    conn.execute(
        "CREATE TABLE IF NOT EXISTS admin_config ("
        "  key TEXT PRIMARY KEY, value TEXT, updated_at TEXT DEFAULT CURRENT_TIMESTAMP)"
    )
    return conn


def get_admin_password() -> str:
    with _connect_admin() as conn:
        row = conn.execute(
            "SELECT value FROM admin_config WHERE key = 'admin_password'"
        ).fetchone()
    if row is None:
        with _connect_admin() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO admin_config (key, value) VALUES ('admin_password', ?)",
                (DEFAULT_ADMIN_KEY,),
            )
            conn.commit()
        return DEFAULT_ADMIN_KEY
    return row["value"]


def update_admin_password(current_password: str, new_password: str) -> bool:
    active = get_admin_password()
    if active != current_password:
        return False
    with _connect_admin() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO admin_config (key, value, updated_at) "
            "VALUES ('admin_password', ?, datetime('now'))",
            (new_password,),
        )
        conn.commit()
    return True


def verify_admin_key(
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    authorization: Optional[str] = Header(None),
):
    token = x_admin_key
    if not token and authorization and authorization.startswith("Bearer "):
        token = authorization.split("Bearer ", 1)[1].strip()
    if not token or token != get_admin_password():
        raise HTTPException(status_code=401, detail="Unauthorized — invalid admin passkey.")
    return True


# ---------------------------------------------------------------
# Global job state (backfill / sync) — guarded by a lock
# ---------------------------------------------------------------
_LOCK = threading.Lock()
BACKFILL_STATE = {
    "is_running": False,
    "status": "idle",
    "mode": None,
    "start_date": None,
    "end_date": None,
    "min_mag": None,
    "regions": [],
    "windows_total": 0,
    "windows_done": 0,
    "fetched": 0,
    "inserted": 0,
    "per_region": {},
    "current_window": None,
    "log": [],
    "error": None,
    "started_at": None,
    "finished_at": None,
}
SYNC_STATE = {
    "is_running": False,
    "last": None,
    "result": {},
}


def _log(msg):
    with _LOCK:
        BACKFILL_STATE["log"] = (BACKFILL_STATE["log"] + [msg])[-200:]


# ---------------------------------------------------------------
# DB helpers (operate on both regional catalogs)
# ---------------------------------------------------------------
def _regions_list(regions):
    if not regions or regions in ("all", "usgs", "global"):
        return list(REGIONS)
    if regions in ("canada", "nrcan"):
        return ["canada"]
    if regions in ("china", "cenc"):
        return ["china"]
    out = [r for r in REGIONS if r in regions]
    if not out:
        raise HTTPException(status_code=400, detail=f"Invalid region(s) or provider: {regions}")
    return out


def _region_rows(region, where="", params=()):
    path = os.path.join(DB_DIR, f"eq-{region}.db")
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    q = f"SELECT id, region, event_time_utc, latitude, longitude, depth_km, magnitude, source FROM earthquakes"
    if where:
        q += f" WHERE {where}"
    rows = [dict(r) for r in conn.execute(q, params).fetchall()]
    conn.close()
    return rows


def get_admin_stats():
    combined = {
        "total_records": 0,
        "earliest_date": None,
        "latest_date": None,
        "max_magnitude": 0,
        "by_year": {},
        "magnitude_distribution": {label: 0 for _, _, label in MAG_BINS},
        "sources": {},
        "per_region": {},
    }
    for region in REGIONS:
        path = os.path.join(DB_DIR, f"eq-{region}.db")
        conn = sqlite3.connect(path)
        row = conn.execute(
            "SELECT COUNT(*) as cnt, MIN(event_time_utc) mn, MAX(event_time_utc) mx, "
            "MAX(magnitude) mxmag FROM earthquakes WHERE region = ?",
            (region,),
        ).fetchone()
        year_rows = conn.execute(
            "SELECT SUBSTR(event_time_utc, 1, 4) y, COUNT(*) cnt FROM earthquakes "
            "WHERE region = ? GROUP BY y ORDER BY y",
            (region,),
        ).fetchall()
        mag_rows = conn.execute(
            "SELECT magnitude FROM earthquakes WHERE region = ?", (region,)
        ).fetchall()
        src_rows = conn.execute(
            "SELECT source, COUNT(*) cnt FROM earthquakes WHERE region = ? "
            "GROUP BY source ORDER BY cnt DESC",
            (region,),
        ).fetchall()
        conn.close()

        cnt, mn, mx, mxmag = row[0], row[1], row[2], row[3]
        combined["total_records"] += cnt
        combined["per_region"][region] = cnt
        if mxmag and mxmag > combined["max_magnitude"]:
            combined["max_magnitude"] = mxmag
        for d in (mn, mx):
            if not d:
                continue
            if combined["earliest_date"] is None or d < combined["earliest_date"]:
                combined["earliest_date"] = d
            if combined["latest_date"] is None or d > combined["latest_date"]:
                combined["latest_date"] = d
        for yr, ycnt in year_rows:
            combined["by_year"][yr] = combined["by_year"].get(yr, 0) + ycnt
        for mag in (r[0] for r in mag_rows):
            if mag is None:
                continue
            for lo, hi, label in MAG_BINS:
                if lo <= mag < hi:
                    combined["magnitude_distribution"][label] += 1
                    break
        for src, scnt in src_rows:
            combined["sources"][src or "Unknown"] = (
                combined["sources"].get(src or "Unknown", 0) + scnt
            )

    db_sizes, wal_sizes = {}, {}
    for region in REGIONS:
        path = os.path.join(DB_DIR, f"eq-{region}.db")
        db_sizes[region] = os.path.getsize(path) if os.path.exists(path) else 0
        wal_path = path + "-wal"
        wal_sizes[region] = os.path.getsize(wal_path) if os.path.exists(wal_path) else 0

    return {
        **combined,
        "by_year_list": [
            {"year": y, "count": c}
            for y, c in sorted(combined["by_year"].items(), reverse=True)
        ],
        "db_size_bytes": sum(db_sizes.values()),
        "db_size_mb": round(sum(db_sizes.values()) / (1024 * 1024), 2),
        "wal_size_mb": round(sum(wal_sizes.values()) / (1024 * 1024), 2),
        "db_sizes": db_sizes,
        "wal_sizes": wal_sizes,
    }


def query_admin_events(
    region=None,
    source=None,
    min_mag=0.0,
    max_mag=10.0,
    start_date=None,
    end_date=None,
    search=None,
    limit=50,
    offset=0,
    sort_by="event_time_utc",
    sort_dir="desc",
):
    targets = _regions_list(region)
    all_rows = []
    for r in targets:
        where = ["region = ?"]
        params = [r]
        if source:
            where.append("source = ?")
            params.append(source)
        where.append("magnitude >= ? AND magnitude <= ?")
        params.extend([min_mag, max_mag])
        if start_date:
            where.append("event_time_utc >= ?")
            params.append(start_date)
        if end_date:
            where.append("event_time_utc <= ?")
            params.append(end_date)
        rows = _region_rows(r, " AND ".join(where), params)
        for row in rows:
            row["db"] = r
        all_rows.extend(rows)
    if search:
        q = search.lower()
        all_rows = [
            row
            for row in all_rows
            if q in (row.get("source") or "").lower()
            or q in row.get("region", "").lower()
            or q in row.get("event_time_utc", "")[:19]
            or q in f"{row.get('latitude',0):.2f}"
            or q in f"{row.get('longitude',0):.2f}"
        ]
    if sort_by not in {"event_time_utc", "magnitude", "region", "latitude", "longitude", "depth_km"}:
        sort_by = "event_time_utc"
    key = sort_by
    all_rows.sort(
        key=lambda x: x[key],
        reverse=(sort_dir == "desc"),
    )
    total = len(all_rows)
    page = all_rows[offset:offset + limit]
    return page, total


def checkpoint_wal():
    """Force a WAL checkpoint on both catalogs."""
    results = {}
    for region in REGIONS:
        path = os.path.join(DB_DIR, f"eq-{region}.db")
        conn = sqlite3.connect(path)
        before = os.path.exists(path + "-wal") and os.path.getsize(path + "-wal") or 0
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.commit()
        after = os.path.exists(path + "-wal") and os.path.getsize(path + "-wal") or 0
        conn.close()
        results[region] = {"wal_before": before, "wal_after": after}
    return {"status": "ok", "checkpoint": results}


def vacuum_db():
    results = {}
    for region in REGIONS:
        path = os.path.join(DB_DIR, f"eq-{region}.db")
        before = os.path.getsize(path)
        conn = sqlite3.connect(path)
        conn.execute("VACUUM")
        conn.execute("ANALYZE")
        conn.commit()
        conn.close()
        after = os.path.getsize(path)
        results[region] = {"before": before, "after": after, "saved": max(0, before - after)}
    return {"status": "ok", "vacuum": results}


def purge_noise(min_mag: float):
    """Delete all events strictly below the magnitude floor across both catalogs."""
    results = {}
    for region in REGIONS:
        path = os.path.join(DB_DIR, f"eq-{region}.db")
        conn = sqlite3.connect(path)
        row = conn.execute(
            "SELECT COUNT(*) FROM earthquakes WHERE region = ? AND (magnitude < ? OR magnitude IS NULL)",
            (region, min_mag),
        ).fetchone()
        deleted = row[0]
        conn.execute(
            "DELETE FROM earthquakes WHERE region = ? AND (magnitude < ? OR magnitude IS NULL)",
            (region, min_mag),
        )
        conn.commit()
        results[region] = deleted
        conn.close()
    return {"status": "ok", "floor": min_mag, "deleted": results, "total_deleted": sum(results.values())}


def purge_date_range(start_date: str, end_date: str, regions: str = "all"):
    """Delete all events within [start_date, end_date] across specified catalog(s)."""
    targets = _regions_list(regions)
    start_iso = f"{start_date}T00:00:00"
    end_iso = f"{end_date}T23:59:59.999"
    results = {}
    for region in targets:
        path = os.path.join(DB_DIR, f"eq-{region}.db")
        if not os.path.exists(path):
            continue
        conn = sqlite3.connect(path)
        row = conn.execute(
            "SELECT COUNT(*) FROM earthquakes WHERE region = ? AND event_time_utc >= ? AND event_time_utc <= ?",
            (region, start_iso, end_iso),
        ).fetchone()
        count = row[0] if row else 0
        conn.execute(
            "DELETE FROM earthquakes WHERE region = ? AND event_time_utc >= ? AND event_time_utc <= ?",
            (region, start_iso, end_iso),
        )
        conn.commit()
        conn.close()
        results[region] = count
    return {
        "status": "ok",
        "start_date": start_date,
        "end_date": end_date,
        "regions": targets,
        "deleted": results,
        "total_deleted": sum(results.values()),
    }



_HEALTH_CACHE = {"data": None, "ts": 0}
_HEALTH_LOCK = threading.Lock()


def _usgs_health():
    payload = {"status": "healthy", "reachable": True, "latency_ms": None, "checked_at": None}
    try:
        t0 = time.time()
        req = urllib.request.Request(
            backfill.USGS + "?format=geojson&limit=1",
            headers={"User-Agent": backfill.UA},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            resp.read(32)
        payload["latency_ms"] = max(1, round((time.time() - t0) * 1000))
        payload["checked_at"] = datetime.now(timezone.utc).isoformat()
    except Exception:
        payload["status"] = "degraded"
        payload["reachable"] = False
    return payload


def _nrcan_health():
    payload = {"status": "healthy", "reachable": True, "latency_ms": None, "checked_at": None}
    try:
        t0 = time.time()
        req = urllib.request.Request(
            "https://www.earthquakescanada.nrcan.gc.ca/fdsnws/event/1/query?format=text&limit=1",
            headers={"User-Agent": "CEMA-admin/1.0"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            resp.read(32)
        payload["latency_ms"] = max(1, round((time.time() - t0) * 1000))
        payload["checked_at"] = datetime.now(timezone.utc).isoformat()
    except Exception:
        payload["status"] = "degraded"
        payload["reachable"] = False
    return payload


def _cenc_health():
    payload = {"status": "healthy", "reachable": True, "latency_ms": None, "checked_at": None}
    try:
        t0 = time.time()
        req = urllib.request.Request(
            "http://news.ceic.ac.cn/",
            headers={"User-Agent": "Mozilla/5.0 (CEMA-probe/1.0)"},
        )
        try:
            with urllib.request.urlopen(req, timeout=4) as resp:
                resp.read(32)
        except urllib.error.HTTPError as he:
            if he.code in (403, 405, 301, 302, 200):
                pass
            else:
                raise
        payload["latency_ms"] = max(1, round((time.time() - t0) * 1000))
        payload["checked_at"] = datetime.now(timezone.utc).isoformat()
    except Exception:
        payload["status"] = "degraded"
        payload["reachable"] = False
    return payload


def _provider_health():
    return _usgs_health()


def _get_all_provider_health():
    now = time.time()
    with _HEALTH_LOCK:
        if _HEALTH_CACHE["data"] is not None and (now - _HEALTH_CACHE["ts"]) < 15:
            return _HEALTH_CACHE["data"]
    usgs_h = _usgs_health()
    nrcan_h = _nrcan_health()
    cenc_h = _cenc_health()
    res = (usgs_h, nrcan_h, cenc_h)
    with _HEALTH_LOCK:
        _HEALTH_CACHE["data"] = res
        _HEALTH_CACHE["ts"] = time.time()
    return res


# ---------------------------------------------------------------
# Backfill runner
# ---------------------------------------------------------------
def _run_backfill_sync(params):
    regions = _regions_list(params.get("regions"))
    start = date.fromisoformat(params["start_date"])
    end = date.fromisoformat(params["end_date"])
    min_mag = params.get("min_mag", 3.0)
    chunk_days = params.get("chunk_days", 60)
    replace = params.get("mode", "backfill") == "backfill"
    source = params.get("source", "usgs")

    def on_progress(p):
        with _LOCK:
            BACKFILL_STATE["windows_done"] = p["done"]
            BACKFILL_STATE["windows_total"] = p["total"]
            BACKFILL_STATE["fetched"] = p["fetched"]
            BACKFILL_STATE["current_window"] = p["current"]

    try:
        results = backfill.run_backfill_job(
            regions=regions,
            start=start,
            end=end,
            min_mag=min_mag,
            chunk_days=chunk_days,
            replace=replace,
            source=source,
            on_progress=on_progress,
            on_log=_log,
        )
        inserted = sum(r.get("events", 0) for r in results.values())
        with _LOCK:
            BACKFILL_STATE["is_running"] = False
            BACKFILL_STATE["status"] = "complete"
            BACKFILL_STATE["per_region"] = results
            BACKFILL_STATE["inserted"] = inserted
            BACKFILL_STATE["finished_at"] = datetime.now(timezone.utc).isoformat()
    except Exception as exc:  # noqa: BLE001
        _log(f"backfill job failed: {exc}")
        with _LOCK:
            BACKFILL_STATE["is_running"] = False
            BACKFILL_STATE["status"] = "failed"
            BACKFILL_STATE["error"] = str(exc)
            BACKFILL_STATE["finished_at"] = datetime.now(timezone.utc).isoformat()


def _run_live_sync_sync(regions):
    start = date.today() - timedelta(days=7)
    end = date.today()

    def on_progress(p):
        with _LOCK:
            SYNC_STATE["windows_done"] = p["done"]

    results = backfill.run_backfill_job(
        regions=regions,
        start=start,
        end=end,
        min_mag=2.0,
        chunk_days=7,
        replace=False,
        on_progress=on_progress,
        on_log=lambda m: _log(m),
    )
    with _LOCK:
        SYNC_STATE["is_running"] = False
        SYNC_STATE["last"] = datetime.now(timezone.utc).isoformat()
        SYNC_STATE["result"] = results


# ---------------------------------------------------------------
# Pydantic request models
# ---------------------------------------------------------------
class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)


class PurgeRangeRequest(BaseModel):
    start_date: str
    end_date: str
    regions: str = "all"


class BackfillRequest(BaseModel):
    start_date: str
    end_date: str
    min_mag: float = Field(ge=3.0, le=10.0, default=3.0)
    chunk_days: int = Field(ge=7, le=365, default=60)
    regions: str = "all"
    mode: str = "backfill"  # backfill | merge
    source: str = "usgs"  # usgs | nrcan | cenc | auto


class ManualEarthquakeRequest(BaseModel):
    region: str
    event_time_utc: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    depth_km: float = Field(ge=0)
    magnitude: float = Field(ge=0, le=10)
    source: str = "OPERATOR"


class DeleteEarthquakeRequest(BaseModel):
    id: int
    region: str


# ---------------------------------------------------------------
# Auth + meta endpoints
# ---------------------------------------------------------------
@router.post("/auth")
async def admin_auth_check(_: bool = Depends(verify_admin_key)):
    return {"status": "authenticated", "message": "Admin credentials valid"}


@router.post("/change-password")
async def admin_change_password(
    req: ChangePasswordRequest, _: bool = Depends(verify_admin_key)
):
    ok = update_admin_password(req.current_password, req.new_password)
    if not ok:
        raise HTTPException(status_code=400, detail="Current passkey is incorrect.")
    return {"status": "success", "message": "Admin passkey updated."}


# ---------------------------------------------------------------
# Status / telemetry
# ---------------------------------------------------------------
@router.get("/status")
async def get_admin_dashboard_status(_: bool = Depends(verify_admin_key)):
    with _LOCK:
        backfill_state = dict(BACKFILL_STATE)
        sync_state = dict(SYNC_STATE)
    database = get_admin_stats()
    usgs_h, nrcan_h, cenc_h = await asyncio.to_thread(_get_all_provider_health)

    can_count = database["per_region"].get("canada", 0)
    chn_count = database["per_region"].get("china", 0)
    total_count = database.get("total_records", can_count + chn_count)

    providers = {
        "nrcan": {
            "name": "NRCan · Earthquakes Canada",
            "region": "canada",
            "role": "Primary National Pipeline (Canada)",
            "status": nrcan_h["status"],
            "reachable": nrcan_h["reachable"],
            "latency_ms": nrcan_h["latency_ms"],
            "catalog_count": can_count,
            "aoi": backfill.AOI["canada"],
            "source": "NRCan FDSN / Web Service",
            "endpoint": "https://earthquakescanada.nrcan.gc.ca",
        },
        "cenc": {
            "name": "CENC · China Networks (中国地震台网)",
            "region": "china",
            "role": "Primary National Pipeline (China)",
            "status": cenc_h["status"],
            "reachable": cenc_h["reachable"],
            "latency_ms": cenc_h["latency_ms"],
            "catalog_count": chn_count,
            "aoi": backfill.AOI["china"],
            "source": "CENC / CEIC Stream",
            "endpoint": "https://news.ceic.ac.cn",
        },
        "usgs": {
            "name": "USGS · Global Dual-AOI Feed",
            "region": "global",
            "role": "Secondary Cross-AOI Routing & Backfill",
            "status": usgs_h["status"],
            "reachable": usgs_h["reachable"],
            "latency_ms": usgs_h["latency_ms"],
            "catalog_count": total_count,
            "aoi": [41.7, -141.0, 83.1, 135.1],
            "source": "USGS FDSN API",
            "endpoint": "https://earthquake.usgs.gov",
        },
    }
    # Backward compatibility aliases for existing tests/clients
    providers["canada"] = providers["nrcan"]
    providers["china"] = providers["cenc"]
    return {
        "status": "healthy",
        "providers": providers,
        "sync_state": sync_state,
        "backfill_state": backfill_state,
        "database": database,
    }


# ---------------------------------------------------------------
# On-demand sync
# ---------------------------------------------------------------
@router.post("/sync/{provider}")
async def admin_sync_provider(provider: str, _: bool = Depends(verify_admin_key)):
    with _LOCK:
        running = SYNC_STATE["is_running"]
    if running:
        return {"status": "in_progress", "message": "A sync job is already running."}
    regions = _regions_list(provider)
    with _LOCK:
        SYNC_STATE["is_running"] = True
        SYNC_STATE["result"] = {}
        SYNC_STATE["last"] = None
    asyncio.create_task(
        asyncio.to_thread(
            lambda: _run_live_sync_sync(regions) or (SYNC_STATE.update(),)
        )
    )
    return {"status": "started", "message": f"Live sync queued for region(s): {', '.join(regions)}"}


# ---------------------------------------------------------------
# Backfill engine
# ---------------------------------------------------------------
@router.post("/backfill")
async def admin_start_backfill(req: BackfillRequest, _: bool = Depends(verify_admin_key)):
    with _LOCK:
        running = BACKFILL_STATE["is_running"]
    if running:
        return {"status": "busy", "message": "A backfill job is currently running."}
    start = date.fromisoformat(req.start_date)
    end = date.fromisoformat(req.end_date)
    if start > end:
        raise HTTPException(status_code=400, detail="start_date must be before end_date.")
    elif end > date.today():
        raise HTTPException(status_code=400, detail="end_date cannot be in the future.")
    elif req.mode not in ("backfill", "merge"):
        raise HTTPException(status_code=400, detail="mode must be 'backfill' or 'merge'.")

    with _LOCK:
        BACKFILL_STATE.update({
            "is_running": True,
            "status": "running",
            "mode": req.mode,
            "start_date": req.start_date,
            "end_date": req.end_date,
            "min_mag": req.min_mag,
            "regions": _regions_list(req.regions),
            "source": req.source,
            "windows_total": 0,
            "windows_done": 0,
            "fetched": 0,
            "inserted": 0,
            "per_region": {},
            "current_window": None,
            "log": [f"$ cema-ops backfill --source {req.source} --{req.mode} {req.start_date}..{req.end_date} M≥{req.min_mag}"],
            "error": None,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "finished_at": None,
        })
    params = req.model_dump()
    asyncio.create_task(asyncio.to_thread(lambda: _run_backfill_sync(params)))
    return {
        "status": "started",
        "message": f"{req.mode} queued {req.start_date} → {req.end_date} (M≥{req.min_mag}) "
                   f"for {', '.join(_regions_list(req.regions))}",
    }


@router.get("/backfill/status")
async def admin_backfill_status(_: bool = Depends(verify_admin_key)):
    with _LOCK:
        return dict(BACKFILL_STATE)


@router.post("/backfill/reset")
async def admin_backfill_reset(_: bool = Depends(verify_admin_key)):
    with _LOCK:
        if BACKFILL_STATE.get("is_running"):
            raise HTTPException(status_code=400, detail="Cannot reset engine while a job is currently running.")
        BACKFILL_STATE.update({
            "status": "idle",
            "is_running": False,
            "mode": None,
            "start_date": None,
            "end_date": None,
            "min_mag": None,
            "regions": [],
            "source": None,
            "windows_total": 0,
            "windows_done": 0,
            "fetched": 0,
            "inserted": 0,
            "per_region": {},
            "current_window": None,
            "log": ["$ cema ops deck armed — awaiting commands"],
            "error": None,
            "started_at": None,
            "finished_at": None,
        })
    return {"status": "ok", "message": "Backfill engine reset to IDLE."}


# ---------------------------------------------------------------
# Database maintenance tools
# ---------------------------------------------------------------
@router.get("/db/download")
async def admin_download_db(_: bool = Depends(verify_admin_key)):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for region in REGIONS:
            path = os.path.join(DB_DIR, f"eq-{region}.db")
            zf.write(path, arcname=f"eq-{region}.db")
    buf.seek(0)
    stamp = int(asyncio.get_event_loop().time())
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=cema-catalog-{stamp}.zip"},
    )


@router.post("/db/checkpoint-wal")
async def admin_checkpoint_wal(_: bool = Depends(verify_admin_key)):
    return checkpoint_wal()


@router.post("/db/vacuum")
async def admin_vacuum_db(_: bool = Depends(verify_admin_key)):
    return vacuum_db()


@router.post("/db/deduplicate")
async def admin_deduplicate_db(_: bool = Depends(verify_admin_key)):
    def run_dedup():
        report = {}
        for region in REGIONS:
            deleted_count = deduplicate(region)
            report[region] = {"duplicate_pairs": deleted_count}
        return report

    report = await asyncio.to_thread(run_dedup)
    return {"status": "ok", "deduplicate": report}


@router.post("/db/purge-noise")
async def admin_purge_noise(
    min_mag: float = Query(3.0, ge=3.0, le=5.0),
    _: bool = Depends(verify_admin_key),
):
    return purge_noise(min_mag)


@router.post("/db/purge-range")
async def admin_purge_range(
    req: PurgeRangeRequest,
    _: bool = Depends(verify_admin_key),
):
    try:
        s = date.fromisoformat(req.start_date)
        e = date.fromisoformat(req.end_date)
        if s > e:
            raise HTTPException(status_code=400, detail="start_date must be before or equal to end_date.")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {exc}")

    res = purge_date_range(req.start_date, req.end_date, req.regions)
    _log(f"purge range {req.start_date}..{req.end_date} [{', '.join(res['regions'])}] → {res['total_deleted']} deleted")
    return res


# ---------------------------------------------------------------
# Event moderation
# ---------------------------------------------------------------
@router.get("/earthquakes")
async def admin_list_earthquakes(
    region: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    min_mag: float = Query(0.0),
    max_mag: float = Query(10.0),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("event_time_utc"),
    sort_dir: str = Query("desc"),
    _: bool = Depends(verify_admin_key),
):
    page, total = query_admin_events(
        region=region, source=source, min_mag=min_mag, max_mag=max_mag,
        start_date=start_date, end_date=end_date, search=search,
        limit=limit, offset=offset, sort_by=sort_by, sort_dir=sort_dir,
    )
    return {"total": total, "limit": limit, "offset": offset, "items": page}


@router.post("/earthquakes")
async def admin_create_earthquake(
    event: ManualEarthquakeRequest, _: bool = Depends(verify_admin_key)
):
    if event.region not in REGIONS:
        raise HTTPException(status_code=400, detail="region must be 'canada' or 'china'.")
    path = os.path.join(DB_DIR, f"eq-{event.region}.db")
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL;")
    loc = assign_location(event.latitude, event.longitude, event.region)
    cur = conn.execute(
        "INSERT INTO earthquakes (region, event_time_utc, latitude, longitude, depth_km, magnitude, source, province, country)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (event.region, event.event_time_utc, event.latitude, event.longitude,
         event.depth_km, event.magnitude, event.source or "OPERATOR",
         loc.get("province"), loc.get("country_code")),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return {"status": "created", "event": {**event.model_dump(), "id": new_id}}


@router.delete("/earthquakes")
async def admin_delete_earthquake(
    req: DeleteEarthquakeRequest, _: bool = Depends(verify_admin_key)
):
    if req.region not in REGIONS:
        raise HTTPException(status_code=400, detail="region must be 'canada' or 'china'.")
    path = os.path.join(DB_DIR, f"eq-{req.region}.db")
    conn = sqlite3.connect(path)
    cur = conn.execute(
        "DELETE FROM earthquakes WHERE id = ? AND region = ?", (req.id, req.region)
    )
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Event not found.")
    return {"status": "deleted", "deleted": True, "id": req.id, "region": req.region}