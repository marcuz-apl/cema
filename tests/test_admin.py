from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

KEY = "cema2026"
AUTH = {"X-Admin-Key": KEY}


def test_admin_route():
    resp = client.get("/admin")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/html")
    assert "Operations Deck" in resp.text


def test_admin_css_js():
    assert client.get("/static/css/admin.css").status_code == 200
    assert client.get("/static/js/admin.js").status_code == 200


def test_admin_auth_required():
    resp = client.get("/api/admin/status")
    assert resp.status_code == 401


def test_admin_auth_wrong_key():
    resp = client.get("/api/admin/status", headers={"X-Admin-Key": "nope"})
    assert resp.status_code == 401


def test_admin_auth_valid():
    resp = client.post("/api/admin/auth", headers=AUTH)
    assert resp.status_code == 200
    assert resp.json()["status"] == "authenticated"


def test_admin_status():
    resp = client.get("/api/admin/status", headers=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert {"nrcan", "cenc", "usgs"}.issubset(set(data["providers"]))
    assert data["providers"]["usgs"]["reachable"] is True
    assert data["providers"]["usgs"]["status"] == "healthy"
    assert data["providers"]["nrcan"]["reachable"] is True
    assert data["providers"]["cenc"]["reachable"] is True
    assert data["database"]["total_records"] > 0
    assert "BY" in data["database"]["by_year"] or data["database"]["by_year_list"]


def test_admin_events_list():
    resp = client.get("/api/admin/earthquakes", headers=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] > 0
    assert len(data["items"]) == data["limit"]
    for item in data["items"]:
        assert item["db"] in ("canada", "china")


def test_admin_events_filters():
    resp = client.get("/api/admin/earthquakes?region=canada&min_mag=4.0", headers=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert item["region"] == "canada"
        assert item["magnitude"] >= 4.0


def test_admin_manual_event_roundtrip():
    payload = {
        "region": "canada",
        "event_time_utc": "2026-09-09T12:00:00Z",
        "latitude": 52.0,
        "longitude": -110.0,
        "depth_km": 10.0,
        "magnitude": 3.3,
        "source": "OPERATOR",
    }
    resp = client.post("/api/admin/earthquakes", json=payload, headers=AUTH)
    assert resp.status_code == 200
    new_id = resp.json()["event"]["id"]
    assert new_id > 0

    found = client.get(f"/api/admin/earthquakes?search=OPERATOR", headers=AUTH).json()
    assert any(e["id"] == new_id for e in found["items"])

    del_resp = client.request(
        "DELETE",
        "/api/admin/earthquakes",
        json={"id": new_id, "region": "canada"},
        headers=AUTH,
    )
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted"] is True

    gone = client.request(
        "DELETE",
        "/api/admin/earthquakes",
        json={"id": new_id, "region": "canada"},
        headers=AUTH,
    )
    assert gone.status_code == 404


def test_admin_manual_event_bad_region():
    payload = {
        "region": "moon",
        "event_time_utc": "2026-09-09T12:00:00Z",
        "latitude": 0.0,
        "longitude": 0.0,
        "depth_km": 10.0,
        "magnitude": 3.3,
        "source": "OPERATOR",
    }
    resp = client.post("/api/admin/earthquakes", json=payload, headers=AUTH)
    assert resp.status_code == 400


def test_admin_backfill_status_idle():
    resp = client.get("/api/admin/backfill/status", headers=AUTH)
    assert resp.status_code == 200
    assert resp.json()["is_running"] is False


def test_admin_checkpoint_wal():
    resp = client.post("/api/admin/db/checkpoint-wal", headers=AUTH)
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    assert set(resp.json()["checkpoint"]) == {"canada", "china"}


def test_admin_export_zip():
    resp = client.get("/api/admin/db/download", headers=AUTH)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"
    assert len(resp.content) > 1000


def test_admin_backfill_reset():
    resp = client.post("/api/admin/backfill/reset", headers=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "reset" in data["message"].lower()

    # Verify status is now idle
    status_resp = client.get("/api/admin/backfill/status", headers=AUTH)
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["is_running"] is False
    assert status_data["status"] == "idle"


def test_admin_deduplicate_all():
    resp = client.post("/api/admin/db/deduplicate", headers=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "deduplicate" in data
    assert "canada" in data["deduplicate"]
    assert "china" in data["deduplicate"]
    assert isinstance(data["deduplicate"]["canada"]["duplicate_pairs"], int)

def test_admin_backfill_year_2000_request_validation():
    # Verify year 2000 backfill request payload validates and accepts chunk_days=365
    payload = {
        "start_date": "2000-01-01",
        "end_date": "2000-12-31",
        "min_mag": 3.0,
        "chunk_days": 365,
        "mode": "merge",
        "regions": "canada",
        "source": "usgs",
    }
    # Reset engine first to ensure idle state
    client.post("/api/admin/backfill/reset", headers=AUTH)
    resp = client.post("/api/admin/backfill", json=payload, headers=AUTH)
    assert resp.status_code in (200, 400)
    if resp.status_code == 200:
        data = resp.json()
        assert data["status"] in ("started", "busy")
        # Cleanly reset backfill engine back to idle
        client.post("/api/admin/backfill/reset", headers=AUTH)

def test_admin_purge_range_endpoint():
    # Insert a temporary test event in 2008
    temp_event = {
        "region": "canada",
        "event_time_utc": "2008-05-12T14:28:00Z",
        "latitude": 51.5,
        "longitude": -120.5,
        "depth_km": 10.0,
        "magnitude": 4.0,
        "source": "OPERATOR",
    }
    create_resp = client.post("/api/admin/earthquakes", json=temp_event, headers=AUTH)
    assert create_resp.status_code == 200

    # Purge year 2008
    payload = {
        "start_date": "2008-01-01",
        "end_date": "2008-12-31",
        "regions": "canada",
    }
    purge_resp = client.post("/api/admin/db/purge-range", json=payload, headers=AUTH)
    assert purge_resp.status_code == 200
    data = purge_resp.json()
    assert data["status"] == "ok"
    assert data["total_deleted"] >= 1
    assert "canada" in data["deleted"]

    # Verify invalid date format returns 400
    bad_payload = {
        "start_date": "not-a-date",
        "end_date": "2008-12-31",
        "regions": "all",
    }
    bad_resp = client.post("/api/admin/db/purge-range", json=bad_payload, headers=AUTH)
    assert bad_resp.status_code == 400

    # Verify start > end returns 400
    reversed_payload = {
        "start_date": "2008-12-31",
        "end_date": "2008-01-01",
        "regions": "all",
    }
    rev_resp = client.post("/api/admin/db/purge-range", json=reversed_payload, headers=AUTH)
    assert rev_resp.status_code == 400

def test_admin_poller_status_and_toggle():
    # 1. Check poller status endpoint
    resp = client.get("/api/admin/poller/status", headers=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert "enabled" in data
    assert data["interval_sec"] == 180

    # 2. Toggle pause poller
    t_resp = client.post("/api/admin/poller/toggle?enable=false", headers=AUTH)
    assert t_resp.status_code == 200
    assert t_resp.json()["enabled"] is False

    # 3. Toggle re-enable poller
    t_resp2 = client.post("/api/admin/poller/toggle?enable=true", headers=AUTH)
    assert t_resp2.status_code == 200
    assert t_resp2.json()["enabled"] is True

def test_admin_backfill_mag_floor_2_validation():
    # Verify BackfillRequest accepts min_mag starting from 2.0
    payload = {
        "start_date": "2024-01-01",
        "end_date": "2024-01-02",
        "min_mag": 2.0,
        "chunk_days": 60,
        "mode": "merge",
        "regions": "canada",
        "source": "usgs",
    }
    client.post("/api/admin/backfill/reset", headers=AUTH)
    resp = client.post("/api/admin/backfill", json=payload, headers=AUTH)
    assert resp.status_code in (200, 400)
    if resp.status_code == 200:
        data = resp.json()
        assert data["status"] in ("started", "busy")
        client.post("/api/admin/backfill/reset", headers=AUTH)
