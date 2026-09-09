# CEMA Design Advisory — Canada / China Focus

## Data Source Recommendations

### Canada
- **Primary**: Natural Resources Canada (NRCan) seismic bulletins and live feeds.
- **Secondary**: USGS global feeds filtered to Canada bounding box (~42°N–83°N, 168°W–52°W).
- **Boundary Data**: Canada provincial / territorial boundaries (GeoJSON); North American plate boundary segments.

### China
- **Primary**: China Earthquake Networks Center (CENC) real-time and catalog feeds.
- **Secondary**: USGS global feeds filtered to China bounding box (~18°N–54°N, 73°E–135°E).
- **Boundary Data**: China provincial / autonomous region boundaries (GeoJSON); Eurasian / Indo-Australian plate boundary segments.

## Database Design — 2 Independent Files

As instructed in Initiative_cema.md:

- `data/eq-canada.db` — Canada-only events, schema identical to `eq-china.db` for portability.
- `data/eq-china.db` — China-only events.

Both use:
- SQLite3 with Write-Ahead Logging (WAL) mode.
- B-Tree indexes on `origintimeutc`, `magnitude`, `latitude`, `longitude`.
- Deduplication: geospatial distance ≤ 25 km, time window ± 60 s.

This split keeps regional queries fast, supports independent updates, and avoids monolithic DB contention.

## UI Design Recommendations

- Keep the 3-column desktop header identical in layout: brand left, telemetry HUD center, action dock right.
- Do not use iframe nesting; build a unified SPA with reactive state.
- Mobile: adaptive dual-drawers (left seismic feed, right 9-dot bento tools grid) rather than a single hamburger menu, preserving quick access to layers and analytics.
- Player bar supports chronological replay across any selected temporal window with magnitude-scaled audio chirps.

## Skill Bundle Status

`alfazen-coding` skills are installed at `~/.claude/skills/alfazen-coding/` and include:
- `changelog-curator`, `versioning-alfazen`, `ponytail` (anti-bloat), `writing-plans`, `verification-before-completion`, `subagent-driven-development`, `test-driven-development`.
