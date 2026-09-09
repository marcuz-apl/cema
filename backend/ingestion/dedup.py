"""Dedup: haversine <=25km + ±60s."""
import math, sqlite3, os
from datetime import datetime, timedelta

DB_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = map(math.radians, [lat1, lat2])
    dphi, dlam = map(math.radians, [lat2 - lat1, lon2 - lon1])
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))

def find_duplicates(db_file, region, max_dist_km=25, max_time_diff_s=60):
    path = os.path.join(DB_DIR, db_file)
    conn = sqlite3.connect(path)
    rows = conn.execute("SELECT id, latitude, longitude, event_time_utc FROM earthquakes WHERE region = ? ORDER BY event_time_utc", (region,)).fetchall()
    duplicates = []
    for i, r1 in enumerate(rows):
        for r2 in rows[i + 1:]:
            dist = haversine(r1[1], r1[2], r2[1], r2[2])
            t1 = datetime.fromisoformat(r1[3].replace("Z", "+00:00"))
            t2 = datetime.fromisoformat(r2[3].replace("Z", "+00:00"))
            dt = abs((t1 - t2).total_seconds())
            if dist <= max_dist_km and dt <= max_time_diff_s:
                duplicates.append((r1[0], r2[0], dist, dt))
    conn.close()
    return duplicates

def deduplicate(region, max_dist_km=25, max_time_diff_s=60):
    db_file = f"eq-{region}.db"
    dups = find_duplicates(db_file, region, max_dist_km, max_time_diff_s)
    if dups:
        to_delete = set(d[1] for d in dups)
        path = os.path.join(DB_DIR, db_file)
        conn = sqlite3.connect(path)
        for did in to_delete:
            conn.execute("DELETE FROM earthquakes WHERE id = ?", (did,))
        conn.commit()
        conn.close()
    return len(dups)
