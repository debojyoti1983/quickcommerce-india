"""Lat/lng -> pincode + city resolution (the "bootstrap" cold-start step).

No external geocoding API is called: this is a demo aggregator (see README —
all connector data is simulated), and reaching out to a third-party geocoder
would mean a new outbound dependency, a new SSRF surface, and possibly a paid
API key for a feature that only needs city-level precision. Instead we resolve
against a small allowlisted table of major Indian metro centroids and pick the
nearest by great-circle distance. Good enough to seed pincode/city for the
comparison engine; the user can always override manually.
"""

from __future__ import annotations

import math
from typing import NamedTuple

from pydantic import BaseModel

# Rough bounding box for India (mainland + islands) — used only to flag
# out-of-area detections; we still return the nearest known metro either way
# so the UI always has *something* sensible to show.
_INDIA_LAT_RANGE = (6.0, 37.5)
_INDIA_LNG_RANGE = (68.0, 97.5)

# A representative pincode per metro — not exhaustive, just enough coverage
# for a demo. lat/lng are approximate city centroids.
KNOWN_LOCATIONS: list[dict] = [
    {"city": "Bengaluru", "pincode": "560001", "lat": 12.9716, "lng": 77.5946},
    {"city": "Mumbai", "pincode": "400001", "lat": 19.0760, "lng": 72.8777},
    {"city": "Delhi", "pincode": "110001", "lat": 28.6139, "lng": 77.2090},
    {"city": "Hyderabad", "pincode": "500001", "lat": 17.3850, "lng": 78.4867},
    {"city": "Chennai", "pincode": "600001", "lat": 13.0827, "lng": 80.2707},
    {"city": "Kolkata", "pincode": "700001", "lat": 22.5726, "lng": 88.3639},
    {"city": "Pune", "pincode": "411001", "lat": 18.5204, "lng": 73.8567},
    {"city": "Ahmedabad", "pincode": "380001", "lat": 23.0225, "lng": 72.5714},
    {"city": "Jaipur", "pincode": "302001", "lat": 26.9124, "lng": 75.7873},
    {"city": "Lucknow", "pincode": "226001", "lat": 26.8467, "lng": 80.9462},
    {"city": "Chandigarh", "pincode": "160001", "lat": 30.7333, "lng": 76.7794},
    {"city": "Kochi", "pincode": "682001", "lat": 9.9312, "lng": 76.2673},
    {"city": "Indore", "pincode": "452001", "lat": 22.7196, "lng": 75.8577},
    {"city": "Nagpur", "pincode": "440001", "lat": 21.1458, "lng": 79.0882},
    {"city": "Bhopal", "pincode": "462001", "lat": 23.2599, "lng": 77.4126},
    {"city": "Surat", "pincode": "395001", "lat": 21.1702, "lng": 72.8311},
    {"city": "Patna", "pincode": "800001", "lat": 25.5941, "lng": 85.1376},
    {"city": "Guwahati", "pincode": "781001", "lat": 26.1445, "lng": 91.7362},
    {"city": "Coimbatore", "pincode": "641001", "lat": 11.0168, "lng": 76.9558},
    {"city": "Visakhapatnam", "pincode": "530001", "lat": 17.6868, "lng": 83.2185},
]

# Beyond this radius the "nearest metro" is too far away to call serviceable —
# it's a demo signal to the UI ("we don't cover this area yet"), not a hard block.
_SERVICEABLE_RADIUS_KM = 300.0
_EARTH_RADIUS_KM = 6371.0


class LocationMatch(BaseModel):
    city: str
    pincode: str
    matched_label: str
    distance_km: float
    serviceable: bool
    in_india: bool


class _Metro(NamedTuple):
    city: str
    pincode: str
    lat: float
    lng: float


_METROS = [_Metro(m["city"], m["pincode"], m["lat"], m["lng"]) for m in KNOWN_LOCATIONS]


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * _EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def resolve_from_latlng(lat: float, lng: float) -> LocationMatch:
    """Nearest known metro by great-circle distance. Never raises — worst case
    is a distant match flagged ``serviceable=False``; the caller/UI decides
    whether to fall back to manual entry."""
    nearest = min(_METROS, key=lambda m: _haversine_km(lat, lng, m.lat, m.lng))
    distance = _haversine_km(lat, lng, nearest.lat, nearest.lng)
    in_india = _INDIA_LAT_RANGE[0] <= lat <= _INDIA_LAT_RANGE[1] and _INDIA_LNG_RANGE[0] <= lng <= _INDIA_LNG_RANGE[1]
    return LocationMatch(
        city=nearest.city,
        pincode=nearest.pincode,
        matched_label=nearest.city,
        distance_km=round(distance, 1),
        serviceable=distance <= _SERVICEABLE_RADIUS_KM,
        in_india=in_india,
    )


def list_known_cities() -> list[dict]:
    """Sorted city list for the manual location picker."""
    return sorted(({"city": m.city, "pincode": m.pincode} for m in _METROS), key=lambda c: c["city"])
