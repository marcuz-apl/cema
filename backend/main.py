from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List
import sqlite3, os

app = FastAPI(title="CEMA API", version="v0.2.0")
DB_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")

class Earthquake(BaseModel):
    id: int; region: str; event_time_utc: Optional[str] = None
    latitude: Optional[float] = None; longitude: Optional[float] = None
    depth_km: Optional[float] = None; magnitude: Optional[float] = None; source: Optional[str] = None

@app.get("/")
async def root(): return {"service":"CEMA","version":"v0.2.0","regions":["canada","china"]}

@app.get("/api/v1/earthquakes")
async def list_earthquakes(region: Optional[str] = None, min_mag: float = 0, max_mag: float = 10, limit: int = 50):
    results = []
    for db_file in ["eq-canada.db", "eq-china.db"]:
        region_filter = "canada" if "canada" in db_file else "china"
        if region and region != region_filter and region != "all": continue
        conn = sqlite3.connect(os.path.join(DB_DIR, db_file))
        cursor = conn.execute("SELECT * FROM earthquakes WHERE magnitude >= ? AND magnitude <= ? ORDER BY event_time_utc DESC LIMIT ?", (min_mag, max_mag, limit))
        for row in cursor.fetchall():
            results.append({"id": row[0], "region": row[1], "event_time_utc": row[2], "latitude": row[3], "longitude": row[4], "depth_km": row[5], "magnitude": row[6], "source": row[7]})
    return {"region": region or "both", "count": len(results), "items": results}

@app.get("/api/v1/earthquakes/stats")
async def stats():
    total = 0
    for db_file in ["eq-canada.db", "eq-china.db"]:
        conn = sqlite3.connect(os.path.join(DB_DIR, db_file))
        total += conn.execute("SELECT COUNT(*) FROM earthquakes").fetchone()[0]
    return {"total": total, "regions": ["canada", "china"]}
