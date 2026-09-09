# CEMA Frontend Visual + Structural Alignment Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development (recommended) or executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Port temas' design system and component structure to CEMA's frontend, adapting for Canada/China branding and CEMA's simpler feature set.

**Architecture:** Single-page HTML app with external CSS design system (ported from temas), Leaflet canvas map, sidebar seismic feed, floating filter/layer/legend/timeline bars, and modals for analytics + data table. All JS inline in index.html for simplicity. Backend serves the frontend at `/` via FastAPI `FileResponse`.

**Tech Stack:** Vanilla HTML/CSS/JS, Leaflet 1.9.4, CartoDB dark basemap, CEMA FastAPI backend (`/api/v1/earthquakes`, `/api/v1/earthquakes/stats`) — served on port **4071**

**Spec:** This plan is based on visual + structural alignment with `../temas/frontend/` — matching the 3-column header, sidebar feed, floating glassmorphism controls, draggable widgets, and responsive mobile patterns while using CEMA's Canada/China identity.

## Global Constraints

- No external JS frameworks — vanilla JS only
- No new dependencies — Leaflet CDN only (already used)
- CEMA API endpoints: `/api/v1/earthquakes`, `/api/v1/earthquakes/stats`, `/api/v1/live`
- Regions: `canada`, `china` (not turkey)
- Brand: "CEMA — Canada / China Earthquake Monitor"
- All docs/comments treat CEMA as independent brand (no temas references in code)
- Frontend served at `GET /` via `backend/main.py` FileResponse
- Keep feature set simpler than temas: no heatmap, no sonification, no 4-tab analytics, no snapshot export

## File Structure

| File | Action | Purpose |
|------|--------|---------|
| `frontend/css/style.css` | Create | Design system ported from temas, adapted for CEMA palette |
| `frontend/index.html` | Rewrite | Component structure matching temas (3-col header, sidebar, floating bars, modals) |
| `backend/main.py` | No change | Already serves frontend at `/` via FileResponse |

## Canada/China Color Palette

| Token | Hex | Usage |
|-------|-----|-------|
| `--accent` | `#DC2626` | Primary brand red (Canada/China shared) |
| `--accent-gold` | `#EAB308` | Secondary gold (China-inspired) |
| `--mag-minor` | `#10b981` | < 3.0 (keep from temas) |
| `--mag-moderate` | `#3B82F6` | 3.0–4.5 (blue, neutral) |
| `--mag-strong` | `#EAB308` | 4.5–6.0 (gold) |
| `--mag-severe` | `#DC2626` | 6.0–7.0 (red) |
| `--mag-catastrophic` | `#9333EA` | >= 7.0 (purple) |
| `--bg-dark` | `#07090e` | Same as temas |
| `--bg-surface` | `#0d121f` | Same as temas |
| `--bg-glass` | `rgba(15, 22, 36, 0.82)` | Same as temas |

---

### Task 1: Create CEMA Design System CSS

**Files:**
- Create: `frontend/css/style.css`

**Interfaces:**
- Consumes: None (standalone CSS)
- Produces: CSS custom properties and component classes used by `index.html`

- [ ] **Step 1: Create `frontend/css/` directory**

```bash
mkdir -p frontend/css
```

- [ ] **Step 2: Create `frontend/css/style.css` with CEMA design system**

Port temas' `style.css` structure with these adaptations:
- Replace `--accent` references from `#38bdf8` (sky-blue) → `#DC2626` (red)
- Replace hover/active glow colors from sky-blue → red
- Replace `--font-main` to include `'Plus Jakarta Sans'` (same as temas)
- Keep all component classes: header, sidebar, filter-bar, layer-controls, map-legend, timeline-bar, modal, event-card, mag-pill, toggle-item, pill-select, slider, search-box, etc.
- Keep dark/light theme support (`html[data-theme="light"]`)
- Keep responsive breakpoints at 1024/768/480px
- Keep draggable widget styles, mobile drawer patterns, animations
- Replace `var(--fault-line)` references to work with CEMA context
- The CSS should be ~2000-2500 lines (trimmed from temas' 4579 — remove analytics-specific styles we won't use)

