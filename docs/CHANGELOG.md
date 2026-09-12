# CHANGELOG — CEMA

All notable changes to the CEMA (Canada / China Earthquake Monitoring & Alert system) project are documented in this file.
Version format adheres to `versioning-alfazen`: `v<m.n.p>+<yymmddc>`.

---

## [v0.9.0+260912d] - 2026-09-12

### Added
- **Admin Panel Dedicated Seismology & Operations Documentation Page (`/admin/docs`)**:
  - Built a comprehensive, high-density Knowledge Base page (`frontend/admin-docs.html`) within the CEMA Operations Deck suite.
  - **Theoretical Seismology & Earthquake Mechanics**: Covers plate boundary kinematics, Reid's Elastic Rebound Theory (1906), rate-and-state stick-slip friction (τ_s), 3D hypocenter vs. 2D epicenter geometry, structural fault classifications (normal, thrust/megathrust, strike-slip), wave propagation physics (P, S, Rayleigh, Love), Moment magnitude scale (Mw = ⅔ log₁₀ M₀ - 6.07), Gutenberg-Richter energy formula (log₁₀ E = 4.8 + 1.5M), frequency-magnitude recurrence (log₁₀ N = a - bM) with b-value stress indicators, and focal depth attenuation.
  - **Regional Earthquake Profiles (Canada & China)**: Detailed comparative seismotectonics, active seismic belts (Cascadia megathrust, Queen Charlotte Fault, St. Lawrence intraplate, Longmenshan thrust belt, Tibetan escape faults, North China grabens), benchmark historical events (1700 Cascadia, 1929 Grand Banks, 1949 Haida Gwaii, 1556 Shaanxi, 1920 Haiyuan, 1976 Tangshan, 2008 Wenchuan), and national monitoring authorities (NRCan / CNSN vs. CENC / CEA).
  - **CEMA Monitoring & Alert Engine Architecture**: Multi-agency ingestion pipelines (NRCan, CENC, USGS) with 3-minute background sync cron, spatial-temporal deduplication algorithm (≤ 25 km, ± 60 s, M ≥ 3.0), dual isolated regional catalogs (`data/eq-canada.db`, `data/eq-china.db`) in SQLite WAL mode, ray-casting sovereign boundary classification, real-time Server-Sent Events (`/api/v1/live`), Web Audio API acoustic sonification, and administrative deletion safeguards.
  - **Navigation & Ergonomics**: Integrated direct header link (`Docs`) with inline SVG icons, scroll-spy table of contents with in-page search, print/PDF export styling (`window.print()`), dark/light theme toggle parity, and mobile-first collapsible navigation summary.
  - **Automated Test Coverage**: Added `test_admin_docs_page` in `tests/test_admin.py` bringing test suite to 52 passing tests.

---

## [v0.9.0+260912c] - 2026-09-12

### Changed
- **Milestone Semantic Versioning Alignment (Phases 6–9)**:
  - Synchronized project versioning with the 9 milestone phases defined in `PRD.md` and `docs/MILESTONES.md`:
    - **Phase 6** (Audio Sonification & Boundaries) aligned to **`v0.6.0`** (starting from build `+2609101`).
    - **Phase 7** (Analytics Deck & Export Studio) aligned to **`v0.7.0`** (starting from build `+2609106`).
    - **Phase 8** (Operations & Admin Console) aligned to **`v0.8.0`** (starting from build `+2609116`).
    - **Phase 9** (Hardening, Containerization & Production Readiness) aligned to **`v0.9.0`** (starting from build `+260911m`).
  - Set active project version to **`v0.9.0+260912c`** across `VERSION`, `PRD.md`, `MILESTONES.md`, FastAPI OpenAPI schema, `/api/v1/info`, Admin console telemetry chips, and asset cache busters.

---

## [v0.9.0+260912b] - 2026-09-12

### Fixed
- **Mobile Table Modal Header Responsiveness (Full <= 768px Range)**:
  - Relocated `#table-modal .modal-header` responsive styling from `@media (max-width: 480px)` to `@media (max-width: 768px)` so intermediate mobile/tablet viewports (481px–768px) no longer fall back to the unconstrained desktop single-row header.
  - Promoted `#table-modal-close` to be a direct child of `.modal-header` with flex ordering (`order: 2`), ensuring the close button `✕` is always anchored on Row 1 alongside the title on all mobile viewports.
  - Added responsive `.word-export` toggling under `<= 480px` to streamline buttons to `⬇ CSV` and `🌐 GeoJSON`, guaranteeing both buttons fit side-by-side on Row 2 with zero overflow across any phone screen down to 320px.
  - Verified across 12 distinct viewport widths (320px to 1440px) with 100% containment inside the modal card.

