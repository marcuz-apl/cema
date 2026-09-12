# CEMA Product Requirements Document (PRD)

## 1. Executive Summary & Product Vision

**CEMA (Canada / China Earthquake Monitoring & Alert system)** is an open, high-performance, real-time seismic observatory platform designed specifically to monitor, visualize, and analyze earthquake events across **Canada** and **China**.

Operating with independent regional persistence, real-time multi-agency ingestion, geospatial border enrichment, acoustic audio sonification, high-density analytics, and an administrative moderation console, CEMA provides a reliable, self-contained, and mobile-friendly seismic intelligence workstation.

---

## 2. Core Tenets & Operating Principles

1. **Strict Brand & Architecture Independence**: CEMA operates as an independent platform. All documentation, public APIs, and codebase comments reflect CEMA's distinct identity without external project references.
2. **Three-Tier Database Topology**: Regional catalogs are partitioned into `data/eq-canada.db` and `data/eq-china.db`, backed by `data/cema-admin.db` for administrative audit logs.
3. **Evidence Before Claim**: Verification through automated pytest and Playwright suites before marking milestones complete.
4. **Mobile-First Ergonomics**: Dual-drawer mobile navigation (left seismic feed, right 9-dot bento control grid) ensuring 60 fps touch interactions on handheld viewports.
5. **Zero External Cloud Keys**: Operates entirely on free, open cartography (CartoDB Dark Matter, OpenStreetMap) and localized GeoJSON boundaries without third-party API key blockers.

---

## 3. Target User Personas

| Persona | Core Needs | Primary Features Used |
|---|---|---|
| **Concerned Resident / Diaspora** | Rapid awareness of recent tremors in Canada or China with local time conversion | Mobile dual-drawer feed, live contextual MST/CST clocks, magnitude classification pills |
| **Emergency & Humanitarian Responder** | Spatial clustering, aftershock frequency, and official bulletin generation | Leaflet Canvas map, timeline player with audio chirps, instant PNG bulletin generator |
| **Seismologist / Data Analyst** | Gutenberg-Richter $b$-value estimation, depth vs. magnitude scatter, catalog exports | Single-page A4 landscape Analytics Deck, CSV & GeoJSON export, "Latest 1000" vs "All Time" data table |
| **Observatory Operator / Admin** | Ingestion pipeline health, historical catalog backfilling, data deduplication, and catalog moderation | Passkey-authenticated Admin Console (`/admin`), multi-source backfill down to Year 2000, safe-guarded date purge tool |

---

## 4. Functional Specifications

### 4.1 Data Ingestion & Deduplication Pipeline
- **Multi-Agency Adapters**:
  - Natural Resources Canada (NRCan) seismic bulletin polling.
  - China Earthquake Networks Center (CENC) real-time feed polling.
  - USGS Earthquake API filtered to Canada (~42°N–83°N, 168°W–52°W) and China (~18°N–54°N, 73°E–135°E) bounding boxes.
- **Intelligent Deduplication**: Cross-agency event consolidation using Haversine distance threshold $\le 25\text{ km}$ and temporal window $\pm 60\text{ s}$.
- **Magnitude Floor**: Standardized M 3.0 threshold across ingestion, backfilling, and user interfaces.

### 4.2 Spatial Enrichment & Sovereign Border Classification
- **Country Assigner**: Exact polygon point-in-polygon matching against sovereign boundaries (`world_countries.geojson`).
- **Administrative Codes**: 2-letter postal abbreviation mapping for all 13 Canadian provinces/territories and 50 US border states.
- **Chinese Administrative Division**: Provincial and autonomous region attribution from static GeoJSON boundaries.

### 4.3 Interactive Leaflet Canvas Cartography
- Canvas-accelerated Leaflet layer handling thousands of historical events smoothly at 60 fps.
- Toggle between CartoDB Dark Matter (low-light emergency mode) and OpenStreetMap Standard (geographic context).
- Layer toggles for North American / Eurasian tectonic fault lines, provincial boundaries, and epicenter markers.
- Magnitude legend with interactive filter chips (M3.0–4.5, M4.5–5.5, M5.5–6.5, M6.5–7.5, M≥7.5).

### 4.4 Seismic Audio Sonification Engine
- Synthetic acoustic synthesizer powered by the browser Web Audio API.
- Converts magnitude dynamically into exponential frequency (Hz) and gain during timeline playback.
- Synchronized auditory cueing for chronological scrub and historical event replay.

### 4.5 Single-Page A4 Landscape Analytics Deck
- 4-quadrant layout tailored for single-view screens and A4 landscape PDF export:
  1. Magnitude frequency histogram and classification distribution.
  2. Focal depth scatter plot (shallow $\le 30\text{ km}$, intermediate, deep).
  3. Gutenberg-Richter recurrence relation and $b$-value estimation.
  4. Cumulative seismic energy accumulation ($E = 10^{4.8 + 1.5M}$) with equal-height cards.

