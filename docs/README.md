# CEMA — Canada / China Earthquake Monitoring & Alert System

## Overview

CEMA is a real-time seismic observatory platform monitoring earthquake activity across Canada and China. It combines multi-agency ingestion, persistent SQLite catalogs (`eq-canada.db`, `eq-china.db`), interactive Leaflet cartography, and a responsive single-page interface.

## Features

- **Real-Time Monitoring**: NRCan (Canada), CENC (China), and USGS feeds.
- **Two Independent Catalogs**: Separate SQLite databases with WAL mode, spatial and temporal indexing.
- **Interactive Map**: Canvas-accelerated Leaflet rendering with Dark Matter / OpenStreetMap theme toggler.
- **Telemetry HUD**: Live clock, total events, max magnitude, 24-hour count.
- **Analysis Tools**: Filter bar (date, magnitude, depth, region), data table, analytics suite, timeline playback with audio sonification.
- **Responsive Design**: Desktop 3-column header; mobile dual-drawer navigation (left feed, right 9-dot bento tools).

## Technology Stack

| Layer | Technologies |
|---|---|
| Backend | Python 3.11+, FastAPI, Uvicorn, Async HTTPX |
| Database | SQLite3 (WAL) × 2 (`eq-canada.db`, `eq-china.db`) |
| Frontend | Vanilla ESM JavaScript, HTML5, CSS Glassmorphism, Leaflet Canvas |
| Mapping | CartoDB Dark Matter, OpenStreetMap, Canada / China boundary GeoJSON |
| DevOps | Docker, Docker Compose |

## Quickstart

```bash
# Clone the repository
git clone https://github.com/your-org/cema.git
cd cema

# Build and start
docker compose up -d --build
```

Access at `http://localhost:4070`.

## Project Structure

```
.
├── backend/          # FastAPI application, ingestion workers, database layer
├── frontend/         # SPA (index.html, CSS, JS assets)
├── data/             # SQLite DB files (eq-canada.db, eq-china.db)
├── docs/             # Technical notes, milestone tracking, changelog
├── assets/           # Icons, favicons, boundary GeoJSON
├── tests/            # pytest + Playwright tests
└── docker-compose.yml
```

## Milestones

1. **Phase 1 — Foundation**: PRD, AGENTS.md, README.md, skill setup.
2. **Phase 2 — Data & Persistence**: Ingestion adapters, 2-DB schemas, historical archives.
3. **Phase 3 — Backend & API**: FastAPI endpoints, multi-region routing, live SSE.
4. **Phase 4 — Frontend UI**: SPA, map, telemetry, drawers, player bar.
5. **Phase 5 — Integration & Release**: End-to-end tests, Docker build, version tag.

## License

MIT License — see `LICENSE`.