---

## [v0.9.0+260912a] - 2026-09-12

### Changed
- **Asset Cache-Busting & No-Cache Headers**:
  - Appended version query string `?v=v0.5.0+260912a` to `/css/style.css` in `frontend/index.html` and admin assets in `frontend/admin.html` to prevent mobile Safari/Chrome aggressive disk-cache lock-in.
  - Added explicit HTTP headers `Cache-Control: no-cache, no-store, must-revalidate`, `Pragma: no-cache`, and `Expires: 0` to FastAPI root `/` and `/admin` `FileResponse` handlers in `backend/main.py`.
- **Application Server Restart**: Cleanly recycled the Uvicorn ASGI daemon on port 4071 to ensure all latest backend and static routes are actively served.

---

## [v0.9.0+260911x] - 2026-09-11

### Fixed
- **Mobile Table Modal Export GeoJSON Button Overflow**: Resolved an issue where the Earthquake Data Table card on mobile devices (`<= 768px`) could not hold the "Export GeoJSON" button due to non-wrapping flex containers pushing export buttons off the right edge.
  - Grouped `#btn-export-csv` and `#btn-export-geojson` into a dedicated `.table-export-actions` container, keeping the export buttons paired side-by-side.
  - Restructured `#table-modal .modal-header` on mobile to stack gracefully:
    - Row 1: `Earthquake Data Table` title with calendar icon, and `✕` close button pinned top-right (`position: absolute; right: 0.65rem; top: 0.6rem;`).
    - Row 2: Catalog scope toggler (`Latest 1000` / `All Time`).
    - Row 3: Paired export buttons (`Export CSV` and `Export GeoJSON`), fully visible and bounded inside the card with ample breathing room.
  - Preserved desktop header alignment where scope toggle, export actions, and close button sit inline on the right.

---

## [v0.9.0+260911w] - 2026-09-11

### Changed
- **Mobile Analytics Deck Scrollable Cards**: Enabled vertical scrolling for cards across all 4 Analytics Deck tabs (`Overview`, `Time`, `Energy`, `Regions`) in mobile view (`max-width: 768px`).
  - Configured `.modal.modal-analytics` with `height: 94vh; max-height: 94vh; display: flex; flex-direction: column; overflow: hidden;`.
  - Configured `.analytics-modal-body` with `flex: 1 1 auto; overflow-y: auto !important; -webkit-overflow-scrolling: touch; min-height: 0; padding: 0.6rem 0.75rem 2.2rem;` ensuring comfortable touch scrolling.
  - Set `.analytics-tab-pane.active` and grid containers (`.analytics-grid-*`) to `height: auto !important; min-height: min-content; display: flex; flex-direction: column; flex: none; gap: 0.85rem;`.
  - Set individual `.analytics-card` elements to natural height (`height: auto; min-height: auto; flex: none;`), enabling cards to stack and scroll smoothly without content truncation.
  - Strictly preserved desktop A4 single-page view (`overflow: hidden; height: 820px;`) for landscape bulletin presentation and export.

---

## [v0.9.0+260911v] - 2026-09-11

### Changed
- **Default Collapsed State for LAYERS and MAG**: Both `LAYERS` controls and `MAG` legend widgets are now collapsed by default on initial page load (`collapsed` class and `aria-expanded="false"`), keeping the bottom HUD clean and providing an unobstructed view of the cartography. Tapping either pill instantly expands the respective control panel.
- **Mobile-Aware Corner Snapping**: Updated `snapWidgetToCorner` to clear inline overrides on mobile (`<= 768px`) ensuring CSS mobile responsive positioning rules remain strictly enforced.

---

## [v0.9.0+260911u] - 2026-09-11

### Changed
- **Mobile Filter Bar Order & Search Expansion**:
  - Reordered mobile filter bar items to `Grip -> Country (CA/CN) -> Time Presets -> MAG Slider -> Search`.
  - Configured `All` on mobile view and `All-Time` on desktop view via `.pill-mobile` / `.pill-desktop`, freeing up horizontal space for the region search bar.
  - Expanded search bar input width on mobile to 85px (expands to 115px on focus).
- **Bottom HUD Row Layout & Smaller Typography**:
  - Landed `LAYERS` (bottom-left), `Play bar` (bottom-center), and `MAG` (bottom-right) all on the very bottom row (`bottom: 0.5rem`).
  - Reduced font sizes for `LAYERS` and `MAG` bars to compact micro-typography (~9px / 0.55rem) with slim toggles and color swatches.
  - Compacted the Play bar (~181px) to guarantee zero overlap across all mobile viewports while preserving step controls, play/pause, scrubber, playback date, and Speed selector (`1×`–`32×`).

