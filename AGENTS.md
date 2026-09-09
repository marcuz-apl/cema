# AGENTS.md — CEMA Agent Collaboration Protocol

## Purpose
This document defines roles, collaboration rules, and quality gates for AI agents working on the CEMA project. It does not reference any sister or predecessor project.

## Agent Roles

### 1. Product Architect (Primary Agent)
- Owns PRD updates, milestone tracking, and architecture decisions.
- Confirms that all docs (README, PRD, AGENTS, CHANGELOG) omit external project references.

### 2. Data & Ingestion Agent
- Designs NRCan (Canada) and CENC (China) ingestion adapters.
- Creates `data/eq-canada.db` and `data/eq-china.db` schemas.
- Implements deduplication logic (≤25 km, ±60 s).

### 3. Backend & API Agent
- Builds FastAPI endpoints (`/api/v1/earthquakes`, stats, live SSE, boundaries).
- Adds WAL mode and multi-region query routing.
- Writes `tests/test_api.py`.

### 4. Frontend & UX Agent
- Implements the unified SPA: 3-column header, telemetry HUD, filter bar, map (Leaflet Canvas), floating MAG / Layers / Player bars, mobile drawers.
- Ensures responsive behavior and dark/light theme synchronization.

### 5. Quality & Release Agent
- Runs `changelog-curator` skills for milestone notes.
- Runs Playwright verification tests.
- Manages `VERSION`, `CHANGELOG.md`, and Docker Compose validation.

### 6. Design Review Agent (Optional)
- Reviews UI against `alfazen-coding` `ui-ux-pro-max` and `impeccable` guidelines.
- Confirms glassmorphism aesthetic, typography hierarchy, and mobile dual-drawer ergonomics.

## Collaboration Rules

1. **No external references**: All docs and comments must treat CEMA as a new, independent brand.
2. **Two DB files**: Any database change must specify which file (`eq-canada.db` or `eq-china.db`) is affected.
3. **Milestone gates**: No phase may be marked complete without the previous phase's deliverables verified.
4. **Evidence before claim**: Use `verification-before-completion` skill before marking tasks complete.
5. **Versioning**: Use `versioning-alfazen` for bounded `m.n.p` bumps and `v{VERSION}-{BUILD}` build IDs.
6. **Code efficiency**: Apply `ponytail` (anti-bloat) — prefer stdlib, avoid unnecessary dependencies, no iframe nesting.
7. **Testing**: Every endpoint and UI interaction must have at least one Playwright or pytest verification.
8. **Mobile-device friendly**: All UI work must verify responsive behavior on mobile viewports (touch targets, drawer navigation, readable telemetry, and 60 fps interaction on phones/tablets).

## Milestone Tracking

Use the `handoff` skill (`HANDOFF.md`) to record milestone status, blockers, and next actions. Update after each phase.
