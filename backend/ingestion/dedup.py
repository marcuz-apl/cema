"""CEMA deduplication engine — haversine <=25km + ±60s."""
import math, sqlite3, os
from datetime import datetime

DB_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi, dlam = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))

def find_duplicates(db_file, region, max_dist_km=25, max_time_diff_s=60):
    path = os.path.join(DB_DIR, db_file)
    if not os.path.exists(path):
        return []
    conn = sqlite3.connect(path)
    rows = conn.execute(
        "SELECT id, latitude, longitude, event_time_utc FROM earthquakes WHERE region = ? ORDER BY event_time_utc",
        (region,),
    ).fetchall()
    conn.close()

    # Pre-parse timestamps into float epoch seconds for high-performance comparison
    parsed = []
    for r in rows:
        t_str = r[3].replace("Z", "+00:00")
        try:
            ts = datetime.fromisoformat(t_str).timestamp()
        except Exception:
            continue
        parsed.append((r[0], r[1], r[2], ts))

    duplicates = []
    # Coarse degree filter: 1 deg lat ~= 111 km
    max_lat_diff = max_dist_km / 110.0

    n = len(parsed)
    for i in range(n):
        r1 = parsed[i]
        for j in range(i + 1, n):
            r2 = parsed[j]
            dt = r2[3] - r1[3]
            # Crucial optimization: rows are strictly ordered by event_time_utc.
            # Once dt > max_time_diff_s, all subsequent rows in the slice are also > max_time_diff_s!
            if dt > max_time_diff_s:
                break
            if abs(r2[1] - r1[1]) > max_lat_diff:
                continue
            dist = haversine(r1[1], r1[2], r2[1], r2[2])
            if dist <= max_dist_km:
                duplicates.append((r1[0], r2[0], dist, dt))

    return duplicates

def deduplicate(region, max_dist_km=25, max_time_diff_s=60):
    db_file = f"eq-{region}.db"
    dups = find_duplicates(db_file, region, max_dist_km, max_time_diff_s)
    if dups:
        to_delete = list(set(d[1] for d in dups))
        path = os.path.join(DB_DIR, db_file)
        conn = sqlite3.connect(path)
        # Execute deletions in clean batches
        for start in range(0, len(to_delete), 500):
            chunk = to_delete[start : start + 500]
            placeholders = ",".join("?" * len(chunk))
            conn.execute(f"DELETE FROM earthquakes WHERE id IN ({placeholders})", chunk)
        conn.commit()
        conn.close()
        return len(to_delete)
    return 0