---

## [v0.9.0+260911t] - 2026-09-11

### Fixed
- **Normal View 'All-Time' Text**: Fixed duplicate text display glitch where 'All-Time' rendered as 'All-TimeAll' by removing the redundant span and restoring standard text button rendering.

### Changed
- **Mobile Menu 9-Dot Bento Icon**: Updated top-right mobile action menu button (`#btn-mobile-menu`) to a 9-dot Bento Grid icon (`⠿` in 3x3 layout), providing clear visual distinction from the 6-dot drag handle grip (`⠿` in 2x3 layout) and aligning with the project's mobile bento specification.

---

## [v0.9.0+260911s] - 2026-09-11

### Changed
- **MAG Filter Visibility on Mobile**: Reordered mobile filter bar layout (`Country -> MAG Filter -> Time Presets`) ensuring the MAG slider (`min=3.0`) is 100% visible on screen without requiring horizontal scrolling.
- **Compact Country Selector**: Streamlined mobile region buttons strictly to `CA` and `CN` (removing extraneous emoji glyphs).
- **Time Presets**: Removed `2020-Now` time range button and condensed `All-Time` to `All` on mobile view.
- **Shrunk Play Bar & Restored Speed Selector**:
  - Shrunk the bottom floating playback bar horizontally to a compact, centered pill console (`width: max-content`, ~309px on 390px viewport).
  - Restored the Speed selector dropdown (`#tl-speed`: `1×` to `32×`) so playback rates are readily selectable on mobile.
  - Formatted active timeline date (`📅`) and suppressed overlapping scrubber labels for a clean, non-colliding layout.

---

## [v0.9.0+260911r] - 2026-09-11

### Added
- **Draggable Filter Bar**: Introduced tactile 6-dot drag grip handle (`#filter-bar-drag`) enabling users to position the floating filter bar anywhere in the map viewport without obscuring cartography or controls.
- **Leaflet Zoom Control Separation**: Filter bar on mobile now leaves dedicated right margin (`max-width: calc(100% - 3.8rem)`), preventing overlap with Leaflet zoom-in and zoom-out buttons.

### Changed
- **Feed Toggle Icon Restoration**: Restored the seismic feed toggle (`#sidebar-toggle`) to the classic 3-line Burger icon (`☰`).
- **Quick Actions Menu Icon**: Converted `#btn-mobile-menu` to standard 3-dot vertical kebab menu style (`⋮`), clearly distinguishing primary navigation from operational quick actions (Audio, Analytics, Table, Theme, Fullscreen).

---

## [v0.9.0+260911q] - 2026-09-11

### Changed
- **2-Letter Mobile Country Selector (CA / CN)**: Replaced full "Canada" and "China" labels with compact "CA" and "CN" (`<span class="region-label-short">`) on mobile screens (`≤768px`), preserving full labels on desktop.
- **Single-Line Mobile Filter Bar**: Enforced `flex-wrap: nowrap !important` with height `42px` and smooth horizontal swipe carousel on mobile.
- **Slim Mobile MAG Slider**: Restored and slimmed down the magnitude slider (`48px` track) into the unified single line on mobile screens instead of hiding it.

---

## [v0.9.0+260911p] - 2026-09-11

### Added
- **Mobile Action Burger Menu**: Replaced the 5 desktop action buttons on mobile screens (≤768px) with a single touch-friendly Burger menu button opening an off-canvas Quick Actions drawer (`frontend/index.html`, `frontend/css/style.css`).
- **Mobile Quick Actions Drawer**: Glassmorphic drawer containing contextual live clocks (MST/CST), Seismic Audio sonification toggle, Seismic Analytics Deck trigger, Data Table & Catalog trigger, Color Theme switch, Fullscreen mode, and link to Admin Console.
- **Dedicated Seismic Feed Icon**: Updated mobile left header button to a seismograph wave icon with badge count to clearly distinguish it from the right-hand menu.

### Changed
- **Timeline Play Bar Bottom Anchoring**: Relocated the mobile timeline player to the bottom of the map viewport (`bottom: calc(0.5rem + env(safe-area-inset-bottom))`), removing the buggy top positioning (`top: 4.4rem`) that obstructed the time filter pills.
- **Mobile Bottom Widget Hierarchy**: Docked the collapsible Layers and Magnitude legend widgets neatly above the timeline play bar (`bottom: calc(3.65rem + env(safe-area-inset-bottom))`).

---

## [v0.9.0+260911m] - 2026-09-11

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
