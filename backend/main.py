from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
from contextlib import asynccontextmanager
import sqlite3, os, json, time, asyncio
from datetime import datetime, date, timedelta, timezone
from .ingestion import backfill

from . import admin as admin_module

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
DB_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DB_FILES = ["eq-canada.db", "eq-china.db"]

def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
    for db_file in DB_FILES:
        path = os.path.join(DB_DIR, db_file)
        if not os.path.exists(path):
            conn = sqlite3.connect(path)
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("CREATE TABLE IF NOT EXISTS earthquakes (id INTEGER PRIMARY KEY AUTOINCREMENT, region TEXT, province TEXT, event_time_utc TEXT, latitude REAL, longitude REAL, depth_km REAL, magnitude REAL, source TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, country TEXT DEFAULT NULL)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_time ON earthquakes(event_time_utc)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mag ON earthquakes(magnitude)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_lat_lon ON earthquakes(latitude, longitude)")
            conn.commit()
            conn.close()
        else:
            conn = sqlite3.connect(path)
            conn.execute("PRAGMA journal_mode=WAL;")
            # Ensure country column exists
            cols = [c[1] for c in conn.execute("PRAGMA table_info(earthquakes)").fetchall()]
            if "country" not in cols:
                conn.execute("ALTER TABLE earthquakes ADD COLUMN country TEXT DEFAULT NULL")
                conn.commit()
            count = conn.execute("SELECT COUNT(*) FROM earthquakes").fetchone()[0]
            conn.close()
            if count == 0:
                seed_data = {
                    "eq-canada.db": [("2024-03-15T14:32:00Z", 49.2827, -123.1207, 10.0, 4.2, "NRCan"), ("2024-01-08T09:15:00Z", 60.4861, -134.6395, 5.0, 3.8, "NRCan"), ("2023-11-22T22:05:00Z", 51.0447, -114.0719, 15.0, 3.5, "NRCan")],
                    "eq-china.db": [("2024-06-10T03:45:00Z", 35.8617, 104.1954, 12.0, 5.1, "CENC"), ("2024-02-28T11:20:00Z", 23.6978, 121.9763, 8.0, 4.7, "CENC"), ("2024-05-01T16:55:00Z", 31.2304, 103.8263, 20.0, 3.9, "CENC")]
                }
                if db_file in seed_data:
                    conn = sqlite3.connect(path)
                    for r in seed_data[db_file]:
                        conn.execute("INSERT OR IGNORE INTO earthquakes (region, event_time_utc, latitude, longitude, depth_km, magnitude, source) VALUES (?, ?, ?, ?, ?, ?, ?)", (db_file.replace("eq-","").replace(".db",""), r[0], r[1], r[2], r[3], r[4], r[5]))
                    conn.commit()
                    conn.close()


async def background_poller():
    """Background cron polling authoritative seismic data sources every 180 seconds (3 minutes)."""
    # Initial startup delay so DB initialization and FastAPI boot finish cleanly
    await asyncio.sleep(6)
    while True:
        try:
            # Check if auto-poller is enabled
            with admin_module._LOCK:
                poller_info = admin_module.SYNC_STATE.setdefault("auto_poller", {
                    "enabled": True,
                    "interval_sec": 180,
                    "last_run": None,
                    "total_runs": 0,
                    "last_new_events": 0,
                })
                enabled = poller_info.get("enabled", False)
                busy = admin_module.BACKFILL_STATE.get("is_running") or admin_module.SYNC_STATE.get("is_running")

            if enabled and not busy:
                def _do_poll():
                    start = date.today() - timedelta(days=2)
                    end = date.today()
                    return backfill.run_backfill_job(
                        regions=list(backfill.REGIONS),
                        start=start,
                        end=end,
                        min_mag=3.0,
                        chunk_days=2,
                        replace=False,
                        on_log=lambda m: admin_module._log(f"[cron 3m] {m}"),
                    )

                results = await asyncio.to_thread(_do_poll)
                total_new = sum(r.get("events", 0) for r in results.values() if isinstance(r, dict))
                with admin_module._LOCK:
                    p = admin_module.SYNC_STATE.setdefault("auto_poller", {})
                    p["last_run"] = datetime.now(timezone.utc).isoformat()
                    p["total_runs"] = p.get("total_runs", 0) + 1
                    p["last_new_events"] = total_new
                admin_module._log(f"[cron 3m] sync complete: {total_new} new M≥3.0 events added across catalogs")
        except asyncio.CancelledError:
            break
        except Exception as exc:
            admin_module._log(f"[cron 3m] sync error: {exc}")

        # Sleep for the 3-minute interval (180s)
        await asyncio.sleep(180)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    poller_task = asyncio.create_task(background_poller())
    try:
        yield
    finally:
        if poller_task:
            poller_task.cancel()
            try:
                await poller_task
            except asyncio.CancelledError:
                pass

app = FastAPI(title="CEMA API", version="0.5.0", lifespan=lifespan)

