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

### Phase 3 — Backend & API (Target: Week 3) ⏳ IN PROGRESS
- [ ] FastAPI service scaffolded (`backend/main.py`)
- [ ] `GET /api/v1/earthquakes` + filters
- [ ] `GET /api/v1/earthquakes/stats`
- [ ] `GET /api/v1/live` (SSE)
- [ ] `GET /api/v1/boundaries/tectonic`
- [ ] `GET /api/v1/boundaries/provinces`
- [ ] Multi-region DB routing
- [ ] Unit tests (`tests/test_api.py`)

### Phase 4 — Frontend UI (Target: Week 4) ⏳ PENDING
- [ ] SPA header (3-col), telemetry HUD, filter bar
- [ ] Leaflet Canvas map + theme toggler
- [ ] Floating MAG / Layers / Player bars
- [ ] Mobile drawers (dual-nav)
- [ ] Mobile-device friendly verification

### Phase 5 — Integration, Quality & Release (Target: Week 5) ⏳ PENDING
- [ ] Playwright E2E tests passing
- [ ] Docker Compose validated
- [ ] Version tag (`v0.2.0` set)
- [ ] `CHANGELOG.md` updated (`changelog-curator`)
- [ ] `HANDOFF.md` milestone checkpoint
- [ ] Quality review (`verification-before-completion`)
