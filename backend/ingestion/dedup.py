"""Deduplication: distance <= 25 km, time window ±60 s."""
import math

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2*R*math.asin(math.sqrt(a))

def is_duplicate(event, catalog):
    for e in catalog:
        time_diff = abs((event['time_utc'] - e['time_utc']).total_seconds())
        if time_diff > 60:
            continue
        dist = haversine(event['lat'], event['lon'], e['lat'], e['lon'])
        if dist <= 25:
            return True
    return False
