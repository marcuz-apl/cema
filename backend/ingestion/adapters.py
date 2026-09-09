"""CEMA ingestion adapters — NRCan (Canada), CENC (China), USGS (global fallback)."""

SOURCES = {
    "canada": "NRCan",
    "china": "CENC",
    "global": "USGS",
}

def fetch_canada():
    return {"source": SOURCES["canada"], "region": "canada", "status": "stub"}

def fetch_china():
    return {"source": SOURCES["china"], "region": "china", "status": "stub"}

def fetch_usgs():
    return {"source": SOURCES["global"], "region": "global", "status": "stub"}
