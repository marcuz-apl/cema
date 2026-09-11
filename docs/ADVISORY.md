# CEMA Design Advisory — Canada / China Focus

## 1. Data Source Architecture & Regional Routing

### Canada
- **Primary Source**: Natural Resources Canada (NRCan) seismic bulletins and live feeds.
- **Secondary / Fallback**: USGS earthquake API filtered to Canada bounding box (~42°N–83°N, 168°W–52°W).
- **Geospatial Boundaries**: Canadian provincial/territorial boundaries GeoJSON (`frontend/data/provinces-canada.geojson`); North American plate boundary segments (`frontend/data/faults-canada.geojson`).

### China
- **Primary Source**: China Earthquake Networks Center (CENC) real-time and catalog feeds.
- **Secondary / Fallback**: USGS earthquake API filtered to China bounding box (~18°N–54°N, 73°E–135°E).
- **Geospatial Boundaries**: China provincial and autonomous region boundaries GeoJSON (`frontend/data/provinces-china.geojson`); Eurasian / Indo-Australian plate boundary segments (`frontend/data/faults-china.geojson`).

---

## 2. Database Topology — 3 Independent Catalogs

CEMA isolates persistence across three purpose-built SQLite databases in `data/`:

1. **`data/eq-canada.db`**: Canada-exclusive seismic events.
2. **`data/eq-china.db`**: China-exclusive seismic events.
3. **`data/cema-admin.db`**: Administrative audit logs, pipeline telemetry, and operator configuration.

### Design Benefits:
- **Write-Ahead Logging (WAL)**: `PRAGMA journal_mode=WAL;` enables concurrent reads during high-frequency ingestion.
- **B-Tree Indexes**: Rapid query evaluation on `origintimeutc`, `magnitude`, `latitude`, `longitude`.
- **Deduplication Engine**: Spatial distance ≤ 25 km, temporal window ± 60 s (`backend/ingestion/dedup.py`).
- **Isolation**: Prevents monolithic database locks; allows independent backfilling, purging, and backup per jurisdiction.

---

## 3. Spatial Enrichment & Sovereign Border Assignment

The catalog enrichment engine (`backend/ingestion/country_assigner.py` and `assign_provinces.py`) verifies:
- Sovereign country identification via high-resolution polygons (`backend/data/world_countries.geojson`).
- 2-letter postal abbreviation mapping for all Canadian provinces/territories and adjacent US states.
- Exact province attribution for Chinese administrative divisions.
- Strict magnitude floor: M 3.0 floor policy maintained across app filters and historical backfill.

---

## 4. Audio Sonification & Cartographic HUD

- **Acoustic Chirps**: Synthetic Web Audio API engine mapping earthquake magnitude exponentially to frequency (Hz) and gain.
- **Contextual Clocks**: Synchronized real-time clocks displaying Canada Mountain Standard Time (MST) and China Standard Time (CST/GMT+8) alongside UTC.
- **Canvas Rendering**: Leaflet Canvas rendering mode prevents DOM bloat when visualizing thousands of historical seismic events.
- **Export Capabilities**: Direct GeoJSON, CSV, and PNG high-resolution bulletin exports.

---

## 5. Operations & Admin Security

- Passkey-protected administrative endpoints mounted at `/admin` and `/api/v1/admin/*`.
- Multi-source historical backfill engine supporting 365-day chunking down to Year 2000.
- Safe-guarded event purging with explicit warning confirmation modal.
- Live Operator.Log terminal stream for real-time operational transparency.
