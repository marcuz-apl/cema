from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_root():
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/html")
    assert "CEMA" in resp.text

def test_root_css():
    resp = client.get("/css/style.css")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/css")

def test_analytics_deck_markup():
    """The analytics deck ships its tab rail, panes and export hooks."""
    resp = client.get("/")
    html = resp.text
    for token in (
        "analytics-tabs-nav",
        'data-tab="overview"', 'data-tab="time"', 'data-tab="energy"', 'data-tab="regions"',
        "analytics-scope-toggle",
        "tab-analytics-overview", "tab-analytics-time", "tab-analytics-energy", "tab-analytics-regions",
        "btn-export-analytics-pdf", "btn-export-analytics-png",
        "html2canvas",
    ):
        assert token in html, f"missing in served HTML: {token}"
    # legacy single-view ids must be gone
    for stale in ('id="mag-bars"', 'id="analytics-total"', 'id="analytics-canada-bar"'):
        assert stale not in html, f"stale analytics id present: {stale}"

def test_analytics_deck_css_hooks():
    css = client.get("/css/style.css").text
    for token in (".analytics-tab-pane", ".kpi-chip", ".chart-diurnal-bars",
                  ".matrix-table", ".export-a4-snapshot", ".bulletin-footer", "@media print"):
        assert token in css, f"missing rule: {token}"

def test_info():
    resp = client.get("/api/v1/info")
    assert resp.status_code == 200
    data = resp.json()
    assert data["service"] == "CEMA"
    assert "canada" in data["regions"]
    assert "china" in data["regions"]

def test_list_earthquakes():
    resp = client.get("/api/v1/earthquakes")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "count" in data
    assert data["count"] > 0

def test_list_earthquakes_by_region():
    resp = client.get("/api/v1/earthquakes?region=canada")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    for item in data["items"]:
        assert item["region"] == "canada"

def test_list_earthquakes_min_mag():
    resp = client.get("/api/v1/earthquakes?min_mag=4.0")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    for item in data["items"]:
        assert item["magnitude"] >= 4.0

def test_stats():
    resp = client.get("/api/v1/earthquakes/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert data["total"] > 0

def test_live_sse():
    routes = [r for r in app.routes if hasattr(r, 'path') and r.path == '/api/v1/live']
    assert len(routes) == 1
    assert routes[0].methods == {'GET'}
    from backend.main import live as live_handler
    assert callable(live_handler)

def test_tectonic_boundaries():
    resp = client.get("/api/v1/boundaries/tectonic")
    assert resp.status_code == 200
    assert resp.json()["type"] == "FeatureCollection"

def test_provinces_boundaries():
    resp = client.get("/api/v1/boundaries/provinces")
    assert resp.status_code == 200
    assert resp.json()["type"] == "FeatureCollection"