### 4.6 Comprehensive Data Table & Export Studio
- Interactive paginated table with First/Last page navigation.
- Scope toggler: "Latest 1000" events (rapid review) vs. "All Time" (full catalog).
- One-click downloads:
  - **GeoJSON**: Standardized geospatial FeatureCollection for GIS software (QGIS, ArcGIS).
  - **CSV**: Spreadsheet-compatible dataset with all spatial and temporal attributes.
  - **PNG Bulletin**: Formatted emergency bulletin image with aligned typography and epicenter details.

### 4.7 Operations & Admin Control Center (`/admin`)
- **Authentication**: Client-side passkey modal verifying against `ADMIN_PASSWORD` (default: `cema2026admin`).
- **Telemetry & Health**: Real-time status checks for USGS, NRCan, and CENC ingestion workers.
- **Historical Backfill**: Multi-year catalog ingestion down to Year 2000 using 365-day chunking to avoid remote rate limits.
- **Range Purge Tool**: Date/year range purge tool with historical presets (Year 2008 Wenchuan cluster, Years 2000–2003) and explicit confirmation warning modal.
- **Deduplication Runner**: Manual in-place catalog deduplication and engine state resets.
- **Operator.Log Terminal**: Live streaming operational terminal styled in dark and light syntax modes.

---

## 5. Non-Functional Requirements & Performance Budgets

| Metric | Target | Verification Method |
|---|---|---|
| **Initial Load Time** | < 2.0 s on 3G Fast network | Lighthouse / DevTools audit |
| **Rendering Performance** | 60 fps smooth pan/zoom with 5,000+ markers | Leaflet Canvas mode verification |
| **API Response Time** | < 50 ms for `/api/v1/earthquakes` with standard limits | Uvicorn benchmark & test suite |
| **Database Concurrency** | Zero table-lock timeouts during concurrent ingestion & querying | SQLite WAL mode verification |
| **Mobile Responsiveness** | Flawless view on 375px to 1920px+ viewports | Playwright mobile emulation |
| **Offline Resilience** | Full UI functionality and local GeoJSON boundary rendering without Internet | Static asset audit |

---

## 6. System Architecture

```
                                  +-----------------------+
                                  | Ingestion Sources     |
                                  | NRCan | CENC | USGS   |
                                  +-----------+-----------+
                                              |
                                              v
+---------------------------------------------------------------------+
| CEMA Backend Service (FastAPI :4071)                                |
|                                                                     |
|  +--------------------+   +-------------------+   +---------------+  |
|  | Ingestion Workers  |-->| Dedup Engine      |-->| Country       |  |
|  | & Backfill Worker  |   | (<=25km, +-60s)   |   | Assigner      |  |
|  +--------------------+   +-------------------+   +-------+-------+  |
|                                                           |          |
|  +--------------------------------------------------------+          |
|  | Multi-Region Database Routing Layer                               |
|  +-----------------+---------------------+------------------+        |
+--------------------|---------------------|------------------|--------+
                     |                     |                  |
                     v                     v                  v
         +-----------------------+ +------------------+ +-------------+
         | data/eq-canada.db     | | data/eq-china.db | | cema-admin  |
         | (WAL, Spatial Indexes)| | (WAL, Indexes)   | | .db (Logs)  |
         +-----------------------+ +------------------+ +-------------+
                     ^                     ^
                     +----------+----------+
                                |
+-------------------------------+--------------------------------------+
| CEMA Unified Frontend (Port 4071)                                    |
|                                                                      |
|  +---------------------------+   +--------------------------------+  |
|  | Public Observatory SPA    |   | Operations & Admin Portal      |  |
|  | - 3-Col Header & Clocks   |   | - Passkey Modal                |  |
|  | - Leaflet Canvas Map      |   | - Telemetry & Ingestion Health |  |
|  | - Floating HUD Controls   |   | - 365-Day Historical Backfill  |  |
|  | - Audio Sonification      |   | - Safe Purge Tools             |  |
|  | - A4 Analytics Deck       |   | - Live Operator.Log Stream     |  |
|  | - Data Table & Exports    |   +--------------------------------+  |
|  +---------------------------+                                       |
+----------------------------------------------------------------------+
```

---

## 7. Milestone Progression Matrix

- **Phase 1 — Foundation & Architecture Design** ✅ (v0.1.0)
- **Phase 2 — Data Architecture & Persistent Catalogs** ✅ (v0.2.0)
- **Phase 3 — Backend API & Real-Time SSE Service** ✅ (v0.3.0)
- **Phase 4 — Frontend Cartography & Responsive SPA** ✅ (v0.4.0)
- **Phase 5 — Quality Gates & Integration Harness** ✅ (v0.5.0)
- **Phase 6 — Audio Sonification & Boundary Geospatial Enrichment** ✅ (v0.6.0+2609101 – v0.6.0+260911h)
- **Phase 7 — Analytics Deck, Export Studio & Data Table** ✅ (v0.7.0+2609106 – v0.7.0+2609114)
- **Phase 8 — Operations & Admin Console** ✅ (v0.8.0+2609116 – v0.8.0+260911l)
- **Phase 9 — Hardening, Containerization & Production Readiness** ✅ (v0.9.0+260911m – v0.9.0+260912c)
