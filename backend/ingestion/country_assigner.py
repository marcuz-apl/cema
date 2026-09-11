#!/usr/bin/env python3
"""High-performance offline country and province boundary classifier for CEMA.

Resolves sovereign country (ISO 3166-1 alpha-2) and province/state names
using bounding-box pre-filtering and ray-casting point-in-geometry.
For Canada and US, assigns official 2-letter postal abbreviations (e.g. BC, YT, WY, ID).
Zero external API calls. Sub-millisecond execution per coordinate.
"""
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DATA = os.path.join(BASE_DIR, "..", "data")
FRONTEND_DATA = os.path.join(BASE_DIR, "..", "..", "frontend", "data")

COUNTRIES_FILE = os.path.join(BACKEND_DATA, "world_countries.geojson")
US_STATES_FILE = os.path.join(BACKEND_DATA, "us_states.geojson")
PROV_CANADA_FILE = os.path.join(FRONTEND_DATA, "provinces-canada.geojson")
PROV_CHINA_FILE = os.path.join(FRONTEND_DATA, "provinces-china.geojson")

CA_PROV_CODES = {
    "Alberta": "AB", "British Columbia": "BC", "Manitoba": "MB", "New Brunswick": "NB",
    "Newfoundland and Labrador": "NL", "Nova Scotia": "NS", "Northwest Territories": "NT",
    "Nunavut": "NU", "Ontario": "ON", "Prince Edward Island": "PE", "Québec": "QC", "Quebec": "QC",
    "Saskatchewan": "SK", "Yukon": "YT"
}

US_STATE_CODES = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA",
    "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE", "District of Columbia": "DC",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL",
    "Indiana": "IN", "Iowa": "IA", "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA",
    "Maine": "ME", "Maryland": "MD", "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN",
    "Mississippi": "MS", "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK", "Oregon": "OR",
    "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC", "South Dakota": "SD",
    "Tennessee": "TN", "Texas": "TX", "Utah": "UT", "Vermont": "VT", "Virginia": "VA",
    "Washington": "WA", "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY", "Puerto Rico": "PR"
}


def _calc_bbox(geom):
    """Compute (min_lat, min_lon, max_lat, max_lon) for a geometry."""
    min_lat, max_lat = 90.0, -90.0
    min_lon, max_lon = 180.0, -180.0
    gtype = geom.get("type")

    def _update_ring(ring):
        nonlocal min_lat, max_lat, min_lon, max_lon
        for lon, lat in ring:
            if lat < min_lat: min_lat = lat
            if lat > max_lat: max_lat = lat
            if lon < min_lon: min_lon = lon
            if lon > max_lon: max_lon = lon

    if gtype == "Polygon":
        for ring in geom.get("coordinates", []):
            _update_ring(ring)
    elif gtype == "MultiPolygon":
        for poly in geom.get("coordinates", []):
            for ring in poly:
                _update_ring(ring)
    return (min_lat, min_lon, max_lat, max_lon)


def _point_in_polygon(lat, lon, ring):
    """Ray casting: ring is list of [lon, lat] points."""
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def _point_in_geometry(lat, lon, geom):
    """Check if point is inside Polygon or MultiPolygon with hole handling."""
    gtype = geom.get("type")
    if gtype == "Polygon":
        coords = geom.get("coordinates", [])
        if not coords:
            return False
        if not _point_in_polygon(lat, lon, coords[0]):
            return False
        for hole in coords[1:]:
            if _point_in_polygon(lat, lon, hole):
                return False
        return True
    elif gtype == "MultiPolygon":
        for poly in geom.get("coordinates", []):
            if not poly:
                continue
            if not _point_in_polygon(lat, lon, poly[0]):
                continue
            in_hole = any(_point_in_polygon(lat, lon, hole) for hole in poly[1:])
            if not in_hole:
                return True
        return False
    return False


