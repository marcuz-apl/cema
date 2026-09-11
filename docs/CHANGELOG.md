# CHANGELOG — CEMA

All notable changes to the CEMA (Canada / China Earthquake Monitoring & Alert system) project are documented in this file.
Version format adheres to `versioning-alfazen`: `v<m.n.p>+<yymmddc>`.

---

## [v0.5.0+260911t] - 2026-09-11

### Fixed
- **Normal View 'All-Time' Text**: Fixed duplicate text display glitch where 'All-Time' rendered as 'All-TimeAll' by removing the redundant span and restoring standard text button rendering.

### Changed
- **Mobile Menu 9-Dot Bento Icon**: Updated top-right mobile action menu button (`#btn-mobile-menu`) to a 9-dot Bento Grid icon (`⠿` in 3x3 layout), providing clear visual distinction from the 6-dot drag handle grip (`⠿` in 2x3 layout) and aligning with the project's mobile bento specification.

---

## [v0.5.0+260911s] - 2026-09-11

### Changed
- **MAG Filter Visibility on Mobile**: Reordered mobile filter bar layout (`Country -> MAG Filter -> Time Presets`) ensuring the MAG slider (`min=3.0`) is 100% visible on screen without requiring horizontal scrolling.
- **Compact Country Selector**: Streamlined mobile region buttons strictly to `CA` and `CN` (removing extraneous emoji glyphs).
- **Time Presets**: Removed `2020-Now` time range button and condensed `All-Time` to `All` on mobile view.
- **Shrunk Play Bar & Restored Speed Selector**:
  - Shrunk the bottom floating playback bar horizontally to a compact, centered pill console (`width: max-content`, ~309px on 390px viewport).
  - Restored the Speed selector dropdown (`#tl-speed`: `1×` to `32×`) so playback rates are readily selectable on mobile.
  - Formatted active timeline date (`📅`) and suppressed overlapping scrubber labels for a clean, non-colliding layout.

---

## [v0.5.0+260911r] - 2026-09-11

### Added
- **Draggable Filter Bar**: Introduced tactile 6-dot drag grip handle (`#filter-bar-drag`) enabling users to position the floating filter bar anywhere in the map viewport without obscuring cartography or controls.
- **Leaflet Zoom Control Separation**: Filter bar on mobile now leaves dedicated right margin (`max-width: calc(100% - 3.8rem)`), preventing overlap with Leaflet zoom-in and zoom-out buttons.

### Changed
- **Feed Toggle Icon Restoration**: Restored the seismic feed toggle (`#sidebar-toggle`) to the classic 3-line Burger icon (`☰`).
- **Quick Actions Menu Icon**: Converted `#btn-mobile-menu` to standard 3-dot vertical kebab menu style (`⋮`), clearly distinguishing primary navigation from operational quick actions (Audio, Analytics, Table, Theme, Fullscreen).

---

## [v0.5.0+260911q] - 2026-09-11

### Changed
- **2-Letter Mobile Country Selector (CA / CN)**: Replaced full "Canada" and "China" labels with compact "CA" and "CN" (`<span class="region-label-short">`) on mobile screens (`≤768px`), preserving full labels on desktop.
- **Single-Line Mobile Filter Bar**: Enforced `flex-wrap: nowrap !important` with height `42px` and smooth horizontal swipe carousel on mobile.
- **Slim Mobile MAG Slider**: Restored and slimmed down the magnitude slider (`48px` track) into the unified single line on mobile screens instead of hiding it.

---

## [v0.5.0+260911p] - 2026-09-11

### Added
- **Mobile Action Burger Menu**: Replaced the 5 desktop action buttons on mobile screens (≤768px) with a single touch-friendly Burger menu button opening an off-canvas Quick Actions drawer (`frontend/index.html`, `frontend/css/style.css`).
- **Mobile Quick Actions Drawer**: Glassmorphic drawer containing contextual live clocks (MST/CST), Seismic Audio sonification toggle, Seismic Analytics Deck trigger, Data Table & Catalog trigger, Color Theme switch, Fullscreen mode, and link to Admin Console.
- **Dedicated Seismic Feed Icon**: Updated mobile left header button to a seismograph wave icon with badge count to clearly distinguish it from the right-hand menu.

### Changed
- **Timeline Play Bar Bottom Anchoring**: Relocated the mobile timeline player to the bottom of the map viewport (`bottom: calc(0.5rem + env(safe-area-inset-bottom))`), removing the buggy top positioning (`top: 4.4rem`) that obstructed the time filter pills.
- **Mobile Bottom Widget Hierarchy**: Docked the collapsible Layers and Magnitude legend widgets neatly above the timeline play bar (`bottom: calc(3.65rem + env(safe-area-inset-bottom))`).

---

## [v0.5.0+260911m] - 2026-09-11

