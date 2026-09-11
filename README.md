# CEMA — Canada / China Earthquake Monitoring & Alert System

[![Version](https://img.shields.io/badge/version-v0.5.0%2B260911m-blue.svg)](VERSION)
[![Python](https://img.shields.io/badge/python-3.11%2B-green.svg)](requirements.txt)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com)
[![Leaflet](https://img.shields.io/badge/Leaflet-1.9.4-brightgreen.svg)](https://leafletjs.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](docker-compose.yml)

## Overview

**CEMA** is a real-time seismic observatory platform dedicated to monitoring earthquake activity across **Canada** and **China**. Operating as a dual-jurisdiction telemetry system, CEMA integrates live multi-agency data streams, high-performance SQLite catalogs with spatial indexing, canvas-accelerated interactive cartography, acoustic audio sonification, analytical intelligence decks, and a comprehensive administrative operations center.

---

## Key Features

- **Dual-Region Real-Time Monitoring**: Direct ingestion from Natural Resources Canada (NRCan), China Earthquake Networks Center (CENC), and USGS with automated deduplication (≤25 km, ±60 s).
- **Independent Catalog Persistence**: Distinct SQLite databases (`eq-canada.db` and `eq-china.db`) operating in Write-Ahead Logging (WAL) mode for concurrency and zero lock contention.
- **Interactive Canvas Cartography**: Canvas-accelerated Leaflet map rendering thousands of historical events at 60 fps, featuring CartoDB Dark Matter and OpenStreetMap basemaps, tectonic fault overlays, and provincial boundaries.
- **Live Contextual Telemetry**: Synchronized header clocks displaying Canada Mountain Standard Time (MST), China Standard Time (CST/GMT+8), and UTC alongside real-time 24h counters and max magnitude indicators.
- **Seismic Audio Sonification**: Web Audio API synthesizer translating earthquake magnitudes into proportional acoustic chirps and frequencies during chronological playback.
- **Single-Page A4 Analytics Deck**: 4-quadrant analytical suite covering magnitude frequency, depth scatter, Gutenberg-Richter $b$-value calculation, and cumulative seismic energy accumulation.
- **Full-Catalog Data Table & Exports**: Instant search, "Latest 1000" vs "All Time" scope toggler, and one-click GeoJSON / CSV catalog exports.
- **High-Resolution Bulletin Generator**: Instant, aligned PNG bulletin generator for official seismic advisories.
- **Operations & Admin Center (`/admin`)**: Passkey-secured moderation console with ingestion pipeline health telemetry, historical backfilling down to Year 2000 with 365-day chunking, date/year range purge tools with confirmation safeguards, deduplication runner, and a live Operator.Log terminal.

---

## Quickstart

### 1. Local Development Starter (Uvicorn)

Run CEMA directly on your host system with Python and Uvicorn:

```bash
# 1. Clone repository & enter workspace
git clone https://github.com/your-org/cema.git
cd cema

# 2. Create and activate a Python 3.11+ virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialize SQLite databases and seed initial data
python3 backend/ingestion/init_db.py

# 5. Start CEMA backend server with Uvicorn
uvicorn backend.main:app --host 0.0.0.0 --port 4071 --reload
```

- **Public Observatory UI**: [http://localhost:4071](http://localhost:4071)
- **Operations & Admin Portal**: [http://localhost:4071/admin](http://localhost:4071/admin) (Default passkey: `cema2026admin`)
- **Interactive API Documentation**: [http://localhost:4071/docs](http://localhost:4071/docs)

---

### 2. Containerized Starter (Docker Compose)

Deploy CEMA in an isolated Docker container with persistent database volumes:

```bash
# Build and start container in the background
docker compose up -d --build

# View container logs
docker compose logs -f cema

# Stop container
docker compose down
```

The application is mapped to `http://localhost:4071` with catalog data stored in `./data`.

---

## Environment Configuration

| Variable | Default | Description |
|---|---|---|
| `PORT` | `4071` | HTTP server port |
| `ADMIN_PASSWORD` | `cema2026admin` | Passkey required for `/admin` operational endpoints |
| `CEMA_ENV` | `production` | Environment mode (`development` / `production`) |

---

## API Endpoints Reference

### Public Seismic Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the unified Observatory Single-Page Application |
| `GET` | `/api/v1/earthquakes` | Query seismic catalog (`region`, `min_mag`, `max_mag`, `start_date`, `end_date`, `bbox`, `limit`, `offset`) |
| `GET` | `/api/v1/earthquakes/stats` | Aggregated telemetry (total events, 24h count, max magnitude, depth distribution) |
| `GET` | `/api/v1/live` | Server-Sent Events (SSE) stream pushing real-time earthquake alerts |
| `GET` | `/api/v1/boundaries/tectonic` | GeoJSON feature collection of North American and Eurasian plate boundaries |
| `GET` | `/api/v1/boundaries/provinces` | GeoJSON feature collection of Canadian and Chinese provincial boundaries |

### Admin & Operations Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/admin` | Serves the Operations & Admin Dashboard |
| `POST` | `/api/v1/admin/verify` | Authenticates operator passkey against session store |
| `GET` | `/api/v1/admin/status` | Ingestion pipeline health checks (USGS, NRCan, CENC) and record counts |
| `POST` | `/api/v1/admin/backfill` | Triggers multi-year historical backfill with 365-day chunking |
| `POST` | `/api/v1/admin/purge` | Safe-guarded date range and magnitude event purge tool |
| `POST` | `/api/v1/admin/dedup` | Executes in-place spatial-temporal deduplication |
| `POST` | `/api/v1/admin/reset` | Resets pipeline caches and catalog states |

---

## Project Structure

```
cema/
├── backend/
│   ├── main.py                     # FastAPI application, routing, lifespan, SSE broadcaster
│   ├── admin.py                    # Admin API routes, auth, backfill, and purge endpoints
│   ├── data/                       # Spatial reference datasets (world countries, US states GeoJSON)
│   └── ingestion/
│       ├── adapters.py             # NRCan, CENC, and USGS feed fetchers
│       ├── init_db.py              # SQLite database schema initialization
│       ├── seed_archive.py         # Baseline historical data populator
│       ├── dedup.py                # Haversine distance & temporal window deduplication
│       ├── country_assigner.py     # Sovereign territory & Canadian/US postal code assigner
│       ├── assign_provinces.py     # Province spatial boundary classifier
│       ├── enrich_catalogs.py      # Spatial enrichment batch processor
│       └── backfill.py             # Historical year chunking and backfill worker
├── frontend/
│   ├── index.html                  # Main Observatory SPA
│   ├── admin.html                  # Operations & Admin Console SPA
│   ├── css/
│   │   ├── style.css               # Main Observatory glassmorphism design system
│   │   └── admin.css               # Admin dashboard high-density styling
│   ├── js/
│   │   └── admin.js                # Admin operator console logic and live log terminal
│   └── data/                       # Frontend GeoJSON boundary files (Canada/China AOIs, faults, provinces)
├── data/
│   ├── eq-canada.db                # SQLite catalog for Canadian seismic events (WAL mode)
│   ├── eq-china.db                 # SQLite catalog for Chinese seismic events (WAL mode)
│   └── cema-admin.db               # SQLite database for admin session logs and audit trails
├── docs/
│   ├── ADVISORY.md                 # Architectural design advisory & regional routing
│   ├── CHANGELOG.md                # Chronological milestone release notes
│   ├── HANDOFF.md                  # Current operational checkpoint & verification state
│   ├── MILESTONES.md               # Progression tracking across Phases 1 through 9
│   └── frontend-alignment.md       # Frontend UI/UX structural specification
├── tests/
│   ├── test_app.py                 # Core API endpoint & database tests
│   ├── test_admin.py               # Admin auth, backfill, and purge route tests
│   ├── test_country_assigner.py    # Geospatial boundary assignment tests
│   └── test_analytics_deck.py      # Analytics deck verification suite
├── Dockerfile                      # Production container image definition
├── docker-compose.yml              # Service specification on port 4071 with volume mounts
├── pytest.ini                      # Pytest runner configuration
├── requirements.txt                # Python backend dependencies
└── VERSION                         # Current semantic release tag
```

---

## Verification & Testing

Execute the automated test suite locally:

```bash
# Run all unit and integration tests
.venv/bin/pytest -v

# Run tests with short summary output
.venv/bin/pytest -q
```

---

## Milestones Progression

- **Phase 1 — Foundation**: Project architecture, PRD, AGENTS protocol, versioning.
- **Phase 2 — Data Persistence**: Ingestion adapters, dual independent SQLite DBs (`eq-canada.db`, `eq-china.db`), deduplication.
- **Phase 3 — Backend Service**: FastAPI REST endpoints, multi-region routing, live SSE stream.
- **Phase 4 — Frontend Cartography**: Responsive SPA, Leaflet Canvas, mobile dual-drawer navigation.
- **Phase 5 — Quality Integration**: Pytest & Playwright harnesses, Docker Compose service.
- **Phase 6 — Audio & Geospatial Enrichment**: Web Audio sonification, sovereign boundary classification, postal code mapping.
- **Phase 7 — Analytics Deck & Exports**: A4 landscape analytics deck, GeoJSON/CSV exports, PNG bulletin generator.
- **Phase 8 — Operations Console**: Admin portal (`/admin`), passkey authentication, backfill engine, safe purge tool, operator logs.
- **Phase 9 — Hardening & Release**: Port 4071 standardization, container persistence, documentation synchronization.

---

## License

MIT License — see `LICENSE` for details.
