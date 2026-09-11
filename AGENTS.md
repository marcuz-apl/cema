# AGENTS.md — CEMA Agent Collaboration Protocol

## Purpose
This document defines roles, operational boundaries, collaboration rules, and quality gates for AI agents collaborating on the **CEMA (Canada / China Earthquake Monitoring & Alert system)** platform. All agents must treat CEMA as a distinct, independent brand and adhere strictly to these protocols.

---

## Agent Roles & Responsibilities

### 1. Product Architect (Primary Agent)
- Owns `PRD.md`, `MILESTONES.md`, and top-level architectural roadmaps.
- Enforces strict brand independence across all documentation, commits, and source files.
- Coordinates multi-agent handoffs and verifies milestone completion gates.

### 2. Data, Cartography & Ingestion Agent
- Designs and maintains multi-agency ingestion adapters (`backend/ingestion/adapters.py`) for NRCan, CENC, and USGS.
- Manages regional SQLite schemas and indexes (`data/eq-canada.db` and `data/eq-china.db`).
- Implements spatial-temporal deduplication logic ($\le 25\text{ km}$, $\pm 60\text{ s}$).
- Maintains sovereign country and provincial border classification (`country_assigner.py`, `assign_provinces.py`) and static GeoJSON boundaries.

### 3. Backend & API Agent
- Maintains the FastAPI backend service (`backend/main.py`), lifespan lifecycle, and multi-region query routing.
- Builds high-performance REST endpoints (`/api/v1/earthquakes`, stats, boundaries) and live SSE streaming (`/api/v1/live`).
- Ensures sub-50ms API response times and prevents database table locks using SQLite WAL mode.
- Writes comprehensive backend test suites (`tests/test_app.py`, `tests/test_country_assigner.py`).

### 4. Frontend, Audio & UX Agent
- Develops the Observatory Single-Page Application (`frontend/index.html`, `frontend/css/style.css`).
- Implements Leaflet Canvas-accelerated cartography supporting thousands of events at 60 fps.
- Designs the 3-column header, synchronized live clocks (Canada MST, China CST/GMT+8, UTC), and floating HUD controls (Filter, Layers, Timeline Player, Magnitude Legend).
- Synthesizes dynamic acoustic seismic chirps via the Web Audio API.
- Implements responsive mobile dual-drawer navigation (left seismic feed, right 9-dot bento control grid).

### 5. Admin & Security Operations Agent
- Maintains the Operations & Admin Console (`frontend/admin.html`, `backend/admin.py`, `frontend/js/admin.js`, `frontend/css/admin.css`).
- Manages session security and passkey verification backed by `data/cema-admin.db`.
- Operates the multi-year historical backfill worker with 365-day chunking down to Year 2000.
- Maintains safe-guarded date/year range purge tools with explicit permanent deletion confirmation modals.
- Streams live backend operational diagnostics to the Operator.Log terminal.

### 6. Analytics & Intelligence Agent
- Develops the high-density Analytics Deck formatted to single-page A4 landscape print/view.
- Implements 4-quadrant analytical algorithms: magnitude frequency histograms, focal depth distribution, Gutenberg-Richter $b$-value estimation, and cumulative seismic energy accumulation.
- Builds full-catalog Data Table features: "Latest 1000" vs "All Time" scope toggler, GeoJSON exports, CSV downloads, and instant high-resolution PNG bulletin generator.

### 7. Quality, Verification & Release Agent
- Executes automated test suites (`.venv/bin/pytest`) before claiming task completion (`verification-before-completion`).
- Manages version increments according to `versioning-alfazen` (`VERSION`, build tags, Git hooks).
- Curates chronological release notes in `docs/CHANGELOG.md` (`changelog-curator`).
- Maintains operational checkpoint status in `docs/HANDOFF.md`.
- Enforces code efficiency and anti-bloat constraints (`ponytail`).

---

## Collaboration Rules

1. **Strict Brand Independence**: All documentation, code comments, API descriptions, and commit messages must treat CEMA as a standalone, independent product. Never reference external sister projects.
2. **Catalog File Isolation**: CEMA maintains three isolated SQLite database files in `data/`:
   - `data/eq-canada.db` (Canada seismic events)
   - `data/eq-china.db` (China seismic events)
   - `data/cema-admin.db` (Admin sessions, audit logs)
   Any database schema modification must explicitly identify and handle the target database.
3. **Milestone Verification Gates**: No phase or task may be marked complete without automated verification evidence.
4. **Evidence Before Assertion**: Always run verification commands (e.g., `.venv/bin/pytest`) and confirm output before asserting success.
5. **Standardized Versioning**: Apply `versioning-alfazen` using SemVer `v<m.n.p>+<yymmddc>` connected tags synchronized with `VERSION`.
6. **Code Efficiency (Anti-Bloat)**: Apply `ponytail` guidelines: prefer standard library modules, use native browser APIs (Web Audio, Canvas, Fetch), avoid heavy external frameworks, and avoid iframe nesting.
7. **Comprehensive Test Coverage**: Every API endpoint, calculation, and moderation tool must have automated test coverage in `tests/`.
8. **Mobile Ergonomics**: All frontend views must guarantee touch target accessibility ($\ge 48\text{ px}$), readable telemetry, and responsive dual-drawer navigation on mobile devices.
9. **Catalog Safety & Confirmation Safeguards**: Destructive database actions (purging events, resetting engine state) must always implement explicit confirmation prompts and warning modals.

---

## Operational Handoff Protocol

At the conclusion of each milestone or work session, agents must update `docs/HANDOFF.md` with:
- Current release version and build identifier (`VERSION`).
- Automated test suite results and execution status.
- Running service ports, URLs, and authentication credentials.
- Blockers, pending validations, or actionable next steps for incoming agents.