### Added
- **Docker Compose Production Setup**: Containerized CEMA service on port `4071:4071` with persistent SQLite volume mounting (`./data:/app/data`) (`4fc7188`).
- **Administrative Operations Console**: Complete `/admin` portal (`backend/admin.py`, `frontend/admin.html`, `frontend/js/admin.js`, `frontend/css/admin.css`) with authenticated API routes, database status, and catalog moderation (`9901a9b`).
- **Purge Safeguards**: Added explicit permanent deletion warning modal and confirmation prompts prior to catalog purges (`ecc841c`).
- **Date/Year Range Purge Tool**: Flexible range purge with presets for historical clusters (Year 2008 Wenchuan, Years 2000–2003) (`7d8d4b7`).
- **Historical Backfill Engine**: Multi-year catalog backfill with Year 2000 presets and automated 365-day chunking to prevent API rate limits (`6872647`).
- **Magnitude-Associated Seismic Audio Sonification**: Synthesized acoustic audio chirps via Web Audio API, dynamically scaling frequency and volume with earthquake magnitude (`5100182`).
- **Sovereign & Province Geospatial Enrichment**: Automatic 2-letter postal code mapping for Canadian provinces and adjacent US border states (`29eec6e`), and sovereign polygon boundary matching (`dacf575`).
- **Dual Contextual Header Clocks**: Real-time synchronized digital clocks displaying Canada Mountain Time (MST) and China Standard Time (CST/GMT+8) (`2624345`, `92c3cc0`).
- **Data Table Scope Toggler & Exports**: "Latest 1000" vs "All Time" full-catalog view toggle, with instant GeoJSON and CSV downloads (`338c8d8`, `584e97d`).
- **A4 Landscape Analytics Deck**: Single-page 4-quadrant overview with equal-height seismic energy cards, depth distribution, and Gutenberg-Richter analysis (`82a84b0`).
- **High-Resolution PNG Bulletin Generator**: Automated instant bulletin export with aligned typography and timestamped filenames (`584e97d`).
- **Operator.Log Terminal**: Live streaming terminal for admin actions with dark and light mode syntax styling (`1bf824b`).
- **Passkey Authentication**: Client-side secure modal with backend verification against `data/cema-admin.db` (`0e54b66`).
- **Pipeline Health Telemetry**: Live status polling and error diagnostics for USGS, NRCan, and CENC ingestion adapters (`0e54b66`).

### Changed
- **Magnitude Floor Standard**: Standardized minimum magnitude floor to M 3.0 across main app UI, data tables, and historical backfill engines (`9f655f6`, `606dcc7`).
- **Deduplication Optimization**: Accelerated spatial-temporal deduplication engine with reset capability and selective backfill source toggles (`dc3df09`).
- **Admin Navigation Routing**: Replaced exit flow with direct routing to public observatory map view (`aa3e7c5`).
- **Table Pagination**: Enhanced data table with First/Last jump buttons and dark-mode purge selector styling (`c538077`).
- **OpenStreetMap Basemap Toggle**: Added native OSM tiles alongside CartoDB Dark Matter without external API key dependencies (`fb2f79d`, `f1bee59`).

### Fixed
- **Versioning Pre-commit Hook**: Corrected build tag calculation to prevent accidental double-bumping during git commits (`dd63dac`).
- **FastAPI Lifespan Management**: Migrated startup logic to modern FastAPI `lifespan` handler and eliminated duplicate app initialization.
- **SSE Stream Testing**: Fixed live SSE timeout in test suite with route-level verification.
- **Pythonpath Test Resolution**: Configured `pytest.ini` with `pythonpath = .` for seamless test execution.

---

## [v0.5.0] - 2026-09-09

### Added
- Auto-initialization and seeding of SQLite databases on startup when empty.
- Full query parameter filtering on `/api/v1/earthquakes` (`start_date`, `end_date`, `bbox`, `offset`, `limit`).
- `dedup.py` with Haversine distance (`≤25km`) and temporal window (`±60s`) deduplication.
- Production `Dockerfile` and initial `.gitignore`.
- Automated test coverage with `pytest-asyncio`.

---

## [v0.4.0] - 2026-09-09

### Added
- Single-page responsive cartographic interface with Leaflet Canvas mode.
- Desktop 3-column header: brand, telemetry HUD, and action dock.
- Mobile dual-drawer navigation: left seismic event feed and right 9-dot bento control grid.
- Floating glassmorphism controls: magnitude filter bar, layer toggles, and timeline player.

---

## [v0.3.0] - 2026-09-09

### Added
- Core FastAPI REST endpoints: `/api/v1/earthquakes`, `/api/v1/earthquakes/stats`.
- Server-Sent Events endpoint `/api/v1/live`.
- Geospatial GeoJSON boundary endpoints for tectonic faults and provincial outlines.
- Multi-region database routing between `data/eq-canada.db` and `data/eq-china.db`.

---

## [v0.2.0] - 2026-09-09

### Added
- Independent SQLite persistent catalogs with WAL mode: `data/eq-canada.db` and `data/eq-china.db`.
- Multi-agency ingestion adapters for NRCan, CENC, and USGS.
- Spatial-temporal B-Tree indexes for sub-millisecond query filtering.
- Initial historical archive seed data.

---

## [v0.1.0] - 2026-09-09

### Added
- Initial CEMA project specification: PRD, AGENTS collaboration protocol, and README.
- Architecture milestone schema and design advisory.