class CountryAssigner:
    _instance = None

    def __init__(self):
        self.countries = []
        self.provinces_ca = []
        self.provinces_cn = []
        self.us_states = []
        self._load_data()

    def _load_data(self):
        if os.path.exists(COUNTRIES_FILE):
            with open(COUNTRIES_FILE, "r", encoding="utf-8") as f:
                gj = json.load(f)
            for f in gj.get("features", []):
                props = f.get("properties", {})
                geom = f.get("geometry", {})
                if geom and geom.get("type") in {"Polygon", "MultiPolygon"}:
                    bbox = _calc_bbox(geom)
                    self.countries.append((
                        props.get("name", "Unknown"),
                        props.get("code", "??"),
                        bbox,
                        geom
                    ))

        if os.path.exists(PROV_CANADA_FILE):
            with open(PROV_CANADA_FILE, "r", encoding="utf-8") as f:
                gj = json.load(f)
            for f in gj.get("features", []):
                props = f.get("properties", {})
                raw_name = props.get("name") or props.get("code") or ""
                # Use 2-letter postal code
                code = props.get("code") or CA_PROV_CODES.get(raw_name, raw_name)
                geom = f.get("geometry", {})
                if geom and geom.get("type") in {"Polygon", "MultiPolygon"}:
                    bbox = _calc_bbox(geom)
                    self.provinces_ca.append((code, bbox, geom))

        if os.path.exists(PROV_CHINA_FILE):
            with open(PROV_CHINA_FILE, "r", encoding="utf-8") as f:
                gj = json.load(f)
            for f in gj.get("features", []):
                props = f.get("properties", {})
                name = props.get("name") or props.get("code") or ""
                geom = f.get("geometry", {})
                if geom and geom.get("type") in {"Polygon", "MultiPolygon"}:
                    bbox = _calc_bbox(geom)
                    self.provinces_cn.append((name, bbox, geom))

        if os.path.exists(US_STATES_FILE):
            with open(US_STATES_FILE, "r", encoding="utf-8") as f:
                gj = json.load(f)
            for f in gj.get("features", []):
                props = f.get("properties", {})
                raw_name = props.get("name") or ""
                # Use 2-letter postal code
                code = US_STATE_CODES.get(raw_name, raw_name)
                geom = f.get("geometry", {})
                if geom and geom.get("type") in {"Polygon", "MultiPolygon"}:
                    bbox = _calc_bbox(geom)
                    self.us_states.append((code, bbox, geom))

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = CountryAssigner()
        return cls._instance

    def assign(self, lat: float, lon: float, sector: str = None):
        """Classify (lat, lon) into country and province.

        Returns:
            dict: { 'country_code': str, 'country_name': str, 'province': Optional[str] }
        """
        # 1. First check if it falls inside Canadian provinces (returns 2-letter code e.g. BC, YT)
        if sector == "canada" or sector is None:
            for code, bbox, geom in self.provinces_ca:
                if bbox[0] <= lat <= bbox[2] and bbox[1] <= lon <= bbox[3]:
                    if _point_in_geometry(lat, lon, geom):
                        return {
                            "country_code": "CA",
                            "country_name": "Canada",
                            "province": code
                        }

        # 2. Check if inside US states (returns 2-letter code e.g. WY, ID, AK)
        if sector == "canada" or sector is None:
            for code, bbox, geom in self.us_states:
                if bbox[0] <= lat <= bbox[2] and bbox[1] <= lon <= bbox[3]:
                    if _point_in_geometry(lat, lon, geom):
                        return {
                            "country_code": "US",
                            "country_name": "United States",
                            "province": code
                        }

        # 3. Check if it falls inside Chinese provinces
        if sector == "china" or sector is None:
            for name, bbox, geom in self.provinces_cn:
                if bbox[0] <= lat <= bbox[2] and bbox[1] <= lon <= bbox[3]:
                    if _point_in_geometry(lat, lon, geom):
                        return {
                            "country_code": "CN",
                            "country_name": "China",
                            "province": name
                        }

        # 4. Check sovereign country polygons
        for name, code, bbox, geom in self.countries:
            if bbox[0] <= lat <= bbox[2] and bbox[1] <= lon <= bbox[3]:
                if _point_in_geometry(lat, lon, geom):
                    prov = None
                    if code == "US":
                        for s_code, s_bbox, s_geom in self.us_states:
                            if s_bbox[0] <= lat <= s_bbox[2] and s_bbox[1] <= lon <= s_bbox[3]:
                                if _point_in_geometry(lat, lon, s_geom):
                                    prov = s_code
                                    break
                    elif code == "CA":
                        for c_code, c_bbox, c_geom in self.provinces_ca:
                            if c_bbox[0] <= lat <= c_bbox[2] and c_bbox[1] <= lon <= c_bbox[3]:
                                if _point_in_geometry(lat, lon, c_geom):
                                    prov = c_code
                                    break
                    return {
                        "country_code": code,
                        "country_name": name,
                        "province": prov
                    }

        # 5. If outside all land boundaries, classify as Offshore
        return {
            "country_code": "OFS",
            "country_name": "Offshore",
            "province": None
        }


def assign_location(lat: float, lon: float, sector: str = None):
    return CountryAssigner.get_instance().assign(lat, lon, sector)


if __name__ == "__main__":
    test_points = [
        (49.2827, -123.1207, "canada"),  # Vancouver, BC
        (43.7742, -105.3225, "canada"),  # Gillette, WY (US)
        (60.5098, -140.0887, "canada"),  # Yakutat, AK (US) / YT border
        (47.5595,  -92.6648, "canada"),  # MN (US)
        (30.6586,  104.0648, "china"),   # Chengdu, Sichuan (CN)
        (37.3514,   74.5557, "china"),   # Tajikistan
    ]
    for lat, lon, sec in test_points:
        res = assign_location(lat, lon, sec)
        print(f"({lat:7.4f}, {lon:9.4f}) [{sec:6}] -> {res['country_code']:3} | {res['country_name']:15} | {res['province']}")
