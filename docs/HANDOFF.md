# HANDOFF — CEMA Milestone Checkpoint (v0.5.0+260911r)

## Current Status & Verification
- **Version**: `v0.5.0+260911r` (defined in `VERSION`)
- **Automated Tests**: **51 passed out of 51 tests (100% passing)** via `.venv/bin/pytest -v`.
  - `tests/test_admin.py` (19 passed): Admin authentication, audit logging, purge tools, backfill triggers, poller status and toggle, Mag floor ≥ 2.0 validation.
  - `tests/test_analytics_deck.py` (15 passed): Full Playwright E2E browser tests, all 4 tabs, chart rendering, exports.
  - `tests/test_app.py` (12 passed): FastAPI core endpoints, stats, live SSE, GeoJSON boundaries.
  - `tests/test_country_assigner.py` (5 passed): Sovereign and provincial border classifiers.
- **Server Port**: `4071`
  - Public Observatory: `http://localhost:4071`
  - Operations & Admin Console: `http://localhost:4071/admin` *(Passkey: `cema2026`)*
- **Active Database Records**:
  - `data/eq-canada.db`: 8,255 events (WAL mode, M≥3.0, 335 in 2000, 7,920 in 2010–2026)
  - `data/eq-china.db`: 14,896 events (WAL mode, M≥3.0, 2010–2026 coverage)
  - Combined Catalog: 23,151 records
  - `data/cema-admin.db`: Admin session and operator action audit log

## Recent Enhancements & Fixes
1. **"2020-Now" Temporal Filter Pill**:
   - Added between "All-Time" and "1Y" in `frontend/index.html` (`[ All-Time ] [ 2020-Now ] [ 1Y ] [ 30D ] [ 7D ] [ 24H ]`).
   - Allows instant inspection of the modern 2020–2026 catalog without loading decades of archive data.
2. **Analytics Deck Time Tab Ergonomics (65% / 35%)**:
   - Updated `.analytics-grid-time-lower` in `frontend/css/style.css` to `grid-template-columns: minmax(0, 1.85fr) minmax(0, 1fr)`.
   - Diurnal 24-hour bars and Day-of-Week 7-day bars now display balanced visual pillar thickness while strictly preserving 0px scroll on A4 single-page height.
3. **Backfill Engine Mag Floor & Dropdown Contrast**:
   - MAG FLOOR selector options start from `2.0` with `3.0` selected as default.
   - Pydantic schema validated with `Field(ge=2.0, le=10.0, default=3.0)`.
   - YEAR dropdown contrast fixed by targeting native `<select>` options in `frontend/css/admin.css` with dark background and light font colors.
4. **Auto-Poller (Cron 3m) Boot Default & Deadlock Elimination**:
   - Auto-poller default on server boot restored to `enabled: true`.
   - Converted `_LOCK` in `backend/admin.py` to `threading.RLock()` and un-nested `_log()` calls, resolving a re-entrant thread deadlock.
   - Wired `#pollerBadge` in `frontend/js/admin.js` to toggle `/api/admin/poller/toggle` on click with visual hover indicators and toasts.
5. **Energy Tab Cumulative Curve Verification**:
   - Verified that the X-axis starts dynamically from `tStart` (earliest record in dataset).
   - Documented that Canada holds 335 records from Year 2000, which can either be purged to align with China at 2010 or backfilled across 2000–2009.

## How to Run Local Development Server
```bash
nohup .venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 4071 --loop asyncio > uvicorn.log 2>&1 &
```
