#!/usr/bin/env python3
import sqlite3, os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "..", "..", "data")

SEEDS = {
    "eq-canada.db": ("canada", [
        ("2024-03-15T14:32:00Z", 49.2827, -123.1207, 10.0, 4.2, "NRCan"),
        ("2024-01-08T09:15:00Z", 60.4861, -134.6395, 5.0, 3.8, "NRCan"),
        ("2023-11-22T22:05:00Z", 51.0447, -114.0719, 15.0, 3.5, "NRCan"),
    ]),
    "eq-china.db": ("china", [
        ("2024-06-10T03:45:00Z", 35.8617, 104.1954, 12.0, 5.1, "CENC"),
        ("2024-02-28T11:20:00Z", 23.6978, 121.9763, 8.0, 4.7, "CENC"),
        ("2024-05-01T16:55:00Z", 31.2304, 103.8263, 20.0, 3.9, "CENC"),
    ]),
}

for db_file, (region, rows) in SEEDS.items():
    path = os.path.join(DB_DIR, db_file)
    conn = sqlite3.connect(path)
    for r in rows:
        conn.execute(
            "INSERT OR IGNORE INTO earthquakes (region, event_time_utc, latitude, longitude, depth_km, magnitude, source) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (region, r[0], r[1], r[2], r[3], r[4], r[5])
        )
    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM earthquakes").fetchone()[0]
    print(f"{db_file} seeded — {count} total records")
    conn.close()
