from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI(title="CEMA API", version="v0.0.1+2609094")

class Earthquake(BaseModel):
    id: int
    region: str
    event_time_utc: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    depth_km: Optional[float]
    magnitude: Optional[float]
    source: Optional[str]

@app.get("/")
async def root():
    return {"service": "CEMA", "version": "v0.0.1", "regions": ["canada", "china"]}

@app.get("/api/v1/earthquakes")
async def list_earthquakes(region: Optional[str] = None, limit: int = 50):
    return {"region": region or "both", "limit": limit, "items": []}

@app.get("/api/v1/earthquakes/stats")
async def stats():
    return {"total": 0, "regions": ["canada", "china"]}
