import sqlite3, os

DB_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
os.makedirs(DB_DIR, exist_ok=True)

SCHEMA = """
CREATE TABLE IF NOT EXISTS earthquakes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    region TEXT,
    event_time_utc TEXT,
    latitude REAL,
    longitude REAL,
    depth_km REAL,
    magnitude REAL,
    source TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_time ON earthquakes(event_time_utc);
CREATE INDEX IF NOT EXISTS idx_mag ON earthquakes(magnitude);
CREATE INDEX IF NOT EXISTS idx_lat_lon ON earthquakes(latitude, longitude);
"""

for db_file in ["eq-canada.db", "eq-china.db"]:
    path = os.path.join(DB_DIR, db_file)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()

print("DBs initialized")
