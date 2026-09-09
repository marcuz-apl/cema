#!/usr/bin/env python3
"""Populate initial historical archive samples for Canada and China."""
import sqlite3
import os

DB_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")

def seed(name, region, rows):
    path = os.path.join(DB_DIR, name)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL;")
    for r in rows:
        conn.execute("INSERT INTO earthquakes (region, event_time_utc, latitude, longitude, depth_km, magnitude, source) VALUES (?, ?, ?, ?, ?, ?, ?)", r)
    conn.commit()
    count = conn.execute("SELECT count(*) FROM earthquakes").fetchone()[0]
    conn.close()
    print(f"Seeded {name}: {count} records ({region})")

canada_samples = [
    ("canada", "2024-03-15T14:32:00Z", 49.2827, -123.1207, 10.0, 4.2, "NRCan"),
    ("canada", "2024-01-08T09:15:00Z", 60.4861, -134.6395, 5.0, 3.8, "NRCan"),
    ("canada", "2023-11-22T22:05:00Z", 51.0447, -114.0719, 15.0, 3.5, "NRCan"),
]

china_samples = [
    ("china", "2024-06-10T03:45:00Z", 35.8617, 104.1954, 12.0, 5.1, "CENC"),
    ("china", "2024-02-28T11:20:00Z", 23.6978, 121.9763, 8.0, 4.7, "CENC"),
    ("china", "2024-05-01T16:55:00Z", 31.2304, 103.8263, 20.0, 3.9, "CENC"),
]

if __name__ == "__main__":
    seed("eq-canada.db", "canada", canada_samples)
    seed("eq-china.db", "china", china_samples)
