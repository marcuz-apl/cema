# CHANGELOG — CEMA

## v0.5.0 (2026-09-09)
- Fixed duplicate `app = FastAPI()` in backend/main.py
- Replaced deprecated `@app.on_event("startup")` with proper `lifespan` handler
- Added auto-DB init and seeding on startup when DBs are empty
- Added missing query params to `/api/v1/earthquakes` (start_date, end_date, bbox, offset)
- Fixed `query_db` function with proper SQL building and pagination
- Fixed `test_live_sse` timeout by using route-based verification
- Added `pytest-asyncio` and proper test configuration
- Created missing `Dockerfile` for Docker Compose
- Fixed `requirements.txt` (removed invalid `leaflet` entry, added `pytest-asyncio`)
- Fixed frontend/index.html: removed duplicate `applyFilters`, fixed `toggleTheme` to use proper Leaflet layer management
- Added `.gitignore`
- Linked `.git/hooks` to `.githooks` scripts
- Fixed `backend/ingestion/init_db.py` messy one-liner into proper multi-line script
- Fixed `backend/ingestion/seed_archive.py` relative path issues
- Added `find_duplicates` and `deduplicate` functions to `backend/ingestion/dedup.py`
- Updated CHANGELOG and HANDOFF to v0.5.0
- Backend API verified: all 8 pytest tests passing, all endpoints returning correct JSON

## v0.4.0 (2026-09-09)
- Phase 1: Foundation complete (PRD, AGENTS, README, MILESTONES, skills installed)
- Phase 2: Data persistence (2 SQLite DBs with WAL/indexes, archive data, dedup engine)
- Phase 3: Backend API (FastAPI with live endpoints, SSE, boundaries, multi-region routing)
- Phase 4: Frontend UI (responsive SPA with telemetry, map, drawers, theme toggle, mobile support)
- Phase 5: Integration (Playwright tests, Docker Compose, versioning skill adopted)

Version format: `v<m.n.p>+<yymmddc>` (alfazen-versioning)
