#!/usr/bin/env python3
"""Assign province to every earthquake using the GeoJSON province boundaries.

Affected DBs:
  - data/eq-canada.db  (region: canada)
  - data/eq-china.db   (region: china)

Point-in-polygon uses ray casting; supports Polygon and MultiPolygon.
Both DB files are updated in place (WAL-safe).
"""
import json
import os
import sqlite3

BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
DB_DIR = os.path.join(BASE_DIR, "data")
GEOJSON_DIR = os.path.join(BASE_DIR, "frontend", "data")
REGIONS = {
    "canada": "provinces-canada.geojson",
    "china": "provinces-china.geojson",
}


def _rings(geom):
    """Yield list of (name, ring) matching properties; returns list of rings per feature."""
    pass


def point_in_polygon(lat, lon, ring):
    """Ray casting: ring is a list of (lon, lat) vertices."""
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def point_in_geometry(lat, lon, geom):
    """Check point inside a Polygon or MultiPolygon geometry."""
    gtype = geom.get("type")
    if gtype == "Polygon":
        # first ring is exterior; holes are subsequent rings
        coords = geom.get("coordinates", [])
        if not coords:
            return False
        if not point_in_polygon(lat, lon, coords[0]):
            return False
        for hole in coords[1:]:
            if point_in_polygon(lat, lon, hole):
                return False
        return True
    if gtype == "MultiPolygon":
        for poly in geom.get("coordinates", []):
            if not poly:
                continue
            if not point_in_polygon(lat, lon, poly[0]):
                continue
            in_hole = any(point_in_polygon(lat, lon, hole) for hole in poly[1:])
            if not in_hole:
                return True
        return False
    return False


def build_province_lookup(geojson_path):
    """Return list of (name, code, geometry)."""
    with open(geojson_path) as f:
        gj = json.load(f)
    lookup = []
    for feat in gj.get("features", []):
        props = feat.get("properties", {})
        name = props.get("name") or props.get("code") or ""
        code = props.get("code") or name
        geom = feat.get("geometry", {})
        if geom and geom.get("type") in {"Polygon", "MultiPolygon"}:
            lookup.append((name, code, geom))
    return lookup


def assign(lookup, lat, lon):
    for name, code, geom in lookup:
        if point_in_geometry(lat, lon, geom):
            return name
    return None


def process_region(region, geojson_name):
    lookup = build_province_lookup(os.path.join(GEOJSON_DIR, geojson_name))
    conn = sqlite3.connect(os.path.join(DB_DIR, f"eq-{region}.db"))
    conn.execute("PRAGMA journal_mode=WAL;")
    rows = conn.execute(
        "SELECT id, latitude, longitude FROM earthquakes WHERE region = ?",
        (region,),
    ).fetchall()
    updated = 0
    skipped = 0
    for rid, lat, lon in rows:
        prov = assign(lookup, lat, lon)
        if prov:
            conn.execute(
                "UPDATE earthquakes SET province = ? WHERE id = ?", (prov, rid)
            )
            updated += 1
        else:
            skipped += 1
    conn.commit()
    conn.close()
    return {"region": region, "updated": updated, "unmatched": skipped}


def main():
    for region, geojson_name in REGIONS.items():
        print(process_region(region, geojson_name))


if __name__ == "__main__":
    main()