Key sections to port (in order):
1. `:root` variables with CEMA palette
2. Light mode overrides
3. Reset & body
4. Header (3-column layout)
5. Brand icon (SVG seismic wave)
6. KPI capsule
7. Icon-only buttons
8. Live indicator
9. App container
10. Sidebar (feed)
11. Event cards
12. Map viewport
13. Filter bar (floating, pill selects, magnitude slider, search)
14. Layer controls (draggable toggle widget)
15. Map legend (draggable magnitude scale)
16. Leaflet popup/marker styles
17. Timeline playback bar
18. Modal (data table)
19. Analytics modal (simplified — single tab, not 4-tab)
20. Buttons, badges, utilities
21. Responsive breakpoints (1024, 768, 480)
22. Print styles (minimal)

- [ ] **Step 3: Verify CSS file is valid**

Open in browser or run a basic syntax check. Ensure no unclosed braces.

- [ ] **Step 4: Commit**

```bash
git add frontend/css/
git commit -m "feat(frontend): add CEMA design system CSS ported from temas"
```

---

### Task 2: Rewrite index.html with Temas Component Structure

**Files:**
- Rewrite: `frontend/index.html`

**Interfaces:**
- Consumes: `frontend/css/style.css` (Task 1), CEMA API endpoints
- Produces: Complete SPA with header, sidebar, map, floating controls, modals

- [ ] **Step 1: Rewrite `frontend/index.html` with temas-style component structure**

The HTML structure must match temas' `index.html` layout:

```html
<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <!-- Meta, fonts, Leaflet CSS, style.css -->
</head>
<body>
  <!-- HEADER: 3-column layout -->
  <header>
    <div class="header-left">
      <!-- Mobile nav burger + Brand (SVG seismic wave icon + text) -->
    </div>
    <div class="header-center">
      <!-- KPI capsule: live indicator, recorded count, max mag, 24h count -->
    </div>
    <div class="header-right">
      <!-- Desktop: icon action dock (sidebar toggle, audio, analytics, table, fullscreen) -->
      <!-- Mobile: tools burger + dropdown menu -->
    </div>
  </header>

  <!-- MAIN VIEWPORT -->
  <div class="app-container">
    <!-- Sidebar backdrop (mobile) -->
    <!-- Sidebar hover zone (desktop auto-hidden reveal) -->
    <!-- Left sidebar: seismic feed with event cards -->
    <aside id="sidebar" class="sidebar auto-hidden">...</aside>

    <!-- Center: map + floating controls -->
    <main class="map-viewport">
      <div id="map"></div>
      <!-- Floating filter bar (pill selects, magnitude slider, region search) -->
      <!-- Floating layer controls (draggable toggle widget) -->
      <!-- Floating timeline playback bar -->
      <!-- Floating magnitude legend -->
    </main>
  </div>

  <!-- Data Table Modal -->
  <div class="modal-backdrop" id="table-modal">...</div>

  <!-- Analytics Modal (simplified single-view) -->
  <div class="modal-backdrop" id="analytics-modal">...</div>

  <!-- Scripts: Leaflet CDN, inline JS -->
</body>
</html>
```

