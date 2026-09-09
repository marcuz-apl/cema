# Product Requirements Document (PRD) — CEMA

## 1. Executive Summary

**CEMA** (Canada / China Earthquake Monitoring & Alert system) is a real-time seismic observatory platform monitoring earthquake activity across Canada and China. It delivers live telemetry, interactive geospatial cartography, historical catalogs, and multimodal playback for researchers, emergency responders, and the general public.

## 2. Scope & Objectives

- Real-time ingestion from authoritative seismic agencies for Canada (Natural Resources Canada — NRCan, USGS for cross-border) and China (China Earthquake Networks Center — CENC, USGS).
- Two independent SQLite database files (`data/eq-canada.db`, `data/eq-china.db`) in WAL mode, each with indexed event catalogs.
- Interactive single-page web application (SPA) mimicking a modern observatory UI: 3-column desktop header (brand left, telemetry HUD center, action dock right), filter bar, zoom/theme toggler, floating magnitude bar, lower-left layers drawer, lower-center player bar.
- Zero cloud dependency; fully self-contained with Docker Compose.
- **Mobile-device friendly**: responsive mobile-first design with adaptive drawers, touch-optimized controls, and 60 fps interaction on phones and tablets.
- No reference to external sister projects in any public-facing documentation.

## 3. Target Personas

- **Concerned Resident / Diaspora**: Needs quick magnitude, location, and time info on mobile.
- **Disaster / Humanitarian Volunteer**: Needs historical context, aftershock frequency, and cluster maps.
- **Geoscientist / Data Analyst**: Needs raw CSV/GeoJSON exports, depth vs magnitude scatter, and boundary overlays.

## 4. Milestones / Phases

### Phase 1 — Foundation & Design Lock
- Finalize PRD, AGENTS.md, README.md, and milestone definitions.
- Confirm `alfazen-coding` bundle skills installed; set up version hooks.
- Define Canada and China data source adapters and 2-DB schema.

### Phase 2 — Data & Persistence
- Build ingestion workers (NRCan / CENC / USGS adapters).
- Create `data/eq-canada.db` and `data/eq-china.db` with WAL, B-Tree indexes on `origintimeutc`, `magnitude`, `latitude`, `longitude`.
- Populate initial historical archives (minimum 2,000 verified records per region where available).
- Implement deduplication (spatial distance ≤ 25 km, time window ± 60 s).

### Phase 3 — Backend & API
- FastAPI service with REST endpoints:
  - `GET /api/v1/earthquakes` (filterable by `region`, `min_mag`, `max_mag`, `start_date`, `end_date`, `bbox`, `limit`, `offset`)
  - `GET /api/v1/earthquakes/stats`
  - `GET /api/v1/live` (SSE for live push)
  - `GET /api/v1/boundaries/tectonic` (GeoJSON)
  - `GET /api/v1/boundaries/provinces` (GeoJSON)
- Database access layer with multi-region query routing.

### Phase 4 — Frontend UI & Cartography
- Vanilla ESM JavaScript + Leaflet Canvas mode.
- Header: brand icon + "CEMA" (left); telemetry capsule (center: live indicator, total recorded, max quake, 24h count); action icons (audio, analytics, data table, full-screen, camera) (right).
- Filter bar just below header (date window, magnitude range, region toggle, depth range).
- Map: zoom in/out buttons; Dark Canvas / OpenStreetMap theme toggler.
- Floating MAG bar (lower right); Layers bar (lower left); Player bar (lower center) with timeline replay.
- Responsive mobile layout: left feed drawer + right 9-dot bento tools grid.

### Phase 5 — Integration, Quality & Release
- End-to-End testing with Playwright (headless browser verification).
- Docker Compose build and local validation.
- Version tag `v0.1.0` (or `v1.0.0` if all milestones met).
- Update CHANGELOG.md per `changelog-curator` skill rules.

## 5. Technical Architecture

- **Data Ingestion**: Async HTTPX workers polling NRCan, CENC, USGS feeds.
- **Persistence**: SQLite3 (WAL) × 2 (`eq-canada.db`, `eq-china.db`).
- **API**: FastAPI + Uvicorn.
- **Frontend**: Vanilla ESM JS, HTML5, CSS Glassmorphism, Leaflet (Canvas mode).
- **Mapping**: CartoDB Dark Matter / OpenStreetMap Standard basemaps; Canada provincial + tectonic boundary GeoJSON; China provincial + tectonic boundary GeoJSON.
- **DevOps**: Docker, Docker Compose.

## 6. Design Advice & Corrections

- **Advice on 2 DB files**: Rather than one monolithic DB, splitting into `eq-canada.db` and `eq-china.db` keeps queries fast, supports independent maintenance, and allows future regional scaling. Both use identical schemas for portability.
- **Advice on UI consistency**: Keep the 3-column desktop header identical in layout to the reference observatory pattern (balanced left brand, centered telemetry, right icon dock). Do not use iframe nesting; use a unified SPA with reactive state.
- **Advice on mobile**: Implement adaptive dual-drawers (left seismic feed, right 9-dot bento grid) rather than collapsing everything into a hamburger menu, preserving quick access to map layers and analytics.
- **Advice on audio / playback**: The player bar should support chronological replay across any selected temporal window with magnitude-scaled audio chirps. This improves accessibility and situational awareness.

## 7. Non-Functional Requirements

- Load time < 2 s for initial map view (cached tiles, lightweight JSON endpoints).
- 60 fps interaction on mobile and desktop.
- Zero external cloud dependencies; fully offline-capable after build.
- Responsive design: mobile-first with desktop enhancement.

## 8. Data Sources & Boundaries

### Canada
- **Primary**: Natural Resources Canada (NRCan) — earthquake bulletins and seismic feed.
- **Secondary / Fallback**: USGS (global feeds filtered to Canada bounding box).
- **Geospatial Boundaries**: Canada provincial / territorial boundaries (GeoJSON); North American plate boundary segments.

### China
- **Primary**: China Earthquake Networks Center (CENC) — real-time and catalog feeds.
- **Secondary / Fallback**: USGS (filtered to China bounding box).
- **Geospatial Boundaries**: China provincial / autonomous region boundaries (GeoJSON); Eurasian / Indo-Australian plate boundary segments.
