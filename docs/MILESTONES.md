# Milestones & Phases — CEMA

## Milestone Schema (per changelog-curator skill)

### Phase 1 — Foundation & Design Lock (Target: Week 1) ✅ COMPLETED
- [x] PRD.md finalized (root folder)
- [x] AGENTS.md created (root folder)
- [x] README.md created (root folder)
- [x] `alfazen-coding` skills verified installed
- [x] Milestones defined (this file + docs/ADVISORY.md + docs/HANDOFF.md)
- [x] Design lock: header layout, telemetry HUD, filter bar, floating MAG / Layers / Player bars confirmed (see PRD.md sec 4 + ADVISORY.md)

### Phase 2 — Data & Persistence (Target: Week 2) ✅ COMPLETED
- [x] NRCan adapter stubbed (`backend/ingestion/adapters.py`)
- [x] CENC adapter stubbed (`backend/ingestion/adapters.py`)
- [x] USGS adapter stubbed (`backend/ingestion/adapters.py`)
- [x] `data/eq-canada.db` schema (WAL + B-Tree indexes)
- [x] `data/eq-china.db` schema (WAL + B-Tree indexes)
- [x] Archive data loaded (Canada 3 NRCan + China 3 CENC records)
- [x] Dedup engine (`haversine <=25km` + `±60s` window)

### Phase 3 — Backend & API (Target: Week 3) ✅ COMPLETED
- [x] FastAPI service scaffolded (`backend/main.py`)
- [x] `GET /api/v1/earthquakes` + filters (`region`, `min_mag`, `max_mag`, `limit`)
- [x] `GET /api/v1/earthquakes/stats` (multi-region DB routing)
- [x] `GET /api/v1/live` (SSE streaming)
- [x] `GET /api/v1/boundaries/tectonic`
- [x] `GET /api/v1/boundaries/provinces`
- [x] Multi-region DB routing (`eq-canada.db` / `eq-china.db`)
- [x] Unit test stub (`tests/test_app.py`)

### Phase 4 — Frontend UI (Target: Week 4) ✅ COMPLETED
- [x] SPA header (3-col), telemetry HUD, filter bar
- [x] Leaflet Canvas map + theme toggler
- [x] Floating MAG / Layers / Player bars
- [x] Mobile drawers (dual-nav)
- [x] Mobile-device friendly verification

### Phase 5 — Integration, Quality & Release (Target: Week 5) ✅ COMPLETED
- [x] Playwright E2E tests passing
- [x] Docker Compose validated
- [x] Version tag (`v0.4.0` set)
- [x] `CHANGELOG.md` updated (`changelog-curator`)
- [x] `HANDOFF.md` milestone checkpoint
- [x] Quality review (`verification-before-completion`)
