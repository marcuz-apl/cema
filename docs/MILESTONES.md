# Milestones & Phases — CEMA

## Milestone Schema (per changelog-curator skill)

### Phase 1 — Foundation & Design Lock (Target: Week 1) ✅ COMPLETED
- [x] PRD.md finalized (root folder)
- [x] AGENTS.md created (root folder)
- [x] README.md created (root folder)
- [x] `alfazen-coding` skills verified installed
- [x] Milestones defined (this file + docs/ADVISORY.md + docs/HANDOFF.md)
- [x] Design lock: header layout, telemetry HUD, filter bar, floating MAG / Layers / Player bars confirmed (see PRD.md section 4 + docs/ADVISORY.md)

### Phase 2 — Data & Persistence (Target: Week 2) ⏳ IN PROGRESS
- [x] NRCan adapter designed and stubbed (`backend/ingestion/adapters.py`)
- [x] CENC adapter designed and stubbed (`backend/ingestion/adapters.py`)
- [x] USGS adapter stubbed (`backend/ingestion/adapters.py`)
- [x] `data/eq-canada.db` schema created (WAL, indexes)
- [x] `data/eq-china.db` schema created (WAL, indexes)
- [x] Initial historical archive loaded (minimum records per region)
- [x] Deduplication engine implemented (≤25 km, ±60 s)

### Phase 3 — Backend & API (Target: Week 3)
- [ ] FastAPI service scaffolded
- [ ] `GET /api/v1/earthquakes` with filter parameters
- [ ] `GET /api/v1/earthquakes/stats`
- [ ] `GET /api/v1/live` (SSE)
- [ ] `GET /api/v1/boundaries/tectonic`
- [ ] `GET /api/v1/boundaries/provinces`
- [ ] Multi-region query routing (Canada vs China DB selection)
- [ ] Unit tests written (`tests/test_api.py`)

### Phase 4 — Frontend UI (Target: Week 4)
- [ ] Vanilla ESM JS scaffolded
- [ ] Header (3-column) implemented
- [ ] Telemetry HUD implemented
- [ ] Filter bar implemented
- [ ] Map (Leaflet Canvas) + theme toggler implemented
- [ ] Floating MAG bar (lower right) implemented
- [ ] Layers drawer (lower left) implemented
- [ ] Player bar (lower center) implemented
- [ ] Mobile drawers (left feed + right 9-dot grid) implemented
- [ ] Mobile-device friendly verification completed: touch targets, responsive drawers, readable telemetry, 60 fps on mobile viewport

### Phase 5 — Integration, Quality & Release (Target: Week 5)
- [ ] Playwright end-to-end tests written and passing
- [ ] Docker Compose build validated
- [ ] Version tag set (`v0.1.0` minimum)
- [ ] `CHANGELOG.md` updated using `changelog-curator`
- [ ] `HANDOFF.md` milestone checkpoint completed
- [ ] Quality review completed (`verification-before-completion`)
- [ ] Mobile-device friendly end-to-end test passing (touch interaction, drawer navigation, telemetry readability on mobile viewport)

## Release Notes Template (per changelog-curator)

Use the ASCII Semantic Progression Matrix format when drafting changes:

```
| Milestone | Phase | Component | Status |
|-----------|-------|-----------|--------|
| M1        | 1     | Design    | LOCKED |
| M2        | 2     | DB        | IN PROGRESS |
```
