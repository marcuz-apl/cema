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
