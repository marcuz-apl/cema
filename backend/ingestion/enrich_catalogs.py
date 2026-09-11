#!/usr/bin/env python3
"""Batch-enrich CEMA databases with country and province boundaries.

Updates:
  - data/eq-canada.db: assigns country ('CA', 'US', etc.) and province
  - data/eq-china.db:  assigns country ('CN', 'JP', 'RU', 'TJ', etc.) and province
WAL-safe transaction processing with progress reporting.
"""
import os
import sqlite3
import time
from country_assigner import assign_location

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "..", "..", "data")


def ensure_column(conn, table, column, col_type):
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    cols = [c[1] for c in cur.fetchall()]
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        conn.commit()
        print(f"Added column {column} ({col_type}) to {table}")


def enrich_database(db_file, sector):
    path = os.path.join(DB_DIR, db_file)
    if not os.path.exists(path):
        print(f"Database {path} not found.")
        return

    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL;")
    ensure_column(conn, "earthquakes", "country", "TEXT DEFAULT NULL")

    rows = conn.execute(
        "SELECT id, latitude, longitude FROM earthquakes"
    ).fetchall()
    total = len(rows)
    print(f"[{sector}] Enriching {total} records from {db_file}...")

    updated = 0
    country_counts = {}
    prov_counts = 0

    batch = []
    t0 = time.time()
    for i, (rid, lat, lon) in enumerate(rows, 1):
        loc = assign_location(lat, lon, sector)
        c_code = loc["country_code"]
        p_name = loc["province"]
        batch.append((c_code, p_name, rid))
        country_counts[c_code] = country_counts.get(c_code, 0) + 1
        if p_name:
            prov_counts += 1

        if len(batch) >= 1000:
            conn.executemany(
                "UPDATE earthquakes SET country = ?, province = ? WHERE id = ?",
                batch
            )
            conn.commit()
            updated += len(batch)
            batch = []

    if batch:
        conn.executemany(
            "UPDATE earthquakes SET country = ?, province = ? WHERE id = ?",
            batch
        )
        conn.commit()
        updated += len(batch)

    conn.close()
    elapsed = time.time() - t0
    print(f"[{sector}] Done in {elapsed:.2f}s ({updated}/{total} updated, {prov_counts} provinces assigned).")
    print(f"[{sector}] Country breakdown:")
    for code, cnt in sorted(country_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {code:4}: {cnt:5} events ({cnt/total*100:5.1f}%)")


def main():
    enrich_database("eq-canada.db", "canada")
    enrich_database("eq-china.db", "china")


if __name__ == "__main__":
    main()
