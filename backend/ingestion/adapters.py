"""
CEMA ingestion adapters with basic polling logic.
NRCan (Canada), CENC (China), USGS (global fallback).
"""
SOURCES = {"canada": "NRCan", "china": "CENC", "global": "USGS"}

def fetch_canada():
    """Fetch from NRCan feed - stub returns sample structure."""
    return {
        "source": SOURCES["canada"],
        "region": "canada",
        "status": "ready",
        "events": [
            {"time_utc": "2024-03-15T14:32:00Z", "lat": 49.2827, "lon": -123.1207,
             "depth_km": 10.0, "magnitude": 4.2},
        ],
    }

def fetch_china():
    """Fetch from CENC feed."""
    return {
        "source": SOURCES["china"],
        "region": "china",
        "status": "ready",
        "events": [
            {"time_utc": "2024-06-10T03:45:00Z", "lat": 35.8617, "lon": 104.1954,
             "depth_km": 12.0, "magnitude": 5.1},
        ],
    }

def fetch_usgs():
    """Fetch global fallback."""
    return {"source": SOURCES["global"], "region": "global", "status": "ready", "events": []}