Key adaptations from temas:
- Brand: "CEMA" with "Canada / China Earthquake Monitor" subtitle
- SVG seismic wave icon in brand (adapt temas' SVG, keep the wave + epicenter design)
- Filter bar: Time pills (All-Time, 1Y, 30D, 7D, 24H), magnitude slider
- **Region toggle**: Prominent pill/toggle button in the header KPI capsule or filter bar — switches between "Canada" 🇨🇦, "China" 🇨🇳, and "All" 🌍. Drives the `region` query param on `/api/v1/earthquakes`. Visual state shows which region is active (filled pill for selected, outline for inactive).
- Layer controls: Tectonic Faults, Province Borders, (no heatmap — CEMA is simpler)
- Timeline bar: Play/Pause, scrubber, date display, speed select, center button
- Legend: Same 5-tier magnitude scale as temas
- Sidebar: Event cards with mag pill, region, time, depth, source
- Analytics modal: Simplified single-view (not 4 tabs) — just overview KPIs + magnitude distribution bar chart
- Data table modal: Same structure as temas (paginated table with export buttons)
- Mobile: Dual drawers (sidebar feed + tools menu), collapsible filter bar, compact floating widgets

- [ ] **Step 2: Write inline `<script>` block for basic interactivity**

The JS should handle:
- Map initialization (Leaflet, CartoDB dark basemap, light basemap toggle)
- `fetchEarthquakes()` — fetch from `/api/v1/earthquakes` and render markers + sidebar cards
- `fetchStats()` — fetch from `/api/v1/earthquakes/stats` and update KPIs
- Filter application (magnitude slider, time preset, region select)
- Sidebar toggle (desktop: auto-hidden with hover reveal, mobile: off-canvas drawer)
- Theme toggle (dark/light basemap + `data-theme` attribute)
- Modal open/close (analytics, data table)
- Mobile tools menu toggle
- Layer toggle (tectonic faults, province borders — placeholder if no GeoJSON yet)
- Timeline playback (basic — play/pause with date scrubber)
- Auto-refresh every 15 seconds
- Keyboard shortcuts (F=sidebar, A=analytics, T=table, Esc=close modal)

JS should be ~300-400 lines (inline in `<script>` tag), much simpler than temas' 2700-line `app.js`.

- [ ] **Step 3: Test the frontend loads correctly**

```bash
curl -s http://localhost:4071/ | head -c 200
```

Verify HTML is served. Open in browser to check:
- Map loads with markers
- Sidebar populates with event cards
- Filters work
- Theme toggle switches basemap
- Modals open/close
- Mobile responsive at 768px and 480px

- [ ] **Step 4: Commit**

```bash
git add frontend/index.html frontend/css/
git commit -m "feat(frontend): rewrite SPA with temas component structure and CEMA branding"
```

---

### Task 3: Verify End-to-End Functionality

**Files:**
- No new files (verification only)

**Interfaces:**
- Consumes: Tasks 1 + 2
- Produces: Passing manual verification

- [ ] **Step 1: Restart backend and verify**

```bash
kill $(lsof -ti:4071) 2>/dev/null; sleep 1
nohup .venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 4071 > /tmp/cema.log 2>&1 &
sleep 2
curl -s http://localhost:4071/ | head -c 100
```

Expected: HTML content returned (not JSON)

- [ ] **Step 2: Verify API endpoints still work**

```bash
curl -s http://localhost:4071/api/v1/earthquakes?limit=2
curl -s http://localhost:4071/api/v1/earthquakes/stats
curl -s http://localhost:4071/api/v1/info
```

Expected: JSON responses with earthquake data

- [ ] **Step 3: Verify CSS loads**

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:4071/css/style.css
```

Expected: 200

- [ ] **Step 4: Visual verification checklist**

Open `http://localhost:4071` in browser and verify:
- [ ] Header shows 3-column layout (brand | KPI capsule | icon dock)
- [ ] Brand shows "CEMA" with seismic wave SVG icon
- [ ] KPI capsule shows live indicator, recorded count, max mag
- [ ] Map loads with earthquake markers
- [ ] Sidebar is auto-hidden, reveals on hover (desktop) or burger tap (mobile)
- [ ] Filter bar floats at top-center of map
- [ ] Layer controls float at bottom-left
- [ ] Legend floats at bottom-right
- [ ] Timeline bar floats at bottom-center
- [ ] Theme toggle switches dark/light basemap
- [ ] Analytics modal opens with overview stats
- [ ] Data table modal opens with paginated earthquake list
- [ ] Mobile responsive: drawers, compact controls, touch-friendly targets

- [ ] **Step 5: Commit final state**

```bash
git add -A
git commit -m "chore(frontend): complete temas-style alignment with CEMA branding"
```