app.include_router(admin_module.router)
app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="css")
app.mount("/data", StaticFiles(directory=os.path.join(FRONTEND_DIR, "data")), name="data")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

class Earthquake(BaseModel):
    id: int
    region: str
    province: Optional[str] = None
    country: Optional[str] = None
    event_time_utc: str
    latitude: float
    longitude: float
    depth_km: float
    magnitude: float
    source: str

def get_db(region: Optional[str] = None):
    if region and region != "all":
        db_file = f"eq-{region}.db"
        if db_file in DB_FILES:
            return [db_file]
        return []
    return DB_FILES

def query_db(db_file, min_mag, max_mag, limit, region_filter, start_date=None, end_date=None, bbox=None):
    conn = sqlite3.connect(os.path.join(DB_DIR, db_file))
    conn.row_factory = sqlite3.Row
    sql = "SELECT * FROM earthquakes WHERE magnitude >= ? AND magnitude <= ?"
    params = [min_mag, max_mag]
    if start_date:
        sql += " AND event_time_utc >= ?"
        params.append(start_date)
    if end_date:
        sql += " AND event_time_utc <= ?"
        params.append(end_date)
    if region_filter:
        sql += " AND region = ?"
        params.append(region_filter)
    if bbox:
        sw_lat, sw_lon, ne_lat, ne_lon = bbox
        sql += " AND latitude >= ? AND latitude <= ? AND longitude >= ? AND longitude <= ?"
        params.extend([sw_lat, ne_lat, sw_lon, ne_lon])
    sql += " ORDER BY event_time_utc DESC"
    if limit:
        sql += " LIMIT ?"
        params.append(limit)
    rows = conn.execute(sql, params).fetchall()
    results = [dict(r) for r in rows]
    conn.close()
    return results

@app.get("/")
async def root():
    return FileResponse(
        os.path.join(FRONTEND_DIR, "index.html"),
        headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}
    )

@app.get("/admin", include_in_schema=False)
async def admin_panel():
    return FileResponse(
        os.path.join(FRONTEND_DIR, "admin.html"),
        headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}
    )

@app.get("/api/v1/info")
async def info():
    return {"service": "CEMA", "version": "0.5.0", "regions": ["canada", "china"]}

@app.get("/api/v1/earthquakes")
async def list_earthquakes(
    region: Optional[str] = Query(None),
    min_mag: float = Query(0),
    max_mag: float = Query(10),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    bbox: Optional[str] = Query(None),
    limit: Optional[int] = Query(None),
    offset: int = Query(0)
):
    bbox_coords = None
    if bbox:
        try:
            parts = bbox.split(",")
            bbox_coords = (float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3]))
        except (ValueError, IndexError):
            bbox_coords = None
    all_results = []
    for db_file in get_db(region):
        region_filter = "canada" if "canada" in db_file else "china"
        all_results.extend(query_db(db_file, min_mag, max_mag, limit, region_filter, start_date, end_date, bbox_coords))
    all_results.sort(key=lambda x: x.get("event_time_utc", ""), reverse=True)
    if limit:
        all_results = all_results[offset:offset + limit]
    return {"region": region or "all", "count": len(all_results), "items": all_results}

@app.get("/api/v1/earthquakes/stats")
async def stats():
    total = 0
    max_mag = 0
    per_region = {}
    day_ago = "strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-1 day')"
    for db_file in DB_FILES:
        conn = sqlite3.connect(os.path.join(DB_DIR, db_file))
        count = conn.execute("SELECT COUNT(*) FROM earthquakes").fetchone()[0]
        mx = conn.execute("SELECT MAX(magnitude) FROM earthquakes").fetchone()[0]
        h24 = conn.execute(
            f"SELECT COUNT(*) FROM earthquakes WHERE event_time_utc >= {day_ago}"
        ).fetchone()[0]
        conn.close()
        total += count
        if mx and mx > max_mag:
            max_mag = mx
        region = "canada" if "canada" in db_file else "china"
        per_region[region] = {"total": count, "max_magnitude": mx or 0, "last_24h": h24}
    return {"total": total, "per_region": per_region, "max_magnitude": max_mag, "regions": ["canada", "china"]}

@app.get("/api/v1/live")
async def live():
    def event_stream():
        while True:
            data = {"status": "live", "regions": ["canada", "china"], "timestamp": time.time()}
            for db_file in DB_FILES:
                conn = sqlite3.connect(os.path.join(DB_DIR, db_file))
                row = conn.execute("SELECT * FROM earthquakes ORDER BY event_time_utc DESC LIMIT 1").fetchone()
                conn.close()
                if row:
                    data["latest"] = {"region": row[1], "magnitude": row[6], "time": row[2]}
            yield f"data: {json.dumps(data)}\n\n"
            time.sleep(5)
    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.get("/api/v1/boundaries/tectonic")
async def tectonic_boundaries():
    return JSONResponse(content={"type": "FeatureCollection", "features": []})

@app.get("/api/v1/boundaries/provinces")
async def provinces():
    return JSONResponse(content={"type": "FeatureCollection", "features": []})


