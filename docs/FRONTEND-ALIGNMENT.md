# CEMA Frontend Visual & Structural Architecture

This document defines CEMA's frontend design system, component hierarchy, cartographic rendering, and interaction specifications.

**Architecture:** Unified Single-Page Application (SPA) with an external CSS design system (`frontend/css/style.css`), Leaflet canvas-accelerated map, sidebar seismic activity feed, floating glassmorphism control modules (filter, layer, magnitude legend, timeline player), and high-density modals (Analytics Deck, Data Table). Served at `/` by FastAPI `backend/main.py`.

**Tech Stack:** Vanilla HTML5, Modern CSS (Glassmorphism + CSS Custom Properties), Vanilla ESM JavaScript, Leaflet 1.9.4 (Canvas mode), CartoDB Dark Matter & OpenStreetMap tile layers — running on port **4071**.

## Core Constraints & Principles

- **No external JS frameworks**: Lightweight, high-performance vanilla JavaScript.
- **Zero unnecessary dependencies**: Leaflet CDN only for map rendering.
- **CEMA API Endpoints**:
  - `GET /api/v1/earthquakes`: Main catalog with spatial, magnitude, and date range filters.
  - `GET /api/v1/earthquakes/stats`: Aggregated metrics across regions.
  - `GET /api/v1/live`: Server-Sent Events (SSE) stream for real-time seismic alerts.
  - `GET /api/v1/boundaries/tectonic`: GeoJSON tectonic plate boundary and fault line overlays.
  - `GET /api/v1/boundaries/provinces`: GeoJSON provincial and territorial borders for Canada and China.
- **Regions**: Primary focus on `canada` and `china` sovereign territories and contiguous zones.
- **Independent Identity**: CEMA (Canada / China Earthquake Monitoring & Alert system) operates as a standalone seismic observatory.

---

## File Structure

| File | Purpose |
|---|---|
| `frontend/index.html` | Public Observatory SPA (3-column header, map viewport, floating HUDs, analytics modal, data table) |
| `frontend/css/style.css` | Complete glassmorphism design system, responsive breakpoints, and micro-animations |
| `frontend/admin.html` | Operations & Admin Control Center (passkey auth, pipeline telemetry, backfill, purge, deduplication) |
| `frontend/css/admin.css` | High-density dark/light theme dashboard styling for administrative operations |
| `frontend/js/admin.js` | Operator console logic, passkey authentication, live terminal log streaming |
| `frontend/data/` | Static GeoJSON files for Canada/China AOIs, faults, and provincial boundaries |

---

## Color Palette & Design Tokens

CEMA uses a curated palette reflecting emergency seismic telemetry with Canada and China sovereign identities:

| Token | Value | Semantic Usage |
|---|---|---|
| `--accent` | `#DC2626` | Primary seismic red (shared national identity) |
| `--accent-gold` | `#EAB308` | Secondary seismic alert gold |
| `--bg-dark` | `#07090e` | Deep obsidian base background |
| `--bg-surface` | `#0d121f` | Elevated card and container background |
| `--bg-glass` | `rgba(15, 22, 36, 0.82)` | Frosted glassmorphism panels with 12px backdrop blur |
| `--border-glass` | `rgba(255, 255, 255, 0.08)` | Subtle translucent structural borders |
| `--text-primary` | `#F1F5F9` | Primary readable content |
| `--text-muted` | `#64748B` | Secondary telemetry labels and metadata |

### Magnitude Classification Scale

| Magnitude | Token | Color | Classification |
|---|---|---|---|
| M 3.0 – 4.5 | `--mag-minor` | `#10B981` | Minor / Light |
| M 4.5 – 5.5 | `--mag-moderate` | `#3B82F6` | Moderate |
| M 5.5 – 6.5 | `--mag-strong` | `#EAB308` | Strong |
| M 6.5 – 7.5 | `--mag-major` | `#F97316` | Major |
| M ≥ 7.5 | `--mag-catastrophic` | `#EF4444` | Catastrophic |

---

## Component Layout & User Flow

### 1. Desktop 3-Column Header
- **Left**: CEMA seismic wave emblem, brand title, and regional active badge.
- **Center**: Real-time Telemetry Capsule (Live connection pulse, 24h count, max magnitude recorded, dual Canada MST / China CST live clocks).
- **Right**: Action dock with tool toggles:
  - Audio Sonification Toggle (synthesizes acoustic chirps proportional to quake magnitude)
  - Analytics Deck Modal
  - Data Table Modal
  - Fullscreen Toggle
  - Quick Snapshot / PNG Bulletin Generator

### 2. Map Canvas & Overlays
- Canvas-accelerated Leaflet layer handling thousands of historical events smoothly at 60 fps.
- Dynamic magnitude-scaled circle markers with depth-coded opacity.
- Tectonic fault line overlays and provincial boundary borders.
- Floating controls:
  - **Filter Bar** (top): Temporal window (24h, 7d, 30d, 1y, all), magnitude slider, region selector.
  - **Layers Bar** (bottom-left): Fault lines, provincial boundaries, epicenters, heat intensity toggle.
  - **Timeline Player Bar** (bottom-center): Chronological scrub and replay with audio sonification.
  - **Magnitude Legend** (bottom-right): Interactive magnitude filter chips.

### 3. Mobile Dual-Drawer Architecture
- On viewports < 768px, desktop floating modules adapt to gesture-friendly slide-over drawers:
  - **Left Drawer**: Live chronological seismic feed with instant epicenter zoom.
  - **Right Drawer**: 9-dot bento control grid for layers, filters, basemap toggle, and analytics.
- 48px minimum touch targets for all interactive actions.
