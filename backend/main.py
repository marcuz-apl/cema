from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="CEMA API", version="v0.1.0+2609091")

class Earthquake(BaseModel):
    id: int
    region: str
    event_time_utc: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    depth_km: Optional[float] = None
    magnitude: Optional[float] = None
    source: Optional[str] = None

@app.get("/")
async def root():
    return {"service":"CEMA","version":"v0.2.0","regions":["canada","china"]}

@app.get("/api/v1/earthquakes")
async def list_earthquakes(region: Optional[str]=None, limit: int=50):
    return {"region":region or "both","limit":limit,"items":[]}

@app.get("/api/v1/earthquakes/stats")
async def stats():
    return {"total":0,"regions":["canada","china"]}
